#!/usr/bin/env python3
"""
SoulBridge AI - Migration Status Checker
Check current database status and suggest migrations for modular architecture
"""
import os
import sys
import logging
from datetime import datetime

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def main():
    """Check migration status and provide recommendations"""
    try:
        # Import database and migration system
        from modules.shared.database import get_database
        from modules.database.migration_runner import MigrationRunner
        
        print("SoulBridge AI - Database Migration Status Check")
        print("=" * 60)
        
        # Initialize database connection
        db = get_database()
        if not db:
            print("❌ Could not connect to database")
            return
        
        # Initialize migration runner
        runner = MigrationRunner(db)
        
        # Get and display status report
        report = runner.status_report()
        print(report)
        
        # Check if migrations are needed
        status = runner.migration_manager.get_migration_status()
        
        if status['pending_migrations'] > 0:
            print(f"\n** Action Required **:")
            print(f"You have {status['pending_migrations']} pending migrations.")
            print("\nTo apply all pending migrations, run:")
            print("python check_migration_status.py --migrate")
            print("\nTo apply migrations automatically with validation:")
            print("python check_migration_status.py --fix-auto")
        else:
            print("\n** All migrations are up to date! **")
            
            # Still check schema health
            validation = runner.schema_validator.validate_schema()
            if not validation["valid"] or validation["warnings"]:
                print("However, schema validation found some issues.")
                print("Run with --validate for details")
        
        print("\n" + "=" * 60)
        
    except ImportError as e:
        print(f"Import error: {e}")
        print("Make sure you're running from the backend directory")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

def run_migrations():
    """Apply pending migrations"""
    try:
        from modules.shared.database import get_database
        from modules.database.migration_runner import MigrationRunner
        
        db = get_database()
        runner = MigrationRunner(db)
        
        print("Applying all pending migrations...")
        result = runner.run_pending_migrations(confirm=True)
        
        if result["success"]:
            print(f"Successfully applied {result.get('applied', 0)} migrations")
        else:
            print(f"Migration failed: {result.get('message', 'Unknown error')}")
            return False
            
        return True
        
    except Exception as e:
        print(f"Migration error: {e}")
        return False

def validate_schema():
    """Validate current schema"""
    try:
        from modules.shared.database import get_database
        from modules.database.migration_runner import MigrationRunner
        
        db = get_database()
        runner = MigrationRunner(db)
        
        print("Validating database schema...")
        report = runner.schema_validator.get_schema_health_report()
        print(report)
        
    except Exception as e:
        print(f"Validation error: {e}")

def auto_fix():
    """Auto-fix schema issues"""
    try:
        from modules.shared.database import get_database
        from modules.database.migration_runner import MigrationRunner
        
        db = get_database()
        runner = MigrationRunner(db)
        
        print("Auto-fixing schema issues...")
        result = runner.validate_and_migrate(auto_fix=True)
        
        if result["success"]:
            print(f"Applied {result.get('fixes_applied', 0)} fixes")
        else:
            print(f"Auto-fix failed: {result.get('message', 'Unknown error')}")
            
    except Exception as e:
        print(f"Auto-fix error: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "--migrate":
            run_migrations()
        elif command == "--validate":
            validate_schema()
        elif command == "--fix-auto":
            auto_fix()
        else:
            print(f"Unknown option: {command}")
            print("Available options: --migrate, --validate, --fix-auto")
    else:
        main()