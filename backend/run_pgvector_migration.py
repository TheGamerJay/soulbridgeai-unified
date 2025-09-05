#!/usr/bin/env python3
"""
Run pgvector Migration
Execute the pgvector extension setup for embedding-based lyric retrieval
"""

import os
import sys
from dotenv import load_dotenv
from database_migrations.add_pgvector_extension import run_pgvector_migration, check_pgvector_status
import json

def main():
    """Main migration runner"""
    print("pgvector Migration Runner")
    print("=" * 50)
    
    # Load environment variables
    load_dotenv()
    
    DATABASE_URL = os.environ.get('DATABASE_URL')
    if not DATABASE_URL:
        print("ERROR: DATABASE_URL environment variable not set")
        print("Please set DATABASE_URL in your .env file")
        return False
    
    print(f"Database: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'Local'}")
    
    # Check current status first
    print("\nChecking current pgvector status...")
    status = check_pgvector_status()
    
    if status['status'] == 'success':
        print("Database connection successful")
        print(f"Extension installed: {status.get('extension_installed', False)}")
        print(f"Tables created: {status.get('tables_created', [])}")
        print(f"Similarity function: {status.get('similarity_function', False)}")
        print(f"Ready for use: {status.get('ready', False)}")
        
        if status.get('ready'):
            print("\npgvector is already fully configured!")
            return True
    else:
        print(f"Status check failed: {status.get('message', 'Unknown error')}")
    
    # Run migration
    print("\nRunning pgvector migration...")
    success = run_pgvector_migration()
    
    if success:
        print("\nMigration completed successfully!")
        
        # Verify final status
        print("\nVerifying installation...")
        final_status = check_pgvector_status()
        
        if final_status['status'] == 'success' and final_status.get('ready'):
            print("pgvector setup is complete and ready for use!")
            
            # Show statistics
            print("\nFinal Configuration:")
            print(f"   Extension: {'YES' if final_status.get('extension_installed') else 'NO'}")
            print(f"   Tables: {', '.join(final_status.get('tables_created', []))}")
            print(f"   Search Function: {'YES' if final_status.get('similarity_function') else 'NO'}")
            
            return True
        else:
            print("Installation verification failed")
            print(json.dumps(final_status, indent=2))
            return False
    else:
        print("\nMigration failed!")
        print("Check the logs above for error details")
        print("Ensure your PostgreSQL instance supports pgvector extension")
        return False

if __name__ == "__main__":
    import logging
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    success = main()
    sys.exit(0 if success else 1)