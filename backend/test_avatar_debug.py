#!/usr/bin/env python3
"""
Quick Avatar Persistence Debug Script
Run this to test if the avatar persistence is working
"""

def test_avatar_persistence():
    """Test avatar persistence functionality"""
    print("🧪 Testing Avatar Persistence System...")
    
    try:
        # Test 1: Import check
        print("\n1️⃣ Testing imports...")
        try:
            from modules.community.community_service import CommunityService
            print("✅ CommunityService imported successfully")
        except ImportError as e:
            print(f"❌ CommunityService import failed: {e}")
            return False
        
        try:
            from avatar_persistence_helper import AvatarPersistenceManager
            print("✅ AvatarPersistenceManager imported successfully")
        except ImportError as e:
            print(f"❌ AvatarPersistenceManager import failed: {e}")
        
        # Test 2: Database connection
        print("\n2️⃣ Testing database connection...")
        try:
            from database_utils import get_database
            db = get_database()
            if db:
                print("✅ Database connection available")
                
                # Test database query
                conn = db.get_connection()
                cursor = conn.cursor()
                
                if db.use_postgres:
                    cursor.execute("SELECT COUNT(*) FROM users")
                else:
                    cursor.execute("SELECT COUNT(*) FROM users")
                    
                user_count = cursor.fetchone()[0]
                print(f"✅ Database query successful - {user_count} users found")
                conn.close()
            else:
                print("❌ Database connection not available")
                
        except Exception as e:
            print(f"❌ Database test failed: {e}")
        
        # Test 3: Community service initialization
        print("\n3️⃣ Testing community service initialization...")
        try:
            from modules.community.companion_manager import CompanionManager
            companion_manager = CompanionManager()
            
            community_service = CommunityService(database=get_database(), companion_manager=companion_manager)
            print("✅ CommunityService initialized successfully")
            
            # Test avatar functionality
            test_user_id = 1  # Use a test user ID
            avatar_result = community_service.get_user_avatar(test_user_id)
            print(f"✅ Avatar retrieval test: {avatar_result['success']}")
            
            if avatar_result['success']:
                companion = avatar_result['companion']
                print(f"   - Companion: {companion.get('name', 'Unknown')}")
                print(f"   - Avatar URL: {companion.get('avatar_url', 'None')}")
                print(f"   - Cache buster: {'?t=' in companion.get('avatar_url', '') or '&t=' in companion.get('avatar_url', '')}")
            
        except Exception as e:
            print(f"❌ Community service test failed: {e}")
        
        print("\n✅ Avatar persistence debug complete!")
        return True
        
    except Exception as e:
        print(f"❌ Debug script failed: {e}")
        return False

if __name__ == "__main__":
    test_avatar_persistence()