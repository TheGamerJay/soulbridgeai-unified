"""
Simple test script for AI insights system without unicode issues
"""
import sqlite3
import sys
import os
from datetime import datetime, timedelta
import random
import uuid

# Simple database manager to avoid unicode issues
class SimpleDB:
    def __init__(self, db_file):
        self.db_file = db_file
        self.connection = sqlite3.connect(db_file)
        
    def fetch_all(self, query, params=()):
        cursor = self.connection.cursor()
        cursor.execute(query, params)
        return cursor.fetchall()
    
    def fetch_one(self, query, params=()):
        cursor = self.connection.cursor()
        cursor.execute(query, params)
        return cursor.fetchone()
    
    def execute_query(self, query, params=()):
        cursor = self.connection.cursor()
        cursor.execute(query, params)
        self.connection.commit()
        return cursor.rowcount

def create_test_data():
    """Create test database with sample mood data"""
    db = SimpleDB('simple_test.db')
    
    # Create tables
    db.execute_query('''
        CREATE TABLE IF NOT EXISTS mood_entries (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            mood TEXT NOT NULL,
            score REAL NOT NULL,
            notes TEXT,
            created_at DATETIME NOT NULL
        )
    ''')
    
    # Clear existing data
    db.execute_query('DELETE FROM mood_entries')
    
    # Create sample mood data for user 'test_user'
    moods = ['happy', 'sad', 'anxious', 'excited', 'calm', 'stressed', 'content']
    user_id = 'test_user'
    
    print("Creating sample mood data...")
    
    for i in range(30):  # 30 days of data
        date = datetime.now() - timedelta(days=i)
        
        # 1-2 mood entries per day
        for j in range(random.randint(1, 2)):
            mood = random.choice(moods)
            
            # Assign scores based on mood
            if mood in ['happy', 'excited', 'calm', 'content']:
                score = random.uniform(0.6, 1.0)
            elif mood in ['sad', 'anxious', 'stressed']:
                score = random.uniform(0.1, 0.5)
            else:
                score = random.uniform(0.3, 0.7)
            
            entry_time = date.replace(
                hour=random.randint(8, 22),
                minute=random.randint(0, 59),
                second=0,
                microsecond=0
            )
            
            notes = f"Feeling {mood} today"
            
            db.execute_query('''
                INSERT INTO mood_entries (id, user_id, mood, score, notes, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (str(uuid.uuid4()), user_id, mood, score, notes, entry_time))
    
    print(f"Created mood data for {user_id}")
    return db

def test_mood_analysis():
    """Test mood pattern analysis directly"""
    db = create_test_data()
    
    # Import and test insights
    sys.path.append(os.path.dirname(__file__))
    from ai_insights import AIInsightsEngine
    
    # Create insights engine with simple DB
    engine = AIInsightsEngine(db_manager=db)
    
    print("\n=== Testing Mood Pattern Analysis ===")
    
    # Test mood patterns
    patterns = engine.analyze_mood_patterns('test_user', days=30)
    
    print(f"Found {len(patterns)} mood patterns:")
    for pattern in patterns:
        print(f"- {pattern.dominant_mood}:")
        print(f"  Average score: {pattern.average_score:.2f}")
        print(f"  Stability: {pattern.mood_stability:.2f}")
        print(f"  Common times: {pattern.common_times}")
        print(f"  Triggers: {pattern.triggers}")
        print()
    
    print("=== Testing Companion Recommendations ===")
    
    # Test companion recommendations
    companions = engine.recommend_companions('test_user')
    
    print(f"Found {len(companions)} companion recommendations:")
    for comp in companions:
        print(f"- {comp.companion_name}: {comp.match_score:.2f} match")
        print(f"  Style: {comp.interaction_style}")
        print(f"  Reasons: {comp.reasons}")
        print()
    
    print("=== Testing Wellness Alerts ===")
    
    # Test wellness alerts
    alerts = engine.generate_wellness_alerts('test_user')
    
    print(f"Found {len(alerts)} wellness alerts:")
    for alert in alerts:
        print(f"- {alert.alert_type} ({alert.severity})")
        print(f"  Message: {alert.message}")
        print(f"  Recommendations: {alert.recommendations}")
        print()
    
    # Test raw data query
    print("=== Raw Mood Data ===")
    mood_data = db.fetch_all('''
        SELECT mood, score, created_at 
        FROM mood_entries 
        WHERE user_id = ? 
        ORDER BY created_at DESC 
        LIMIT 10
    ''', ('test_user',))
    
    print("Recent mood entries:")
    for mood, score, timestamp in mood_data:
        print(f"- {mood}: {score:.2f} at {timestamp}")
    
    db.connection.close()
    print("\nTest completed successfully!")

if __name__ == "__main__":
    test_mood_analysis()