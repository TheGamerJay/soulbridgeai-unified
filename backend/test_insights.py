"""
Test script for AI insights system
Creates sample data and tests the insights functionality
"""
import sqlite3
import json
import uuid
from datetime import datetime, timedelta
import random

def create_test_database():
    """Create a test database with sample data"""
    # Connect to database
    conn = sqlite3.connect('test_soulbridge.db')
    cursor = conn.cursor()
    
    # Create necessary tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS mood_entries (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            mood TEXT NOT NULL,
            score REAL NOT NULL,
            notes TEXT,
            created_at DATETIME NOT NULL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_profiles (
            user_id TEXT PRIMARY KEY,
            display_name TEXT NOT NULL,
            email TEXT,
            bio TEXT,
            avatar_url TEXT,
            public_profile BOOLEAN DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id TEXT PRIMARY KEY,
            conversation_id TEXT NOT NULL,
            sender_id TEXT NOT NULL,
            recipient_id TEXT NOT NULL,
            content TEXT NOT NULL,
            message_type TEXT DEFAULT 'text',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS conversations (
            id TEXT PRIMARY KEY,
            user1_id TEXT NOT NULL,
            user2_id TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_insights_cache (
            user_id TEXT PRIMARY KEY,
            insights_data TEXT NOT NULL,
            created_at DATETIME NOT NULL
        )
    ''')
    
    # Sample users
    test_users = [
        {'user_id': 'user1', 'display_name': 'Alice', 'email': 'alice@test.com'},
        {'user_id': 'user2', 'display_name': 'Bob', 'email': 'bob@test.com'},
        {'user_id': 'user3', 'display_name': 'Charlie', 'email': 'charlie@test.com'}
    ]
    
    for user in test_users:
        cursor.execute('''
            INSERT OR REPLACE INTO user_profiles (user_id, display_name, email, bio, public_profile)
            VALUES (?, ?, ?, ?, ?)
        ''', (user['user_id'], user['display_name'], user['email'], 'Test user profile', 1))
    
    # Sample mood data for last 30 days
    moods = ['happy', 'sad', 'anxious', 'excited', 'calm', 'stressed', 'content', 'overwhelmed']
    
    for user in test_users:
        user_id = user['user_id']
        
        for i in range(30):
            date = datetime.now() - timedelta(days=i)
            
            # Generate 1-3 mood entries per day
            num_entries = random.randint(1, 3)
            
            for j in range(num_entries):
                mood = random.choice(moods)
                # Score based on mood (roughly)
                if mood in ['happy', 'excited', 'calm', 'content']:
                    score = random.uniform(0.6, 1.0)
                elif mood in ['sad', 'anxious', 'stressed', 'overwhelmed']:
                    score = random.uniform(0.1, 0.5)
                else:
                    score = random.uniform(0.3, 0.7)
                
                # Add some noise based on time
                hour_offset = random.randint(0, 23)
                entry_time = date.replace(hour=hour_offset, minute=random.randint(0, 59))
                
                notes = f"Feeling {mood} today. Had some work to do."
                if mood == 'stressed':
                    notes = "Work was really overwhelming today. Too many deadlines."
                elif mood == 'happy':
                    notes = "Great day! Exercise made me feel good."
                elif mood == 'anxious':
                    notes = "Worried about the presentation tomorrow."
                
                cursor.execute('''
                    INSERT INTO mood_entries (id, user_id, mood, score, notes, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (str(uuid.uuid4()), user_id, mood, score, notes, entry_time))
    
    # Sample messages between users
    conversations = [
        ('user1', 'user2'),
        ('user1', 'user3'),
        ('user2', 'user3')
    ]
    
    for user1, user2 in conversations:
        conv_id = str(uuid.uuid4())
        cursor.execute('''
            INSERT INTO conversations (id, user1_id, user2_id)
            VALUES (?, ?, ?)
        ''', (conv_id, user1, user2))
        
        # Add some messages
        messages = [
            "Hey, how are you feeling today?",
            "I'm doing pretty well, thanks for asking!",
            "Want to chat about what's on your mind?",
            "Sure, I've been a bit stressed lately with work.",
            "I understand. Maybe we can do something relaxing together?"
        ]
        
        for i, content in enumerate(messages):
            sender = user1 if i % 2 == 0 else user2
            recipient = user2 if i % 2 == 0 else user1
            
            cursor.execute('''
                INSERT INTO messages (id, conversation_id, sender_id, recipient_id, content)
                VALUES (?, ?, ?, ?, ?)
            ''', (str(uuid.uuid4()), conv_id, sender, recipient, content))
    
    conn.commit()
    conn.close()
    print("Test database created with sample data!")

def test_insights():
    """Test the AI insights functionality"""
    from models import SoulBridgeDB
    from ai_insights import init_ai_insights, init_insights_database
    
    # Initialize database
    db = SoulBridgeDB('test_soulbridge.db')
    
    # Initialize insights database tables
    conn = sqlite3.connect('test_soulbridge.db')
    init_insights_database(conn)
    conn.close()
    
    # Initialize AI insights engine
    ai_insights = init_ai_insights(db, None)
    
    if not ai_insights:
        print("Failed to initialize AI insights engine")
        return
    
    # Test mood pattern analysis
    print("\n=== Testing Mood Pattern Analysis ===")
    patterns = ai_insights.analyze_mood_patterns('user1', days=30)
    print(f"Found {len(patterns)} mood patterns for user1:")
    for pattern in patterns[:3]:
        print(f"- {pattern.dominant_mood}: avg score {pattern.average_score:.2f}, stability {pattern.mood_stability:.2f}")
    
    # Test personality analysis
    print("\n=== Testing Personality Analysis ===")
    personality = ai_insights.analyze_personality('user1')
    if personality:
        print(f"Personality type: {personality.personality_type}")
        print(f"Communication style: {personality.communication_style}")
        print(f"Activity preferences: {personality.activity_preferences}")
    else:
        print("No personality data available")
    
    # Test companion recommendations
    print("\n=== Testing Companion Recommendations ===")
    companions = ai_insights.recommend_companions('user1')
    print(f"Found {len(companions)} companion recommendations:")
    for comp in companions[:3]:
        print(f"- {comp.companion_name}: {comp.match_score:.2f} match ({comp.interaction_style})")
    
    # Test wellness alerts
    print("\n=== Testing Wellness Alerts ===")
    alerts = ai_insights.generate_wellness_alerts('user1')
    print(f"Found {len(alerts)} wellness alerts:")
    for alert in alerts:
        print(f"- {alert.alert_type} ({alert.severity}): {alert.message}")
    
    # Test comprehensive insights
    print("\n=== Testing Comprehensive Insights ===")
    insights = ai_insights.get_comprehensive_insights('user1')
    if insights:
        print(f"Generated comprehensive insights for {insights.user_id}")
        print(f"- {len(insights.mood_patterns)} mood patterns")
        print(f"- {len(insights.companion_recommendations)} companion recommendations")
        print(f"- {len(insights.wellness_alerts)} wellness alerts")
    else:
        print("No comprehensive insights available")

if __name__ == "__main__":
    print("Creating test database...")
    create_test_database()
    
    print("\nTesting AI insights...")
    test_insights()
    
    print("\nTest completed!")