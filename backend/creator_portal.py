"""
Creator Portal System for SoulBridge AI
Professional dashboard for wellness content creators and monetization
"""
import logging
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import decimal

logger = logging.getLogger(__name__)

class CreatorStatus(Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    SUSPENDED = "suspended"
    FEATURED = "featured"

class ContentStatus(Enum):
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    PUBLISHED = "published"
    ARCHIVED = "archived"

class MonetizationModel(Enum):
    FREE = "free"
    ONE_TIME_PURCHASE = "one_time_purchase"
    SUBSCRIPTION = "subscription"
    PAY_PER_VIEW = "pay_per_view"
    DONATION_BASED = "donation_based"

class PaymentStatus(Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"

@dataclass
class CreatorProfile:
    creator_id: str
    user_id: str
    business_name: str
    creator_status: CreatorStatus
    specializations: List[str]
    bio: str
    website: Optional[str]
    social_links: Dict[str, str]
    verification_documents: List[str]
    tax_info: Dict[str, Any]
    bank_info: Dict[str, Any]
    revenue_share: float  # Platform's revenue share (0.0 to 1.0)
    total_earnings: decimal.Decimal
    total_sales: int
    rating: float
    created_at: datetime
    verified_at: Optional[datetime]

@dataclass
class CreatorContent:
    content_id: str
    creator_id: str
    title: str
    description: str
    content_type: str
    category: str
    tags: List[str]
    monetization_model: MonetizationModel
    price: Optional[decimal.Decimal]
    subscription_price_monthly: Optional[decimal.Decimal]
    content_status: ContentStatus
    content_files: List[Dict[str, Any]]  # File metadata
    preview_content: Optional[str]
    duration_minutes: Optional[int]
    difficulty_level: str
    target_audience: str
    learning_objectives: List[str]
    prerequisites: List[str]
    view_count: int
    purchase_count: int
    rating: float
    rating_count: int
    revenue_generated: decimal.Decimal
    created_at: datetime
    published_at: Optional[datetime]
    updated_at: datetime

@dataclass
class CreatorCourse:
    course_id: str
    creator_id: str
    title: str
    description: str
    category: str
    total_modules: int
    total_duration_hours: float
    price: decimal.Decimal
    subscription_price: Optional[decimal.Decimal]
    enrollment_count: int
    completion_rate: float
    rating: float
    curriculum: List[Dict[str, Any]]
    course_status: ContentStatus
    preview_video_url: Optional[str]
    certificate_template: Optional[str]
    created_at: datetime
    launched_at: Optional[datetime]

@dataclass
class CreatorEarnings:
    earning_id: str
    creator_id: str
    content_id: Optional[str]
    course_id: Optional[str]
    user_id: str  # Purchaser
    transaction_type: str  # purchase, subscription, tip
    gross_amount: decimal.Decimal
    platform_fee: decimal.Decimal
    creator_amount: decimal.Decimal
    payment_status: PaymentStatus
    payment_processor: str  # stripe, paypal, etc.
    payment_reference: str
    created_at: datetime
    paid_out_at: Optional[datetime]

@dataclass
class CreatorAnalytics:
    creator_id: str
    date: datetime
    content_views: int
    new_followers: int
    revenue: decimal.Decimal
    course_enrollments: int
    completion_rate: float
    rating_average: float
    engagement_score: float
    top_content: List[str]
    demographic_data: Dict[str, Any]

@dataclass
class SubscriptionPlan:
    plan_id: str
    creator_id: str
    plan_name: str
    description: str
    price_monthly: decimal.Decimal
    price_yearly: Optional[decimal.Decimal]
    features: List[str]
    max_content_access: Optional[int]
    subscriber_count: int
    is_active: bool
    created_at: datetime

class CreatorPortalManager:
    """Manages creator portal, monetization, and marketplace features"""
    
    def __init__(self, db_manager=None, payment_processor=None):
        self.db = db_manager
        self.payment_processor = payment_processor
        
        # Platform revenue share configuration
        self.default_revenue_share = 0.15  # Platform takes 15%
        self.featured_creator_share = 0.10  # Featured creators pay 10%
        self.minimum_payout_threshold = decimal.Decimal('50.00')  # $50 minimum payout
        
        # Content review settings
        self.auto_approve_verified_creators = True
        self.review_queue_max_days = 7
        
        logger.info("Creator Portal Manager initialized")
    
    def create_creator_profile(self, user_id: str, business_name: str, 
                             specializations: List[str], bio: str,
                             website: Optional[str] = None) -> Optional[str]:
        """Create a new creator profile"""
        try:
            if not self.db:
                return None
            
            creator_id = str(uuid.uuid4())
            
            creator = CreatorProfile(
                creator_id=creator_id,
                user_id=user_id,
                business_name=business_name,
                creator_status=CreatorStatus.PENDING,
                specializations=specializations,
                bio=bio,
                website=website,
                social_links={},
                verification_documents=[],
                tax_info={},
                bank_info={},
                revenue_share=self.default_revenue_share,
                total_earnings=decimal.Decimal('0.00'),
                total_sales=0,
                rating=0.0,
                created_at=datetime.now(),
                verified_at=None
            )
            
            # Store creator profile
            query = """
                INSERT INTO creator_profiles
                (creator_id, user_id, business_name, creator_status, specializations,
                 bio, website, social_links, verification_documents, tax_info,
                 bank_info, revenue_share, total_earnings, total_sales, rating,
                 created_at, verified_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            self.db.execute_query(query, (
                creator.creator_id, creator.user_id, creator.business_name,
                creator.creator_status.value, json.dumps(creator.specializations),
                creator.bio, creator.website, json.dumps(creator.social_links),
                json.dumps(creator.verification_documents), json.dumps(creator.tax_info),
                json.dumps(creator.bank_info), float(creator.revenue_share),
                float(creator.total_earnings), creator.total_sales, creator.rating,
                creator.created_at, creator.verified_at
            ))
            
            logger.info(f"Creator profile created: {creator_id} for user {user_id}")
            return creator_id
            
        except Exception as e:
            logger.error(f"Error creating creator profile: {e}")
            return None
    
    def create_content(self, creator_id: str, title: str, description: str,
                      content_type: str, category: str, monetization_model: MonetizationModel,
                      price: Optional[decimal.Decimal] = None, 
                      subscription_price_monthly: Optional[decimal.Decimal] = None) -> Optional[str]:
        """Create new content for monetization"""
        try:
            if not self.db:
                return None
            
            content_id = str(uuid.uuid4())
            
            content = CreatorContent(
                content_id=content_id,
                creator_id=creator_id,
                title=title,
                description=description,
                content_type=content_type,
                category=category,
                tags=self._generate_content_tags(category, content_type),
                monetization_model=monetization_model,
                price=price,
                subscription_price_monthly=subscription_price_monthly,
                content_status=ContentStatus.DRAFT,
                content_files=[],
                preview_content=None,
                duration_minutes=None,
                difficulty_level="beginner",
                target_audience="general",
                learning_objectives=[],
                prerequisites=[],
                view_count=0,
                purchase_count=0,
                rating=0.0,
                rating_count=0,
                revenue_generated=decimal.Decimal('0.00'),
                created_at=datetime.now(),
                published_at=None,
                updated_at=datetime.now()
            )
            
            # Store content
            query = """
                INSERT INTO creator_content
                (content_id, creator_id, title, description, content_type, category,
                 tags, monetization_model, price, subscription_price_monthly,
                 content_status, content_files, preview_content, duration_minutes,
                 difficulty_level, target_audience, learning_objectives, prerequisites,
                 view_count, purchase_count, rating, rating_count, revenue_generated,
                 created_at, published_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            self.db.execute_query(query, (
                content.content_id, content.creator_id, content.title, content.description,
                content.content_type, content.category, json.dumps(content.tags),
                content.monetization_model.value, float(content.price) if content.price else None,
                float(content.subscription_price_monthly) if content.subscription_price_monthly else None,
                content.content_status.value, json.dumps(content.content_files),
                content.preview_content, content.duration_minutes, content.difficulty_level,
                content.target_audience, json.dumps(content.learning_objectives),
                json.dumps(content.prerequisites), content.view_count, content.purchase_count,
                content.rating, content.rating_count, float(content.revenue_generated),
                content.created_at, content.published_at, content.updated_at
            ))
            
            logger.info(f"Creator content created: {content_id} by {creator_id}")
            return content_id
            
        except Exception as e:
            logger.error(f"Error creating creator content: {e}")
            return None
    
    def submit_content_for_review(self, content_id: str, creator_id: str) -> bool:
        """Submit content for platform review"""
        try:
            if not self.db:
                return False
            
            # Check if creator owns this content
            ownership_query = "SELECT creator_id FROM creator_content WHERE content_id = ?"
            result = self.db.fetch_one(ownership_query, (content_id,))
            
            if not result or result[0] != creator_id:
                logger.warning(f"Creator {creator_id} doesn't own content {content_id}")
                return False
            
            # Check if creator is verified for auto-approval
            creator_query = "SELECT creator_status FROM creator_profiles WHERE creator_id = ?"
            creator_result = self.db.fetch_one(creator_query, (creator_id,))
            
            auto_approve = (self.auto_approve_verified_creators and 
                          creator_result and creator_result[0] == CreatorStatus.VERIFIED.value)
            
            new_status = ContentStatus.APPROVED if auto_approve else ContentStatus.PENDING_REVIEW
            published_at = datetime.now() if auto_approve else None
            
            # Update content status
            update_query = """
                UPDATE creator_content 
                SET content_status = ?, published_at = ?, updated_at = ?
                WHERE content_id = ?
            """
            
            self.db.execute_query(update_query, (
                new_status.value, published_at, datetime.now(), content_id
            ))
            
            if auto_approve:
                logger.info(f"Content {content_id} auto-approved for verified creator {creator_id}")
            else:
                logger.info(f"Content {content_id} submitted for review by {creator_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error submitting content for review: {e}")
            return False
    
    def process_content_purchase(self, content_id: str, buyer_user_id: str, 
                               payment_method: str) -> Dict[str, Any]:
        """Process a content purchase"""
        try:
            if not self.db:
                return {'success': False, 'error': 'Database unavailable'}
            
            # Get content details
            content_query = """
                SELECT cc.creator_id, cc.title, cc.price, cc.monetization_model,
                       cp.revenue_share
                FROM creator_content cc
                JOIN creator_profiles cp ON cc.creator_id = cp.creator_id
                WHERE cc.content_id = ? AND cc.content_status = 'published'
            """
            
            content_result = self.db.fetch_one(content_query, (content_id,))
            
            if not content_result:
                return {'success': False, 'error': 'Content not found or not available'}
            
            creator_id, title, price, monetization_model, revenue_share = content_result
            
            if monetization_model == MonetizationModel.FREE.value:
                # Free content - just record access
                self._record_content_access(content_id, buyer_user_id, free=True)
                return {
                    'success': True,
                    'message': 'Free content access granted',
                    'access_granted': True
                }
            
            if not price or price <= 0:
                return {'success': False, 'error': 'Invalid content price'}
            
            # Process payment (mock implementation)
            payment_result = self._process_payment(
                amount=decimal.Decimal(str(price)),
                buyer_id=buyer_user_id,
                payment_method=payment_method,
                description=f"Purchase: {title}"
            )
            
            if not payment_result['success']:
                return {'success': False, 'error': payment_result['error']}
            
            # Calculate earnings
            gross_amount = decimal.Decimal(str(price))
            platform_fee = gross_amount * decimal.Decimal(str(revenue_share))
            creator_amount = gross_amount - platform_fee
            
            # Record earnings
            earning_id = str(uuid.uuid4())
            earnings_query = """
                INSERT INTO creator_earnings
                (earning_id, creator_id, content_id, user_id, transaction_type,
                 gross_amount, platform_fee, creator_amount, payment_status,
                 payment_processor, payment_reference, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            self.db.execute_query(earnings_query, (
                earning_id, creator_id, content_id, buyer_user_id, 'purchase',
                float(gross_amount), float(platform_fee), float(creator_amount),
                PaymentStatus.COMPLETED.value, 'mock_processor',
                payment_result['payment_reference'], datetime.now()
            ))
            
            # Update content stats
            self.db.execute_query("""
                UPDATE creator_content 
                SET purchase_count = purchase_count + 1,
                    revenue_generated = revenue_generated + ?
                WHERE content_id = ?
            """, (float(gross_amount), content_id))
            
            # Update creator earnings
            self.db.execute_query("""
                UPDATE creator_profiles 
                SET total_earnings = total_earnings + ?,
                    total_sales = total_sales + 1
                WHERE creator_id = ?
            """, (float(creator_amount), creator_id))
            
            # Grant content access
            self._record_content_access(content_id, buyer_user_id, free=False)
            
            logger.info(f"Content purchase processed: {content_id} by {buyer_user_id}")
            
            return {
                'success': True,
                'message': 'Purchase completed successfully',
                'earning_id': earning_id,
                'amount_paid': float(gross_amount),
                'access_granted': True
            }
            
        except Exception as e:
            logger.error(f"Error processing content purchase: {e}")
            return {'success': False, 'error': 'Purchase processing failed'}
    
    def get_creator_analytics(self, creator_id: str, days: int = 30) -> Dict[str, Any]:
        """Get comprehensive analytics for a creator"""
        try:
            if not self.db:
                return {}
            
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # Revenue analytics
            revenue_query = """
                SELECT 
                    COUNT(*) as total_transactions,
                    SUM(gross_amount) as total_revenue,
                    SUM(creator_amount) as creator_earnings,
                    AVG(gross_amount) as avg_transaction_value
                FROM creator_earnings 
                WHERE creator_id = ? AND created_at >= ? AND payment_status = 'completed'
            """
            
            revenue_data = self.db.fetch_one(revenue_query, (creator_id, start_date))
            
            # Content performance
            content_query = """
                SELECT 
                    COUNT(*) as total_content,
                    SUM(view_count) as total_views,
                    SUM(purchase_count) as total_purchases,
                    AVG(rating) as avg_rating
                FROM creator_content 
                WHERE creator_id = ? AND content_status = 'published'
            """
            
            content_data = self.db.fetch_one(content_query, (creator_id,))
            
            # Top performing content
            top_content_query = """
                SELECT content_id, title, view_count, purchase_count, revenue_generated
                FROM creator_content 
                WHERE creator_id = ? AND content_status = 'published'
                ORDER BY revenue_generated DESC 
                LIMIT 5
            """
            
            top_content = self.db.fetch_all(top_content_query, (creator_id,))
            
            # Recent earnings trend
            daily_earnings_query = """
                SELECT 
                    DATE(created_at) as date,
                    SUM(creator_amount) as daily_earnings,
                    COUNT(*) as daily_transactions
                FROM creator_earnings 
                WHERE creator_id = ? AND created_at >= ? AND payment_status = 'completed'
                GROUP BY DATE(created_at)
                ORDER BY date DESC
            """
            
            daily_earnings = self.db.fetch_all(daily_earnings_query, (creator_id, start_date))
            
            analytics = {
                'period_days': days,
                'revenue': {
                    'total_transactions': revenue_data[0] if revenue_data else 0,
                    'total_revenue': float(revenue_data[1]) if revenue_data and revenue_data[1] else 0.0,
                    'creator_earnings': float(revenue_data[2]) if revenue_data and revenue_data[2] else 0.0,
                    'avg_transaction': float(revenue_data[3]) if revenue_data and revenue_data[3] else 0.0
                },
                'content': {
                    'total_content': content_data[0] if content_data else 0,
                    'total_views': content_data[1] if content_data else 0,
                    'total_purchases': content_data[2] if content_data else 0,
                    'avg_rating': float(content_data[3]) if content_data and content_data[3] else 0.0
                },
                'top_content': [
                    {
                        'content_id': row[0],
                        'title': row[1],
                        'views': row[2],
                        'purchases': row[3],
                        'revenue': float(row[4])
                    } for row in top_content
                ],
                'daily_trend': [
                    {
                        'date': row[0],
                        'earnings': float(row[1]),
                        'transactions': row[2]
                    } for row in daily_earnings
                ]
            }
            
            return analytics
            
        except Exception as e:
            logger.error(f"Error getting creator analytics: {e}")
            return {}
    
    def get_marketplace_content(self, category: Optional[str] = None, 
                               monetization_model: Optional[MonetizationModel] = None,
                               min_price: Optional[decimal.Decimal] = None,
                               max_price: Optional[decimal.Decimal] = None,
                               limit: int = 20) -> List[Dict[str, Any]]:
        """Get content for marketplace discovery"""
        try:
            if not self.db:
                return []
            
            query = """
                SELECT cc.*, cp.business_name, cp.rating as creator_rating
                FROM creator_content cc
                JOIN creator_profiles cp ON cc.creator_id = cp.creator_id
                WHERE cc.content_status = 'published'
            """
            
            params = []
            
            if category:
                query += " AND cc.category = ?"
                params.append(category)
            
            if monetization_model:
                query += " AND cc.monetization_model = ?"
                params.append(monetization_model.value)
            
            if min_price is not None:
                query += " AND cc.price >= ?"
                params.append(float(min_price))
            
            if max_price is not None:
                query += " AND cc.price <= ?"
                params.append(float(max_price))
            
            query += " ORDER BY cc.rating DESC, cc.view_count DESC LIMIT ?"
            params.append(limit)
            
            results = self.db.fetch_all(query, tuple(params))
            
            marketplace_content = []
            for row in results:
                content_data = {
                    'content_id': row[0],
                    'creator_id': row[1],
                    'title': row[2],
                    'description': row[3],
                    'content_type': row[4],
                    'category': row[5],
                    'tags': json.loads(row[6]) if row[6] else [],
                    'monetization_model': row[7],
                    'price': float(row[8]) if row[8] else 0.0,
                    'subscription_price_monthly': float(row[9]) if row[9] else None,
                    'duration_minutes': row[13],
                    'difficulty_level': row[14],
                    'view_count': row[18],
                    'purchase_count': row[19],
                    'rating': row[20],
                    'rating_count': row[21],
                    'published_at': row[24],
                    'creator_name': row[26],
                    'creator_rating': row[27]
                }
                marketplace_content.append(content_data)
            
            return marketplace_content
            
        except Exception as e:
            logger.error(f"Error getting marketplace content: {e}")
            return []
    
    def _process_payment(self, amount: decimal.Decimal, buyer_id: str, 
                        payment_method: str, description: str) -> Dict[str, Any]:
        """Process payment (mock implementation)"""
        try:
            # Mock payment processing
            # In production, integrate with Stripe, PayPal, etc.
            
            payment_reference = f"pay_{uuid.uuid4().hex[:16]}"
            
            # Simulate payment processing
            import random
            success = random.random() > 0.05  # 95% success rate
            
            if success:
                return {
                    'success': True,
                    'payment_reference': payment_reference,
                    'amount': float(amount),
                    'status': 'completed'
                }
            else:
                return {
                    'success': False,
                    'error': 'Payment processing failed',
                    'payment_reference': payment_reference
                }
            
        except Exception as e:
            logger.error(f"Error processing payment: {e}")
            return {'success': False, 'error': 'Payment system error'}
    
    def _record_content_access(self, content_id: str, user_id: str, free: bool = False):
        """Record user access to content"""
        try:
            if not self.db:
                return
            
            access_id = str(uuid.uuid4())
            query = """
                INSERT OR REPLACE INTO content_access
                (access_id, content_id, user_id, access_type, granted_at, expires_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """
            
            access_type = 'free' if free else 'purchased'
            granted_at = datetime.now()
            expires_at = None  # Permanent access for purchases
            
            self.db.execute_query(query, (
                access_id, content_id, user_id, access_type, granted_at, expires_at
            ))
            
            logger.info(f"Content access recorded: {content_id} for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error recording content access: {e}")
    
    def _generate_content_tags(self, category: str, content_type: str) -> List[str]:
        """Generate relevant tags for content"""
        category_tags = {
            'anxiety_management': ['anxiety', 'calm', 'breathing', 'relaxation'],
            'meditation': ['mindfulness', 'present', 'awareness', 'peace'],
            'fitness': ['exercise', 'movement', 'strength', 'cardio'],
            'nutrition': ['healthy', 'diet', 'wellness', 'balance'],
            'sleep': ['rest', 'bedtime', 'insomnia', 'recovery']
        }
        
        type_tags = {
            'guided_meditation': ['guided', 'meditation', 'practice'],
            'article': ['education', 'tips', 'guide', 'information'],
            'video': ['visual', 'demonstration', 'tutorial'],
            'audio': ['listening', 'audio', 'voice'],
            'course': ['learning', 'structured', 'comprehensive']
        }
        
        tags = category_tags.get(category, []) + type_tags.get(content_type, [])
        return list(set(tags))  # Remove duplicates

# Database initialization
def init_creator_portal_database(db_connection):
    """Initialize creator portal database tables"""
    try:
        # Creator profiles table
        db_connection.execute('''
            CREATE TABLE IF NOT EXISTS creator_profiles (
                creator_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL UNIQUE,
                business_name TEXT NOT NULL,
                creator_status TEXT NOT NULL,
                specializations TEXT NOT NULL,
                bio TEXT NOT NULL,
                website TEXT,
                social_links TEXT,
                verification_documents TEXT,
                tax_info TEXT,
                bank_info TEXT,
                revenue_share REAL NOT NULL,
                total_earnings REAL DEFAULT 0.0,
                total_sales INTEGER DEFAULT 0,
                rating REAL DEFAULT 0.0,
                created_at DATETIME NOT NULL,
                verified_at DATETIME,
                INDEX(user_id),
                INDEX(creator_status),
                INDEX(created_at)
            )
        ''')
        
        # Creator content table
        db_connection.execute('''
            CREATE TABLE IF NOT EXISTS creator_content (
                content_id TEXT PRIMARY KEY,
                creator_id TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                content_type TEXT NOT NULL,
                category TEXT NOT NULL,
                tags TEXT,
                monetization_model TEXT NOT NULL,
                price REAL,
                subscription_price_monthly REAL,
                content_status TEXT NOT NULL,
                content_files TEXT,
                preview_content TEXT,
                duration_minutes INTEGER,
                difficulty_level TEXT NOT NULL,
                target_audience TEXT NOT NULL,
                learning_objectives TEXT,
                prerequisites TEXT,
                view_count INTEGER DEFAULT 0,
                purchase_count INTEGER DEFAULT 0,
                rating REAL DEFAULT 0.0,
                rating_count INTEGER DEFAULT 0,
                revenue_generated REAL DEFAULT 0.0,
                created_at DATETIME NOT NULL,
                published_at DATETIME,
                updated_at DATETIME NOT NULL,
                INDEX(creator_id),
                INDEX(content_status),
                INDEX(category),
                INDEX(monetization_model),
                INDEX(published_at)
            )
        ''')
        
        # Creator earnings table
        db_connection.execute('''
            CREATE TABLE IF NOT EXISTS creator_earnings (
                earning_id TEXT PRIMARY KEY,
                creator_id TEXT NOT NULL,
                content_id TEXT,
                course_id TEXT,
                user_id TEXT NOT NULL,
                transaction_type TEXT NOT NULL,
                gross_amount REAL NOT NULL,
                platform_fee REAL NOT NULL,
                creator_amount REAL NOT NULL,
                payment_status TEXT NOT NULL,
                payment_processor TEXT NOT NULL,
                payment_reference TEXT NOT NULL,
                created_at DATETIME NOT NULL,
                paid_out_at DATETIME,
                INDEX(creator_id),
                INDEX(payment_status),
                INDEX(created_at),
                INDEX(user_id)
            )
        ''')
        
        # Creator courses table
        db_connection.execute('''
            CREATE TABLE IF NOT EXISTS creator_courses (
                course_id TEXT PRIMARY KEY,
                creator_id TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                category TEXT NOT NULL,
                total_modules INTEGER NOT NULL,
                total_duration_hours REAL NOT NULL,
                price REAL NOT NULL,
                subscription_price REAL,
                enrollment_count INTEGER DEFAULT 0,
                completion_rate REAL DEFAULT 0.0,
                rating REAL DEFAULT 0.0,
                curriculum TEXT NOT NULL,
                course_status TEXT NOT NULL,
                preview_video_url TEXT,
                certificate_template TEXT,
                created_at DATETIME NOT NULL,
                launched_at DATETIME,
                INDEX(creator_id),
                INDEX(category),
                INDEX(course_status),
                INDEX(created_at)
            )
        ''')
        
        # Content access table
        db_connection.execute('''
            CREATE TABLE IF NOT EXISTS content_access (
                access_id TEXT PRIMARY KEY,
                content_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                access_type TEXT NOT NULL,
                granted_at DATETIME NOT NULL,
                expires_at DATETIME,
                INDEX(content_id),
                INDEX(user_id),
                UNIQUE(content_id, user_id)
            )
        ''')
        
        # Subscription plans table
        db_connection.execute('''
            CREATE TABLE IF NOT EXISTS subscription_plans (
                plan_id TEXT PRIMARY KEY,
                creator_id TEXT NOT NULL,
                plan_name TEXT NOT NULL,
                description TEXT NOT NULL,
                price_monthly REAL NOT NULL,
                price_yearly REAL,
                features TEXT NOT NULL,
                max_content_access INTEGER,
                subscriber_count INTEGER DEFAULT 0,
                is_active BOOLEAN DEFAULT 1,
                created_at DATETIME NOT NULL,
                INDEX(creator_id),
                INDEX(is_active)
            )
        ''')
        
        db_connection.commit()
        logger.info("Creator portal database tables initialized")
        
    except Exception as e:
        logger.error(f"Error initializing creator portal database: {e}")

# Global instance
creator_portal_manager = None

def init_creator_portal_manager(db_manager=None, payment_processor=None):
    """Initialize creator portal manager"""
    global creator_portal_manager
    try:
        creator_portal_manager = CreatorPortalManager(db_manager, payment_processor)
        logger.info("Creator portal manager initialized successfully")
        return creator_portal_manager
    except Exception as e:
        logger.error(f"Error initializing creator portal manager: {e}")
        return None

def get_creator_portal_manager():
    """Get creator portal manager instance"""
    return creator_portal_manager