"""
Database Schema Fix API Route
Allows manual execution of database fixes on Railway deployment
"""
import logging
import os
import psycopg2
from flask import Blueprint, jsonify

logger = logging.getLogger(__name__)

# Create blueprint
bp = Blueprint('api_database_fix', __name__)

@bp.route("/api/database/emergency-fix", methods=['GET', 'POST'])
def emergency_database_fix():
    """Emergency fix for persistent database schema errors"""
    try:
        from emergency_database_fix import emergency_fix
        success = emergency_fix()
        return jsonify({
            "success": success,
            "message": "Emergency database fix completed" if success else "Emergency fix failed"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Emergency fix failed: {str(e)}"
        }), 500

@bp.route("/api/database/nuclear-fix", methods=['GET', 'POST'])
def nuclear_database_fix():
    """Nuclear database fix - completely rebuild schema"""
    try:
        from nuclear_database_fix import nuclear_fix
        success = nuclear_fix()
        return jsonify({
            "success": success,
            "message": "Nuclear database fix completed - schema completely rebuilt!" if success else "Nuclear fix failed"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Nuclear fix failed: {str(e)}"
        }), 500

@bp.route("/api/database/inspect", methods=['GET'])
def inspect_database():
    """Inspect actual database schema and column names"""
    try:
        from database_inspector import inspect_database
        success = inspect_database()
        return jsonify({
            "success": success,
            "message": "Database inspection completed - check logs for details"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Database inspection failed: {str(e)}"
        }), 500

@bp.route("/api/database/columns", methods=['GET'])
def show_columns():
    """Show all database table columns"""
    try:
        from show_columns import show_columns
        success = show_columns()
        return jsonify({
            "success": success,
            "message": "Database columns displayed - check logs for table structures"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Show columns failed: {str(e)}"
        }), 500

@bp.route("/api/database/fix-schema", methods=['GET', 'POST'])
def fix_database_schema():
    """Fix missing database tables and columns"""
    from flask import request
    
    # GET request returns info about what the endpoint does
    if request.method == 'GET':
        return jsonify({
            "success": True,
            "message": "Database schema fix endpoint",
            "description": "POST to this endpoint to fix missing database tables and columns",
            "fixes": [
                "Creates feature_usage table if missing",
                "Adds credits, last_credit_reset, purchased_credits columns to users table",
                "Creates performance indexes"
            ]
        })
    
    # POST request performs the actual fix
    try:
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            return jsonify({
                "success": False,
                "error": "DATABASE_URL not found in environment"
            }), 500
            
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        results = []
        
        # 1. Create feature_usage table if it doesn't exist
        logger.info("🔧 Creating feature_usage table...")
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS feature_usage (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    feature_name VARCHAR(50) NOT NULL,
                    usage_date DATE NOT NULL,
                    usage_count INTEGER DEFAULT 1,
                    last_used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, feature_name, usage_date)
                )
            """)
            results.append("✅ Created/verified feature_usage table")
        except Exception as e:
            results.append(f"❌ Error creating feature_usage table: {e}")
        
        # 2. Add missing columns to users table
        missing_columns = [
            ('credits', 'INTEGER DEFAULT 0'),
            ('last_credit_reset', 'TIMESTAMP'),
            ('purchased_credits', 'INTEGER DEFAULT 0')
        ]
        
        for column_name, column_type in missing_columns:
            try:
                logger.info(f"🔧 Adding column '{column_name}' to users table...")
                cursor.execute(f"ALTER TABLE users ADD COLUMN {column_name} {column_type}")
                results.append(f"✅ Added column '{column_name}' to users table")
            except psycopg2.errors.DuplicateColumn:
                results.append(f"⚠️ Column '{column_name}' already exists")
                conn.rollback()  # Rollback the failed transaction
            except Exception as e:
                results.append(f"❌ Error adding column '{column_name}': {e}")
                conn.rollback()
        
        # 3. Create indexes for performance
        logger.info("🔧 Creating indexes for performance...")
        try:
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_feature_usage_user_feature_date ON feature_usage(user_id, feature_name, usage_date)")
            results.append("✅ Created feature_usage index")
        except Exception as e:
            results.append(f"⚠️ Index creation warning: {e}")
        
        # Commit all changes
        conn.commit()
        conn.close()
        
        logger.info("🎉 Database schema fix completed successfully!")
        
        return jsonify({
            "success": True,
            "message": "Database schema fix completed",
            "results": results
        })
        
    except Exception as e:
        logger.error(f"❌ Database schema fix failed: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "message": "Database schema fix failed"
        }), 500