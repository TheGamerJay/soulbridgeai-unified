"""
SoulBridge AI - Migration Runner
Command-line and programmatic migration execution
"""
import os
import sys
import logging
from datetime import datetime
from typing import Dict, Any
from .migration_manager import MigrationManager
from .schema_validator import SchemaValidator

logger = logging.getLogger(__name__)

class MigrationRunner:
    """Migration execution and management"""
    
    def __init__(self, database=None):
        self.database = database
        self.migration_manager = MigrationManager(database)
        self.schema_validator = SchemaValidator(database)
    
    def status_report(self) -> str:
        """Generate comprehensive migration status report"""
        report = ["**SoulBridge AI - Database Migration Status**\n"]
        
        # Migration status
        status = self.migration_manager.get_migration_status()
        report.append(f"**Migration Overview**:")
        report.append(f"  - Total Migrations: {status['total_migrations']}")
        report.append(f"  - Applied: {status['applied_migrations']}")
        report.append(f"  - Pending: {status['pending_migrations']}")
        
        # Module breakdown
        if status['modules']:
            report.append(f"\n**By Module**:")
            for module, stats in status['modules'].items():
                progress = f"{stats['applied']}/{stats['total']}"
                status_icon = "OK" if stats['pending'] == 0 else "PENDING"
                report.append(f"  {status_icon} {module}: {progress} ({stats['pending']} pending)")
        
        # Pending migrations
        if status['pending_list']:
            report.append(f"\n**Pending Migrations**:")
            pending = self.migration_manager.get_pending_migrations()
            for migration in pending:
                report.append(f"  - {migration['name']}: {migration['description']}")
        
        # Schema validation
        report.append(f"\n{self.schema_validator.get_schema_health_report()}")
        
        # Suggestions
        suggestions = self.schema_validator.suggest_migrations()
        if suggestions:
            report.append(f"\n**Recommended Actions**:")
            for suggestion in suggestions:
                report.append(f"  - Apply migration: {suggestion}")
        
        return "\n".join(report)
    
    def run_pending_migrations(self, confirm: bool = False) -> Dict[str, Any]:
        """Run all pending migrations"""
        pending = self.migration_manager.get_pending_migrations()
        
        if not pending:
            logger.info("✅ No pending migrations")
            return {"success": True, "message": "No pending migrations"}
        
        if not confirm:
            logger.info(f"Found {len(pending)} pending migrations. Use confirm=True to apply.")
            return {
                "success": False, 
                "message": f"Found {len(pending)} pending migrations",
                "pending": pending
            }
        
        logger.info(f"🔧 Applying {len(pending)} pending migrations...")
        
        result = self.migration_manager.apply_all_pending()
        
        if result["success"]:
            logger.info(f"✅ Successfully applied {result['applied']} migrations")
        else:
            logger.error(f"❌ {result['failed']} migrations failed")
        
        return result
    
    def run_specific_migration(self, migration_name: str) -> bool:
        """Run a specific migration"""
        logger.info(f"🔧 Applying migration: {migration_name}")
        
        if migration_name not in self.migration_manager.migrations:
            logger.error(f"Migration {migration_name} not found")
            return False
        
        return self.migration_manager.apply_migration(migration_name)
    
    def validate_and_migrate(self, auto_fix: bool = False) -> Dict[str, Any]:
        """Validate schema and optionally auto-fix issues"""
        logger.info("🔍 Validating database schema...")
        
        validation = self.schema_validator.validate_schema()
        
        if "error" in validation:
            return {"success": False, "error": validation["error"]}
        
        if validation["valid"] and not validation["warnings"]:
            logger.info("✅ Schema is healthy")
            return {"success": True, "message": "Schema is healthy", "validation": validation}
        
        logger.info(f"⚠️ Schema validation found {len(validation['issues'])} issues and {len(validation['warnings'])} warnings")
        
        if not auto_fix:
            return {
                "success": False,
                "message": "Schema validation failed - use auto_fix=True to attempt repairs",
                "validation": validation
            }
        
        # Attempt to fix issues automatically
        logger.info("🔧 Attempting to auto-fix schema issues...")
        
        suggested_migrations = self.schema_validator.suggest_migrations()
        
        if not suggested_migrations:
            return {
                "success": False,
                "message": "No automatic fixes available",
                "validation": validation
            }
        
        # Apply suggested migrations
        fixed_count = 0
        failed_count = 0
        
        for migration_name in suggested_migrations:
            if self.migration_manager.apply_migration(migration_name):
                fixed_count += 1
                logger.info(f"✅ Applied fix: {migration_name}")
            else:
                failed_count += 1
                logger.error(f"❌ Failed to apply: {migration_name}")
        
        # Re-validate after fixes
        new_validation = self.schema_validator.validate_schema()
        
        return {
            "success": failed_count == 0,
            "message": f"Applied {fixed_count} fixes, {failed_count} failed",
            "fixes_applied": fixed_count,
            "fixes_failed": failed_count,
            "validation_before": validation,
            "validation_after": new_validation
        }

def run_migration_cli():
    """Command-line interface for migrations"""
    if len(sys.argv) < 2:
        print("Usage: python migration_runner.py [status|migrate|validate|fix] [options]")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    try:
        # Import database (this would be adjusted based on your setup)
        from ...shared.database import get_database
        db = get_database()
        
        runner = MigrationRunner(db)
        
        if command == "status":
            print(runner.status_report())
            
        elif command == "migrate":
            confirm = "--confirm" in sys.argv
            result = runner.run_pending_migrations(confirm)
            if not result["success"]:
                print(f"❌ {result['message']}")
                sys.exit(1)
            else:
                print(f"✅ {result['message']}")
                
        elif command == "validate":
            validation = runner.schema_validator.validate_schema()
            print(runner.schema_validator.get_schema_health_report())
            if not validation["valid"]:
                sys.exit(1)
                
        elif command == "fix":
            auto_fix = "--auto" in sys.argv
            result = runner.validate_and_migrate(auto_fix)
            if not result["success"]:
                print(f"❌ {result['message']}")
                sys.exit(1)
            else:
                print(f"✅ {result['message']}")
                
        else:
            print(f"Unknown command: {command}")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Migration runner error: {e}")
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_migration_cli()