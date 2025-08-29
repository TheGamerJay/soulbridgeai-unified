"""
Database Connection Manager
Centralized database access for all modules
"""
import sqlite3
import psycopg2
import os
from typing import Optional, Union
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Centralized database connection management"""
    
    def __init__(self):
        self.connection = None
        self._db_type = None
        
    def get_connection(self) -> Union[sqlite3.Connection, psycopg2.extensions.connection]:
        """Get database connection based on environment"""
        if self.connection is None:
            self._connect()
        return self.connection
    
    def _connect(self):
        """Establish database connection"""
        database_url = os.environ.get('DATABASE_URL')
        
        if database_url and database_url.startswith('postgresql'):
            # Production PostgreSQL
            try:
                self.connection = psycopg2.connect(database_url)
                self._db_type = 'postgresql'
                logger.info("✅ Connected to PostgreSQL database")
            except Exception as e:
                logger.error(f"❌ PostgreSQL connection failed: {e}")
                raise
        else:
            # Local SQLite fallback
            db_path = os.path.join('backend', 'soulbridge.db')
            try:
                self.connection = sqlite3.connect(db_path, check_same_thread=False)
                self.connection.row_factory = sqlite3.Row
                self._db_type = 'sqlite'
                logger.info("✅ Connected to SQLite database")
            except Exception as e:
                logger.error(f"❌ SQLite connection failed: {e}")
                raise
    
    def execute_query(self, query: str, params: tuple = None, fetch: str = None):
        """Execute database query with consistent interface"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            if fetch == 'one':
                result = cursor.fetchone()
                return dict(result) if result and self._db_type == 'sqlite' else result
            elif fetch == 'all':
                results = cursor.fetchall()
                return [dict(row) for row in results] if results and self._db_type == 'sqlite' else results
            else:
                conn.commit()
                return cursor.rowcount
        except Exception as e:
            conn.rollback()
            logger.error(f"❌ Database query failed: {e}")
            raise
        finally:
            cursor.close()
    
    def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            self.connection = None
            logger.info("📴 Database connection closed")

# Global database manager instance
db_manager = DatabaseManager()

def get_database():
    """Get global database manager instance"""
    return db_manager