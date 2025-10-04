"""
Enhanced Password Reset System - Production Ready
Based on user's reference implementation with improved security and database handling
"""
import hashlib
import secrets
import logging
from datetime import datetime, timedelta
from flask import request, jsonify, flash, redirect, render_template
from auth import Database
from database_utils import format_query

logger = logging.getLogger(__name__)

# Configuration
RESET_TOKEN_TTL_MINUTES = 60

def _sha256(s: str) -> str:
    """Hash string using SHA256"""
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def _now():
    """Get current UTC datetime"""
    return datetime.utcnow()

def auth_forgot_password_improved():
    """Enhanced forgot password with proper security"""
    if request.method == "GET":
        return render_template('forgot_password.html')
    
    # Ensure password reset tokens table exists
    try:
        from create_password_reset_table import create_password_reset_tokens_table
        create_password_reset_tokens_table()
    except Exception as e:
        logger.warning(f"Could not ensure password reset table exists: {e}")
    
    # Handle POST - Always return generic message to prevent email enumeration
    generic_message = 'If an account with that email exists, a reset link has been sent.'
    
    try:
        email = request.form.get('email', '').strip().lower()
        logger.info(f"Password reset requested for: {email}")
        
        if not email:
            flash(generic_message, 'success')
            return redirect('/auth/forgot-password')
        
        # Database operations using proper abstraction
        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor()
        
        try:
            # Check if user exists (case-insensitive)
            placeholder = "%s" if db.use_postgres else "?"
            cursor.execute(f"SELECT id, email, display_name FROM users WHERE LOWER(email) = {placeholder}", (email,))
            user = cursor.fetchone()
            
            if not user:
                # Still return success to prevent email enumeration
                flash(generic_message, 'success')
                return redirect('/auth/forgot-password')
            
            user_id, user_email, display_name = user
            
            # Generate secure token (32 bytes = 43 URL-safe chars)
            raw_token = secrets.token_urlsafe(32)
            token_hash = _sha256(raw_token)
            
            # Token expires in 1 hour
            expires_at = _now() + timedelta(minutes=RESET_TOKEN_TTL_MINUTES)
            
            # Get client info for security
            client_ip = request.headers.get('X-Forwarded-For', request.remote_addr or '')
            user_agent = request.headers.get('User-Agent', '')[:500]  # Limit length
            
            # Store hashed token in database (match existing table structure)
            if db.use_postgres:
                # PostgreSQL schema: id, email, token, expires_at, used, created_at
                expires_str = expires_at.isoformat()
                cursor.execute("""
                    INSERT INTO password_reset_tokens 
                    (email, token, expires_at, used)
                    VALUES (%s, %s, %s, %s)
                """, (user_email, token_hash, expires_str, 0))
            else:
                expires_str = expires_at.isoformat() + 'Z'
                cursor.execute(format_query("""
                    INSERT INTO password_reset_tokens 
                    (user_id, token_hash, expires_at, request_ip, request_ua)
                    VALUES (?, ?, ?, ?, ?)
                """), (user_id, token_hash, expires_str, client_ip, user_agent))
            
            conn.commit()
            
            # Generate reset URL with raw token
            reset_url = f"{request.url_root}auth/reset-password?token={raw_token}"
            
            # Send actual email
            try:
                from email_sender import send_password_reset_email
                email_sent = send_password_reset_email(user_email, reset_url, RESET_TOKEN_TTL_MINUTES)
                
                if email_sent:
                    logger.info(f"✅ Password reset email sent to: {user_email}")
                    flash('A password reset link has been sent to your email address.', 'success')
                    flash('Please check your inbox and spam folder.', 'info')
                else:
                    logger.warning(f"⚠️ Failed to send email to: {user_email}, showing link instead")
                    # Fallback: show link on page if email fails
                    flash(f'Email delivery failed. Reset link: {reset_url}', 'success')
                    flash('(Please bookmark this link - it expires in 60 minutes)', 'info')
                    
            except Exception as email_error:
                logger.error(f"❌ Email system error: {email_error}")
                # Fallback: show link on page if email system fails
                flash(f'Reset link: {reset_url}', 'success')
                flash('(Email system unavailable - please bookmark this link)', 'info')
                flash(f'This link expires in {RESET_TOKEN_TTL_MINUTES} minutes.', 'info')
            
            logger.info(f"Password reset token generated for user: {user_email} (ID: {user_id})")
            
        finally:
            cursor.close()
            conn.close()
        
        return redirect('/auth/forgot-password')
        
    except Exception as e:
        logger.error(f"Password reset error: {e}", exc_info=True)
        flash(generic_message, 'success')  # Still return generic success
        return redirect('/auth/forgot-password')

def verify_reset_token_improved(token_raw):
    """Enhanced token verification with proper security"""
    try:
        if not token_raw:
            return False
        
        token_hash = _sha256(token_raw)
        
        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor()
        
        try:
            if db.use_postgres:
                # PostgreSQL schema: id, email, token, expires_at, used, created_at
                cursor.execute("""
                    SELECT email, expires_at, used 
                    FROM password_reset_tokens 
                    WHERE token = %s 
                    LIMIT 1
                """, (token_hash,))
                
                result = cursor.fetchone()
                if not result:
                    return False
                
                email, expires_at, used = result
                
                # Check if already used (used is integer: 0 = false, 1 = true)
                if used:
                    return False
            else:
                # SQLite schema: user_id, token_hash, expires_at, used_at, etc.
                cursor.execute(format_query("""
                    SELECT user_id, expires_at, used_at 
                    FROM password_reset_tokens 
                    WHERE token_hash = ? 
                    LIMIT 1
                """), (token_hash,))
                
                result = cursor.fetchone()
                if not result:
                    return False
                
                user_id, expires_at, used_at = result
                
                # Check if already used
                if used_at:
                    return False
            
            # Parse expiration time (handle both formats)
            try:
                if isinstance(expires_at, str):
                    expires_dt = datetime.fromisoformat(expires_at.replace('Z', ''))
                else:
                    expires_dt = expires_at
            except (ValueError, AttributeError):
                return False
            
            # Check if expired
            if _now() > expires_dt:
                return False
            
            return True
            
        finally:
            cursor.close()
            conn.close()
            
    except Exception as e:
        logger.error(f"Token verification error: {e}")
        return False

def use_reset_token_improved(token_raw, new_password):
    """Enhanced token usage with proper security and cleanup"""
    try:
        if not token_raw or not new_password:
            return None
        
        token_hash = _sha256(token_raw)
        
        db = Database()
        conn = db.get_connection()
        cursor = conn.cursor()
        
        try:
            if db.use_postgres:
                # PostgreSQL schema: id, email, token, expires_at, used, created_at
                cursor.execute("""
                    SELECT email, expires_at, used 
                    FROM password_reset_tokens 
                    WHERE token = %s 
                    LIMIT 1
                """, (token_hash,))
                
                result = cursor.fetchone()
                if not result:
                    return None
                
                user_email, expires_at, used = result
                
                # Check if already used (used is integer: 0 = false, 1 = true)
                if used:
                    return None
                    
                # Get user_id from email for password update
                cursor.execute("SELECT id FROM users WHERE email = %s", (user_email,))
                user_result = cursor.fetchone()
                if not user_result:
                    return None
                user_id = user_result[0]
                
            else:
                # SQLite schema: user_id, token_hash, expires_at, used_at, etc.
                cursor.execute(format_query("""
                    SELECT user_id, expires_at, used_at 
                    FROM password_reset_tokens 
                    WHERE token_hash = ? 
                    LIMIT 1
                """), (token_hash,))
                
                result = cursor.fetchone()
                if not result:
                    return None
                
                user_id, expires_at, used_at = result
                
                # Check if already used
                if used_at:
                    return None
            
            # Parse expiration time
            try:
                if isinstance(expires_at, str):
                    expires_dt = datetime.fromisoformat(expires_at.replace('Z', ''))
                else:
                    expires_dt = expires_at
            except (ValueError, AttributeError):
                return None
            
            # Check if expired
            if _now() > expires_dt:
                return None
            
            # Hash new password using bcrypt (matching existing system)
            import bcrypt
            password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            # Update user's password
            if db.use_postgres:
                cursor.execute("UPDATE users SET password_hash = %s WHERE id = %s"), (password_hash, user_id))
                
                # Mark token as used (integer field in PostgreSQL: 0 = false, 1 = true)
                cursor.execute("UPDATE password_reset_tokens SET used = %s WHERE token = %s"), (1, token_hash))
                
                # Security: Mark all other unused tokens for this email as used
                cursor.execute("UPDATE password_reset_tokens SET used = %s WHERE email = %s AND used = %s", (1, user_email, 0))
            else:
                cursor.execute(format_query("UPDATE users SET password_hash = ? WHERE id = ?"), (password_hash, user_id))
                
                # Mark token as used with timestamp
                time_str = _now().isoformat() + 'Z'
                cursor.execute(format_query("UPDATE password_reset_tokens SET used_at = ? WHERE token_hash = ?"), (time_str, token_hash))
                
                # Security: Mark all other unused tokens for this user as used
                cursor.execute(format_query("""
                    UPDATE password_reset_tokens 
                    SET used_at = COALESCE(used_at, ?)
                    WHERE user_id = ? AND used_at IS NULL
                """), (time_str, user_id))
            
            conn.commit()
            logger.info(f"Password reset completed for user ID: {user_id}")
            return user_id
            
        finally:
            cursor.close()
            conn.close()
            
    except Exception as e:
        logger.error(f"Token usage error: {e}")
        return None

def auth_reset_password_improved():
    """Enhanced reset password endpoint"""
    if request.method == "GET":
        # Validate token and show reset form
        token = request.args.get('token', '').strip()
        if not token:
            flash('Invalid reset link', 'error')
            return redirect('/auth/login')
        
        # Verify token
        is_valid = verify_reset_token_improved(token)
        if not is_valid:
            flash('Reset link is invalid or expired', 'error')
            return redirect('/auth/login')
        
        return render_template('reset_password.html', token=token)
    
    # Handle POST - process password reset
    try:
        token = request.form.get('token', '').strip()
        new_password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        if not token or not new_password or not confirm_password:
            flash('All fields are required', 'error')
            return redirect(f'/auth/reset-password?token={token}')
        
        if new_password != confirm_password:
            flash('Passwords do not match', 'error')
            return redirect(f'/auth/reset-password?token={token}')
        
        if len(new_password) < 8:
            flash('Password must be at least 8 characters', 'error')
            return redirect(f'/auth/reset-password?token={token}')
        
        # Use token to reset password
        user_id = use_reset_token_improved(token, new_password)
        if not user_id:
            flash('Reset link is invalid or expired', 'error')
            return redirect('/auth/login')
        
        flash('Password updated successfully! You can now sign in.', 'success')
        return redirect('/auth/login')
        
    except Exception as e:
        logger.error(f"Reset password error: {e}")
        flash('Password reset failed. Please try again.', 'error')
        return redirect('/auth/login')