"""
Advanced AI-Powered Customer Support Chatbot
Handles user inquiries, provides instant responses, and escalates complex issues
"""
import openai
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import re

logger = logging.getLogger(__name__)

class Priority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class TicketStatus(Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"

@dataclass
class SupportTicket:
    id: str
    user_id: str
    subject: str
    description: str
    category: str
    priority: Priority
    status: TicketStatus
    created_at: datetime
    updated_at: datetime
    assigned_agent: Optional[str] = None
    resolution: Optional[str] = None
    satisfaction_rating: Optional[int] = None

@dataclass
class ChatMessage:
    id: str
    conversation_id: str
    sender: str  # 'user' or 'bot'
    message: str
    timestamp: datetime
    intent: Optional[str] = None
    confidence: Optional[float] = None

class SupportChatbot:
    def __init__(self, openai_client, db_manager, notification_manager):
        self.openai_client = openai_client
        self.db = db_manager
        self.notification_manager = notification_manager
        
        # Knowledge base for common questions
        self.knowledge_base = {
            'account': {
                'login_issues': {
                    'keywords': ['login', 'password', 'access', 'sign in', 'authentication'],
                    'response': "I can help with login issues. Please try resetting your password using the 'Forgot Password' link. If you're still having trouble, I can escalate this to our technical team."
                },
                'profile_setup': {
                    'keywords': ['profile', 'setup', 'account creation', 'registration'],
                    'response': "Setting up your profile is easy! Go to Settings > Profile and complete the required fields. Need help with a specific step?"
                }
            },
            'billing': {
                'payment_issues': {
                    'keywords': ['payment', 'billing', 'charge', 'card', 'subscription'],
                    'response': "I can help with billing questions. Can you describe the specific issue? I can check your payment history or help update payment methods."
                },
                'subscription': {
                    'keywords': ['subscription', 'plan', 'upgrade', 'downgrade', 'cancel'],
                    'response': "For subscription changes, you can manage your plan in Settings > Billing. Would you like me to guide you through the process?"
                }
            },
            'technical': {
                'app_performance': {
                    'keywords': ['slow', 'performance', 'lag', 'crash', 'error'],
                    'response': "Sorry to hear about performance issues. Try clearing your browser cache or refreshing the page. If problems persist, I'll create a technical support ticket."
                },
                'features': {
                    'keywords': ['feature', 'how to', 'tutorial', 'guide'],
                    'response': "I'd be happy to explain our features! What specific functionality would you like to learn about?"
                }
            }
        }
        
        # Escalation triggers
        self.escalation_keywords = [
            'angry', 'frustrated', 'terrible', 'awful', 'complaint',
            'manager', 'supervisor', 'legal', 'lawsuit', 'refund',
            'cancel account', 'delete account', 'privacy violation'
        ]
        
        self.conversation_context = {}  # Store conversation history
        
    def process_message(self, user_id: str, message: str, conversation_id: str = None) -> Dict:
        """Process incoming user message and generate appropriate response"""
        try:
            # Create new conversation if needed
            if not conversation_id:
                conversation_id = f"conv_{user_id}_{datetime.now().timestamp()}"
            
            # Store user message
            user_message = ChatMessage(
                id=f"msg_{datetime.now().timestamp()}",
                conversation_id=conversation_id,
                sender='user',
                message=message,
                timestamp=datetime.now()
            )
            
            # Analyze intent and sentiment
            intent_analysis = self._analyze_intent(message)
            sentiment = self._analyze_sentiment(message)
            
            # Check for escalation triggers
            needs_escalation = self._check_escalation_needed(message, sentiment)
            
            if needs_escalation:
                return self._escalate_to_human(user_id, message, conversation_id, intent_analysis)
            
            # Generate AI response
            bot_response = self._generate_response(user_id, message, intent_analysis, conversation_id)
            
            # Store bot message
            bot_message = ChatMessage(
                id=f"msg_{datetime.now().timestamp()}_bot",
                conversation_id=conversation_id,
                sender='bot',
                message=bot_response['message'],
                timestamp=datetime.now(),
                intent=intent_analysis['intent'],
                confidence=intent_analysis['confidence']
            )
            
            # Store conversation in database
            self._store_conversation([user_message, bot_message])
            
            return {
                'success': True,
                'conversation_id': conversation_id,
                'response': bot_response['message'],
                'intent': intent_analysis['intent'],
                'confidence': intent_analysis['confidence'],
                'escalated': False,
                'suggested_actions': bot_response.get('actions', [])
            }
            
        except Exception as e:
            logger.error(f"Error processing support message: {e}")
            return {
                'success': False,
                'error': 'Unable to process your message. Please try again.',
                'escalated': True
            }
    
    def _analyze_intent(self, message: str) -> Dict:
        """Analyze user intent using keyword matching and AI"""
        message_lower = message.lower()
        
        # Check knowledge base for intent matching
        for category, subcategories in self.knowledge_base.items():
            for intent, data in subcategories.items():
                for keyword in data['keywords']:
                    if keyword in message_lower:
                        return {
                            'intent': f"{category}_{intent}",
                            'category': category,
                            'confidence': 0.8
                        }
        
        # Use AI for complex intent analysis
        try:
            prompt = f"""
            Analyze the intent of this customer support message and categorize it:
            Message: "{message}"
            
            Categories: account, billing, technical, general_inquiry, complaint
            
            Respond with JSON format:
            {{"intent": "category_name", "confidence": 0.0-1.0, "sentiment": "positive/neutral/negative"}}
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=100,
                temperature=0.3
            )
            
            result = json.loads(response.choices[0].message.content)
            return result
            
        except Exception as e:
            logger.error(f"AI intent analysis failed: {e}")
            return {'intent': 'general_inquiry', 'confidence': 0.5, 'sentiment': 'neutral'}
    
    def _analyze_sentiment(self, message: str) -> str:
        """Analyze message sentiment"""
        negative_indicators = ['angry', 'frustrated', 'terrible', 'awful', 'hate', 'worst']
        positive_indicators = ['great', 'good', 'excellent', 'love', 'amazing', 'perfect']
        
        message_lower = message.lower()
        
        negative_count = sum(1 for word in negative_indicators if word in message_lower)
        positive_count = sum(1 for word in positive_indicators if word in message_lower)
        
        if negative_count > positive_count:
            return 'negative'
        elif positive_count > negative_count:
            return 'positive'
        else:
            return 'neutral'
    
    def _check_escalation_needed(self, message: str, sentiment: str) -> bool:
        """Check if conversation should be escalated to human agent"""
        message_lower = message.lower()
        
        # Check for escalation keywords
        for keyword in self.escalation_keywords:
            if keyword in message_lower:
                return True
        
        # Escalate if very negative sentiment
        if sentiment == 'negative' and any(word in message_lower for word in ['terrible', 'awful', 'worst']):
            return True
        
        return False
    
    def _generate_response(self, user_id: str, message: str, intent_analysis: Dict, conversation_id: str) -> Dict:
        """Generate contextual response using AI and knowledge base"""
        
        # Check knowledge base first
        intent = intent_analysis.get('intent', '')
        for category, subcategories in self.knowledge_base.items():
            for sub_intent, data in subcategories.items():
                if f"{category}_{sub_intent}" == intent:
                    return {
                        'message': data['response'],
                        'actions': self._get_suggested_actions(category, sub_intent)
                    }
        
        # Use AI for complex responses
        try:
            conversation_history = self._get_conversation_history(conversation_id)
            
            prompt = f"""
            You are a helpful customer support chatbot for SoulBridge AI. 
            Provide a helpful, empathetic response to this customer inquiry.
            
            User message: "{message}"
            Intent: {intent_analysis.get('intent', 'general')}
            Conversation history: {conversation_history[-3:] if conversation_history else 'None'}
            
            Guidelines:
            - Be friendly and professional
            - Provide specific, actionable help
            - If you can't solve the issue, offer to escalate
            - Keep responses concise but helpful
            - Use the user's name if available
            
            Respond with only the support message, no additional formatting.
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
                temperature=0.7
            )
            
            return {
                'message': response.choices[0].message.content.strip(),
                'actions': []
            }
            
        except Exception as e:
            logger.error(f"AI response generation failed: {e}")
            return {
                'message': "I'm here to help! Could you please provide more details about your issue so I can assist you better?",
                'actions': []
            }
    
    def _escalate_to_human(self, user_id: str, message: str, conversation_id: str, intent_analysis: Dict) -> Dict:
        """Escalate conversation to human agent"""
        try:
            # Create support ticket
            ticket_id = f"ticket_{datetime.now().timestamp()}"
            
            ticket = SupportTicket(
                id=ticket_id,
                user_id=user_id,
                subject=f"Escalated chat: {intent_analysis.get('intent', 'Support Request')}",
                description=f"Original message: {message}\nEscalated from chatbot conversation: {conversation_id}",
                category=intent_analysis.get('category', 'general'),
                priority=Priority.HIGH,
                status=TicketStatus.OPEN,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            # Store ticket in database
            self._create_support_ticket(ticket)
            
            # Notify support team
            self.notification_manager.send_notification(
                user_id="support_team",
                title="New Escalated Support Ticket",
                message=f"Ticket {ticket_id} requires immediate attention",
                notification_type="support_escalation",
                priority="high"
            )
            
            return {
                'success': True,
                'conversation_id': conversation_id,
                'response': f"I've escalated your inquiry to our support team. Ticket #{ticket_id} has been created and you'll hear from us within 2 hours. Is there anything else I can help with in the meantime?",
                'escalated': True,
                'ticket_id': ticket_id
            }
            
        except Exception as e:
            logger.error(f"Error escalating to human: {e}")
            return {
                'success': False,
                'response': "I'm unable to escalate right now. Please email support@soulbridge.ai for immediate assistance.",
                'escalated': True
            }
    
    def _get_suggested_actions(self, category: str, intent: str) -> List[str]:
        """Get suggested actions based on category and intent"""
        actions = {
            'account': {
                'login_issues': ['Reset Password', 'Check Account Status', 'Contact Support'],
                'profile_setup': ['View Tutorial', 'Complete Profile', 'Skip for Now']
            },
            'billing': {
                'payment_issues': ['View Billing History', 'Update Payment Method', 'Contact Billing'],
                'subscription': ['Manage Subscription', 'View Plans', 'Cancel Subscription']
            },
            'technical': {
                'app_performance': ['Clear Cache', 'Restart App', 'Report Bug'],
                'features': ['View Help Center', 'Watch Tutorial', 'Schedule Demo']
            }
        }
        
        return actions.get(category, {}).get(intent, [])
    
    def _store_conversation(self, messages: List[ChatMessage]):
        """Store conversation messages in database"""
        try:
            if not self.db:
                return
            
            for message in messages:
                query = """
                INSERT INTO support_conversations 
                (id, conversation_id, sender, message, timestamp, intent, confidence)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """
                self.db.execute_query(query, (
                    message.id, message.conversation_id, message.sender,
                    message.message, message.timestamp, message.intent, message.confidence
                ))
        except Exception as e:
            logger.error(f"Error storing conversation: {e}")
    
    def _get_conversation_history(self, conversation_id: str) -> List[Dict]:
        """Retrieve conversation history"""
        try:
            if not self.db:
                return []
            
            query = """
            SELECT sender, message, timestamp FROM support_conversations 
            WHERE conversation_id = ? ORDER BY timestamp ASC
            """
            results = self.db.fetch_all(query, (conversation_id,))
            return [{'sender': r[0], 'message': r[1], 'timestamp': r[2]} for r in results]
        except Exception as e:
            logger.error(f"Error getting conversation history: {e}")
            return []
    
    def _create_support_ticket(self, ticket: SupportTicket):
        """Store support ticket in database"""
        try:
            if not self.db:
                return
            
            query = """
            INSERT INTO support_tickets 
            (id, user_id, subject, description, category, priority, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            self.db.execute_query(query, (
                ticket.id, ticket.user_id, ticket.subject, ticket.description,
                ticket.category, ticket.priority.value, ticket.status.value,
                ticket.created_at, ticket.updated_at
            ))
        except Exception as e:
            logger.error(f"Error creating support ticket: {e}")
    
    def get_ticket_status(self, ticket_id: str) -> Optional[Dict]:
        """Get support ticket status"""
        try:
            if not self.db:
                return None
            
            query = """
            SELECT id, subject, status, priority, created_at, updated_at, resolution
            FROM support_tickets WHERE id = ?
            """
            result = self.db.fetch_one(query, (ticket_id,))
            
            if result:
                return {
                    'id': result[0],
                    'subject': result[1],
                    'status': result[2],
                    'priority': result[3],
                    'created_at': result[4],
                    'updated_at': result[5],
                    'resolution': result[6]
                }
            return None
        except Exception as e:
            logger.error(f"Error getting ticket status: {e}")
            return None
    
    def update_ticket_satisfaction(self, ticket_id: str, rating: int, feedback: str = None):
        """Update ticket satisfaction rating"""
        try:
            if not self.db:
                return
            
            query = """
            UPDATE support_tickets 
            SET satisfaction_rating = ?, updated_at = ?
            WHERE id = ?
            """
            self.db.execute_query(query, (rating, datetime.now(), ticket_id))
            
            if feedback:
                # Store feedback separately
                feedback_query = """
                INSERT INTO support_feedback (ticket_id, rating, feedback, created_at)
                VALUES (?, ?, ?, ?)
                """
                self.db.execute_query(feedback_query, (ticket_id, rating, feedback, datetime.now()))
                
        except Exception as e:
            logger.error(f"Error updating satisfaction: {e}")

def init_support_database(db_connection):
    """Initialize support chatbot database tables"""
    try:
        # Support conversations table
        db_connection.execute('''
            CREATE TABLE IF NOT EXISTS support_conversations (
                id TEXT PRIMARY KEY,
                conversation_id TEXT NOT NULL,
                sender TEXT NOT NULL,
                message TEXT NOT NULL,
                timestamp DATETIME NOT NULL,
                intent TEXT,
                confidence REAL,
                INDEX(conversation_id),
                INDEX(timestamp)
            )
        ''')
        
        # Support tickets table
        db_connection.execute('''
            CREATE TABLE IF NOT EXISTS support_tickets (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                subject TEXT NOT NULL,
                description TEXT NOT NULL,
                category TEXT NOT NULL,
                priority TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL,
                assigned_agent TEXT,
                resolution TEXT,
                satisfaction_rating INTEGER,
                INDEX(user_id),
                INDEX(status),
                INDEX(priority),
                INDEX(created_at)
            )
        ''')
        
        # Support feedback table
        db_connection.execute('''
            CREATE TABLE IF NOT EXISTS support_feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_id TEXT NOT NULL,
                rating INTEGER NOT NULL,
                feedback TEXT,
                created_at DATETIME NOT NULL,
                FOREIGN KEY (ticket_id) REFERENCES support_tickets (id),
                INDEX(ticket_id),
                INDEX(rating)
            )
        ''')
        
        db_connection.commit()
        logger.info("Support chatbot database tables initialized")
        
    except Exception as e:
        logger.error(f"Error initializing support database: {e}")

# Global instance
support_chatbot_instance = None

def init_support_chatbot(openai_client, db_manager, notification_manager):
    """Initialize support chatbot"""
    global support_chatbot_instance
    try:
        support_chatbot_instance = SupportChatbot(openai_client, db_manager, notification_manager)
        logger.info("Support chatbot initialized successfully")
        return support_chatbot_instance
    except Exception as e:
        logger.error(f"Error initializing support chatbot: {e}")
        return None

def get_support_chatbot():
    """Get support chatbot instance"""
    return support_chatbot_instance