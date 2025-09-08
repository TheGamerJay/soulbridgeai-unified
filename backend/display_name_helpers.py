"""
Simple Display Name Helpers - One Writer, One Reader
Database is the source of truth
"""
import logging
from database_utils import get_database

logger = logging.getLogger(__name__)

def set_display_name(user_id: int, name: str) -> bool:
    """Set display name - DB write with commit"""
    try:
        db = get_database()
        if not db:
            logger.error("Database not available")
            return False
            
        conn = db.get_connection()
        try:
            placeholder = "%s" if hasattr(db, 'use_postgres') and db.use_postgres else "?"
            query = f"UPDATE users SET display_name = {placeholder} WHERE id = {placeholder}"
            
            cur = conn.cursor()
            cur.execute(query, (name.strip(), user_id))
            conn.commit()
            
            success = cur.rowcount > 0
            if success:
                logger.info(f"✅ WRITER: User {user_id} display name set to '{name.strip()}'")
            else:
                logger.error(f"❌ WRITER: User {user_id} not found")
                
            return success
            
        finally:
            conn.close()
            
    except Exception as e:
        logger.error(f"Failed to set display name for user {user_id}: {e}")
        return False

def get_display_name(user_id: int) -> str:
    """Get display name - DB read only"""
    try:
        db = get_database()
        if not db:
            logger.error("Database not available")
            return "User"
            
        conn = db.get_connection()
        try:
            placeholder = "%s" if hasattr(db, 'use_postgres') and db.use_postgres else "?"
            query = f"SELECT display_name, email FROM users WHERE id = {placeholder}"
            
            cur = conn.cursor()
            cur.execute(query, (user_id,))
            result = cur.fetchone()
            
            if result:
                db_name = result[0]
                email = result[1]
                
                if db_name and db_name.strip():
                    name = db_name.strip()
                    logger.info(f"✅ READER: User {user_id} display name '{name}'")
                    return name
                else:
                    # Fallback to email prefix
                    fallback = email.split('@')[0] if email else "User"
                    logger.info(f"📧 READER: User {user_id} using email fallback '{fallback}'")
                    return fallback
            else:
                logger.error(f"❌ READER: User {user_id} not found")
                return "User"
                
        finally:
            conn.close()
            
    except Exception as e:
        logger.error(f"Failed to get display name for user {user_id}: {e}")
        return "User"

def get_profile_image(user_id: int) -> str:
    """Get profile image URL - DB read only"""
    try:
        db = get_database()
        if not db:
            logger.error("Database not available")
            return "/static/logos/New IntroLogo.png"
            
        conn = db.get_connection()
        try:
            placeholder = "%s" if hasattr(db, 'use_postgres') and db.use_postgres else "?"
            query = f"SELECT profile_image, profile_image_data FROM users WHERE id = {placeholder}"
            
            cur = conn.cursor()
            cur.execute(query, (user_id,))
            result = cur.fetchone()
            
            if result:
                profile_image = result[0]
                profile_image_data = result[1]
                
                # If user has profile image data, return API endpoint
                if profile_image_data:
                    url = f"/api/profile-image/{user_id}"
                    logger.info(f"✅ READER: User {user_id} profile image from DB '{url}'")
                    return url
                # If user has profile_image path, use it
                elif profile_image:
                    logger.info(f"✅ READER: User {user_id} profile image path '{profile_image}'")
                    return profile_image
                else:
                    # Default image
                    default = "/static/logos/New IntroLogo.png"
                    logger.info(f"📷 READER: User {user_id} using default image '{default}'")
                    return default
            else:
                logger.error(f"❌ READER: User {user_id} not found")
                return "/static/logos/New IntroLogo.png"
                
        finally:
            conn.close()
            
    except Exception as e:
        logger.error(f"Failed to get profile image for user {user_id}: {e}")
        return "/static/logos/New IntroLogo.png"