"""
SoulBridge AI - Schema Validator
Validates database schema and identifies issues
"""
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class SchemaValidator:
    """Database schema validation and health checking"""
    
    def __init__(self, database=None):
        self.database = database
        self.expected_tables = self._get_expected_schema()
    
    def _get_expected_schema(self) -> Dict[str, Dict[str, Any]]:
        """Define expected database schema"""
        return {
            "users": {
                "required_columns": [
                    "id", "email", "password_hash", "display_name", "created_at",
                    "user_plan", "trial_active", "trial_expires_at", "stripe_customer_id"
                ],
                "deprecated_columns": [
                    "plan_type", "trial_companion", "companion_data", 
                    "feature_preview_seen", "trial_warning_sent"
                ],
                "indexes": ["idx_users_email", "idx_users_stripe_customer_id"]
            },
            "migration_history": {
                "required_columns": [
                    "id", "migration_name", "description", "module", 
                    "applied_at", "rollback_sql", "checksum"
                ],
                "indexes": ["idx_migration_history_name"]
            },
            "voice_journal_entries": {
                "required_columns": [
                    "id", "user_id", "transcription", "analysis_summary",
                    "emotions", "mood_score", "created_at"
                ],
                "indexes": ["idx_voice_journal_user_id", "idx_voice_journal_created_at"]
            },
            "voice_chat_sessions": {
                "required_columns": [
                    "id", "user_id", "companion_id", "session_start", "created_at"
                ],
                "indexes": ["idx_voice_chat_user_id", "idx_voice_chat_companion"]
            },
            "email_sent_log": {
                "required_columns": [
                    "id", "user_id", "recipient_email", "email_type", "sent_at"
                ],
                "indexes": ["idx_email_log_user_id", "idx_email_log_type"]
            },
            "credit_transactions": {
                "required_columns": [
                    "id", "user_id", "transaction_type", "amount", 
                    "balance_before", "balance_after", "created_at"
                ],
                "indexes": ["idx_credit_transactions_user_id"]
            }
        }
    
    def get_current_schema(self) -> Dict[str, Any]:
        """Get current database schema"""
        try:
            if not self.database:
                return {"error": "Database not available"}
            
            conn = self.database.get_connection()
            cursor = conn.cursor()
            
            schema = {"tables": {}, "indexes": []}
            
            if hasattr(self.database, 'use_postgres') and self.database.use_postgres:
                # PostgreSQL schema query
                cursor.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
                    ORDER BY table_name
                """)
                tables = cursor.fetchall()
                
                for (table_name,) in tables:
                    # Get columns for each table
                    cursor.execute("""
                        SELECT column_name, data_type, is_nullable, column_default
                        FROM information_schema.columns
                        WHERE table_name = %s AND table_schema = 'public'
                        ORDER BY ordinal_position
                    """, (table_name,))
                    
                    columns = cursor.fetchall()
                    schema["tables"][table_name] = {
                        "columns": [
                            {
                                "name": col[0],
                                "type": col[1], 
                                "nullable": col[2] == "YES",
                                "default": col[3]
                            } 
                            for col in columns
                        ]
                    }
                
                # Get indexes
                cursor.execute("""
                    SELECT indexname, tablename 
                    FROM pg_indexes 
                    WHERE schemaname = 'public'
                    ORDER BY tablename, indexname
                """)
                indexes = cursor.fetchall()
                schema["indexes"] = [{"name": idx[0], "table": idx[1]} for idx in indexes]
                
            else:
                # SQLite schema query
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
                tables = cursor.fetchall()
                
                for (table_name,) in tables:
                    # Get columns for each table
                    cursor.execute(f"PRAGMA table_info({table_name})")
                    columns = cursor.fetchall()
                    
                    schema["tables"][table_name] = {
                        "columns": [
                            {
                                "name": col[1],
                                "type": col[2],
                                "nullable": not col[3],
                                "default": col[4]
                            }
                            for col in columns
                        ]
                    }
                
                # Get indexes
                cursor.execute("""
                    SELECT name, tbl_name 
                    FROM sqlite_master 
                    WHERE type='index' AND name NOT LIKE 'sqlite_%'
                    ORDER BY tbl_name, name
                """)
                indexes = cursor.fetchall()
                schema["indexes"] = [{"name": idx[0], "table": idx[1]} for idx in indexes]
            
            conn.close()
            return schema
            
        except Exception as e:
            logger.error(f"Error getting current schema: {e}")
            return {"error": str(e)}
    
    def validate_schema(self) -> Dict[str, Any]:
        """Validate current schema against expected schema"""
        current_schema = self.get_current_schema()
        
        if "error" in current_schema:
            return current_schema
        
        validation_results = {
            "valid": True,
            "issues": [],
            "warnings": [],
            "missing_tables": [],
            "missing_columns": {},
            "deprecated_columns": {},
            "missing_indexes": [],
            "summary": {}
        }
        
        current_tables = set(current_schema["tables"].keys())
        expected_tables = set(self.expected_tables.keys())
        
        # Check for missing tables
        missing_tables = expected_tables - current_tables
        if missing_tables:
            validation_results["missing_tables"] = list(missing_tables)
            validation_results["valid"] = False
            validation_results["issues"].extend([
                f"Missing table: {table}" for table in missing_tables
            ])
        
        # Check for extra tables (informational)
        extra_tables = current_tables - expected_tables
        if extra_tables:
            validation_results["warnings"].extend([
                f"Unexpected table: {table}" for table in extra_tables
            ])
        
        # Validate each expected table
        for table_name, expected_table in self.expected_tables.items():
            if table_name not in current_tables:
                continue  # Already handled as missing table
            
            current_table = current_schema["tables"][table_name]
            current_columns = {col["name"] for col in current_table["columns"]}
            
            # Check for missing required columns
            required_columns = set(expected_table.get("required_columns", []))
            missing_columns = required_columns - current_columns
            
            if missing_columns:
                validation_results["missing_columns"][table_name] = list(missing_columns)
                validation_results["valid"] = False
                validation_results["issues"].extend([
                    f"Missing column {table_name}.{col}" for col in missing_columns
                ])
            
            # Check for deprecated columns
            deprecated_columns = set(expected_table.get("deprecated_columns", []))
            found_deprecated = deprecated_columns & current_columns
            
            if found_deprecated:
                validation_results["deprecated_columns"][table_name] = list(found_deprecated)
                validation_results["warnings"].extend([
                    f"Deprecated column {table_name}.{col}" for col in found_deprecated
                ])
        
        # Check for missing indexes
        current_index_names = {idx["name"] for idx in current_schema["indexes"]}
        expected_indexes = []
        for table_data in self.expected_tables.values():
            expected_indexes.extend(table_data.get("indexes", []))
        
        missing_indexes = set(expected_indexes) - current_index_names
        if missing_indexes:
            validation_results["missing_indexes"] = list(missing_indexes)
            validation_results["warnings"].extend([
                f"Missing index: {idx}" for idx in missing_indexes
            ])
        
        # Summary
        validation_results["summary"] = {
            "total_issues": len(validation_results["issues"]),
            "total_warnings": len(validation_results["warnings"]),
            "schema_health": "healthy" if validation_results["valid"] and not validation_results["warnings"] else 
                           "needs_attention" if validation_results["valid"] else "critical"
        }
        
        return validation_results
    
    def get_schema_health_report(self) -> str:
        """Get human-readable schema health report"""
        validation = self.validate_schema()
        
        if "error" in validation:
            return f"Schema validation failed: {validation['error']}"
        
        report = ["**Database Schema Health Report**\n"]
        
        # Overall status
        health = validation["summary"]["schema_health"]
        if health == "healthy":
            report.append("**Status**: Healthy - No issues found")
        elif health == "needs_attention":
            report.append("**Status**: Needs Attention - Warnings found")
        else:
            report.append("**Status**: Critical - Issues require immediate attention")
        
        # Issues
        if validation["issues"]:
            report.append(f"\n**Critical Issues** ({len(validation['issues'])}):")
            for issue in validation["issues"]:
                report.append(f"  - {issue}")
        
        # Warnings
        if validation["warnings"]:
            report.append(f"\n**Warnings** ({len(validation['warnings'])}):")
            for warning in validation["warnings"]:
                report.append(f"  - {warning}")
        
        # Recommendations
        report.append("\n**Recommendations**:")
        if validation["missing_tables"]:
            report.append("  - Run pending migrations to create missing tables")
        if validation["missing_columns"]:
            report.append("  - Apply schema migrations to add missing columns")
        if validation["deprecated_columns"]:
            report.append("  - Consider cleanup migration to remove deprecated columns")
        if validation["missing_indexes"]:
            report.append("  - Add missing indexes for better performance")
        
        if validation["valid"] and not validation["warnings"]:
            report.append("  - Schema is healthy - no action needed")
        
        return "\n".join(report)
    
    def suggest_migrations(self) -> List[str]:
        """Suggest which migrations should be applied"""
        validation = self.validate_schema()
        suggestions = []
        
        if "error" in validation:
            return [f"Cannot suggest migrations: {validation['error']}"]
        
        if validation["missing_tables"]:
            # Check which migrations would create missing tables
            if "migration_history" in validation["missing_tables"]:
                suggestions.append("001_create_migration_tracking")
            if "voice_journal_entries" in validation["missing_tables"]:
                suggestions.append("003_voice_module_support")
            if "email_sent_log" in validation["missing_tables"]:
                suggestions.append("004_notifications_module_support")
            if "credit_transactions" in validation["missing_tables"]:
                suggestions.append("005_credits_system_consolidation")
        
        if validation["deprecated_columns"]:
            suggestions.append("002_cleanup_deprecated_user_columns")
        
        if validation["missing_columns"]:
            for table, columns in validation["missing_columns"].items():
                if table == "users" and any(col in ["monthly_credits", "credits_reset_date"] for col in columns):
                    suggestions.append("005_credits_system_consolidation")
        
        return suggestions