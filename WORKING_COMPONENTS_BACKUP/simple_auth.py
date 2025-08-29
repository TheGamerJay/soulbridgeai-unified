# Simple, Clean Authentication System
import bcrypt
import secrets
from datetime import datetime, timedelta
from functools import wraps
from flask import session, request, jsonify, redirect
import logging

logger = logging.getLogger(__name__)

class SimpleAuth:
    def __init__(self, db):
        self.db = db
    
    def create_user(self, email, password, display_name):
        """Create a new user account"""
        try:
            # Check if user already exists
            if self.user_exists(email):
                return {"success": False, "error": "User already exists"}
            
            # Hash password
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(rounds=12)).decode('utf-8')
            
            # Insert into database
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            placeholder = "%s" if hasattr(self.db, 'postgres_url') and self.db.postgres_url else "?"
            
            cursor.execute(f"""
                INSERT INTO users (email, password_hash, display_name, email_verified, created_at)
                VALUES ({placeholder}, {placeholder}, {placeholder}, 1, CURRENT_TIMESTAMP)
            """, (email.lower().strip(), password_hash, display_name))
            
            conn.commit()
            user_id = cursor.lastrowid
            conn.close()
            
            logger.info(f"User created successfully: {email}")
            return {"success": True, "user_id": user_id}
            
        except Exception as e:
            logger.error(f"Create user error: {e}")
            return {"success": False, "error": str(e)}
    
    def authenticate(self, email, password):
        """Authenticate user credentials"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            placeholder = "%s" if hasattr(self.db, 'postgres_url') and self.db.postgres_url else "?"
            
            # Try to fetch with plan_type first, fallback if column doesn't exist
            try:
                cursor.execute(f"""
                    SELECT id, email, password_hash, display_name, plan_type
                    FROM users WHERE email = {placeholder}
                """, (email.lower().strip(),))
                user_data = cursor.fetchone()
                has_plan_type = True
            except Exception as col_error:
                # plan_type column might not exist, try without it
                logger.warning(f"plan_type column not found, falling back: {col_error}")
                
                # IMPORTANT: In PostgreSQL, we need to rollback the transaction after an error
                try:
                    conn.rollback()
                except:
                    pass  # Some database types don't support rollback
                
                # Create new cursor after rollback
                cursor = conn.cursor()
                cursor.execute(f"""
                    SELECT id, email, password_hash, display_name
                    FROM users WHERE email = {placeholder}
                """, (email.lower().strip(),))
                user_data = cursor.fetchone()
                has_plan_type = False
            
            conn.close()
            
            if user_data:
                if bcrypt.checkpw(password.encode('utf-8'), user_data[2].encode('utf-8')):
                    logger.info(f"Authentication successful: {email}")
                    
                    # Handle plan_type based on whether column exists
                    if has_plan_type and len(user_data) > 4 and user_data[4]:
                        plan_type = user_data[4]
                    else:
                        plan_type = 'foundation'  # Default to foundation
                    
                    return {
                        "success": True,
                        "user_id": user_data[0],
                        "email": user_data[1],
                        "display_name": user_data[3],
                        "plan_type": plan_type
                    }
                else:
                    logger.warning(f"Authentication failed: {email}")
                    return {"success": False, "error": "Invalid email or password"}
            else:
                logger.warning(f"Authentication failed - user not found: {email}")
                return {"success": False, "error": "Invalid email or password"}
                
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return {"success": False, "error": "Authentication failed"}
    
    def user_exists(self, email):
        """Check if user exists"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            placeholder = "%s" if hasattr(self.db, 'postgres_url') and self.db.postgres_url else "?"
            
            cursor.execute(f"SELECT id FROM users WHERE email = {placeholder}", (email.lower().strip(),))
            result = cursor.fetchone()
            conn.close()
            
            return result is not None
            
        except Exception as e:
            logger.error(f"User exists check error: {e}")
            return False
    
    def create_session(self, user_data):
        """Create secure user session"""
        session.permanent = False  # Session ends when browser closes
        session['user_authenticated'] = True
        session['user_id'] = user_data['user_id']
        session['user_email'] = user_data['email']
        session['display_name'] = user_data['display_name']
        session['last_activity'] = datetime.now().isoformat()
        session['session_version'] = "2025-07-28-banking-security"  # BANKING SECURITY: Force version check
        # Load user's actual plan from database instead of defaulting to foundation
        user_plan = user_data.get('plan_type', 'foundation')  # Get plan from user data
        session['user_plan'] = user_plan
        print(f"🔧 LOGIN: Set user_plan = {user_plan} for {user_data['email']}")
        
        # Try to fetch and store account creation date and profile image
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            placeholder = "%s" if hasattr(self.db, 'postgres_url') and self.db.postgres_url else "?"
            
            # First try to get creation date and profile image (check both column names)
            try:
                # Ensure profile_image columns exist (migration for PostgreSQL)
                try:
                    if hasattr(self.db, 'postgres_url') and self.db.postgres_url:
                        # PostgreSQL
                        cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS profile_image TEXT")
                        cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS profile_image_data TEXT")
                    logger.info("✅ Profile image columns ensured during session creation")
                except Exception as migration_error:
                    logger.warning(f"Migration warning during session creation: {migration_error}")
                
                # Try new profile_image column first
                cursor.execute(f"SELECT created_at, profile_image, profile_picture_url FROM users WHERE id = {placeholder}", (user_data['user_id'],))
                result = cursor.fetchone()
                
                if result and result[0]:
                    if isinstance(result[0], str):
                        session['account_created'] = result[0]
                    else:
                        session['account_created'] = result[0].isoformat()
                    logger.info(f"Account creation date stored: {session['account_created']}")
                
                # Load profile image from database (check both columns)
                profile_img = None
                if result and len(result) > 1:
                    # Try profile_image column first (new)
                    if result[1]:
                        profile_img = result[1]
                        logger.info(f"Profile image loaded from profile_image column: {result[1]}")
                    # Fallback to profile_picture_url column (legacy)
                    elif len(result) > 2 and result[2]:
                        profile_img = result[2]
                        logger.info(f"Profile image loaded from profile_picture_url column: {result[2]}")
                
                if profile_img:
                    # 🔧 MIGRATION: Convert old filesystem paths to API endpoints
                    if profile_img.startswith('/static/uploads/profiles/'):
                        # Get user_id from the current result or session
                        user_id = user_data.get('id') or user_data.get('user_id')
                        if user_id:
                            profile_img = f"/api/profile-image/{user_id}"
                            logger.info(f"🔄 Migrated old filesystem path to API endpoint: {profile_img}")
                        else:
                            profile_img = '/static/logos/New IntroLogo.png'
                            logger.warning("Could not migrate filesystem path, using default")
                    
                    session['profile_image'] = profile_img
                    logger.info(f"✅ Profile image loaded from database: {profile_img}")
                else:
                    # Check if there's already a profile image in session (preserve uploads)
                    existing_profile = session.get('profile_image')
                    if existing_profile and existing_profile.startswith('/api/profile-image/'):
                        logger.info(f"🔄 Preserving existing uploaded profile image from session: {existing_profile}")
                        # Keep the existing uploaded image
                    else:
                        # Set default profile image if none exists and no upload in session
                        session['profile_image'] = '/static/logos/New IntroLogo.png'
                        logger.info("No profile image found, using default IntroLogo.png")
                    
            except Exception as profile_error:
                # If profile_image column doesn't exist, just get creation date
                logger.warning(f"Profile image column might not exist: {profile_error}")
                try:
                    cursor.execute(f"SELECT created_at FROM users WHERE id = {placeholder}", (user_data['user_id'],))
                    result = cursor.fetchone()
                    
                    if result and result[0]:
                        if isinstance(result[0], str):
                            session['account_created'] = result[0]
                        else:
                            session['account_created'] = result[0].isoformat()
                        logger.info(f"Account creation date stored: {session['account_created']}")
                        
                except Exception as date_error:
                    logger.warning(f"Could not fetch creation date: {date_error}")
                
                # Check if there's already a profile image in session (preserve uploads)
                existing_profile = session.get('profile_image')
                if existing_profile and existing_profile.startswith('/api/profile-image/'):
                    logger.info(f"🔄 Preserving existing uploaded profile image from session: {existing_profile}")
                    # Keep the existing uploaded image
                else:
                    # Set default profile image due to database schema issue
                    session['profile_image'] = '/static/logos/New IntroLogo.png'
                    logger.info("Set default profile image due to database schema issue")
            
            conn.close()
        except Exception as e:
            logger.warning(f"Could not fetch user data during login: {e}")
            # Check if there's already a profile image in session (preserve uploads) 
            existing_profile = session.get('profile_image')
            if existing_profile and existing_profile.startswith('/api/profile-image/'):
                logger.info(f"🔄 Preserving existing uploaded profile image from session after error: {existing_profile}")
                # Keep the existing uploaded image
            else:
                # Set default profile image on error
                session['profile_image'] = '/static/logos/New IntroLogo.png'
        
        logger.info(f"Secure session created for user: {user_data['email']}")
    
    def clear_session(self):
        """Clear user session"""
        user_email = session.get('user_email', 'unknown')
        session.clear()
        logger.info(f"Session cleared for user: {user_email}")
    
    def is_authenticated(self):
        """Check if user is authenticated"""
        return session.get('user_authenticated', False) and session.get('user_id')

# Decorator for protected routes
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_authenticated'):
            if request.is_json:
                return jsonify({"success": False, "error": "Authentication required"}), 401
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function