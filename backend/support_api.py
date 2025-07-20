"""
Support API endpoints for the customer support chatbot system
"""
from flask import Blueprint, request, jsonify, session
from functools import wraps
import logging
from datetime import datetime
import json

logger = logging.getLogger(__name__)

def create_support_api(support_chatbot, rate_limiter, security_monitor):
    """Create support API blueprint"""
    
    support_api = Blueprint('support', __name__, url_prefix='/api/support')
    
    def require_auth(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                return jsonify({'error': 'Authentication required'}), 401
            return f(*args, **kwargs)
        return decorated_function
    
    @support_api.route('/chat', methods=['POST'])
    @require_auth
    def chat_with_support():
        """Send message to support chatbot"""
        try:
            data = request.get_json()
            
            if not data or 'message' not in data:
                return jsonify({'error': 'Message is required'}), 400
            
            user_id = session['user_id']
            message = data['message'].strip()
            conversation_id = data.get('conversation_id')
            
            if not message:
                return jsonify({'error': 'Message cannot be empty'}), 400
            
            # Rate limiting (if available)
            if rate_limiter and not rate_limiter.check_rate_limit(f"support_chat_{user_id}", max_requests=10, window=300):
                return jsonify({'error': 'Too many support messages. Please wait before sending more.'}), 429
            
            # Security monitoring (if available)
            if security_monitor:
                security_monitor.log_event(user_id, 'support_chat', {
                    'message_length': len(message),
                    'conversation_id': conversation_id
                })
            
            # Process message with chatbot
            if not support_chatbot:
                return jsonify({'error': 'Support system temporarily unavailable'}), 503
            
            response = support_chatbot.process_message(user_id, message, conversation_id)
            
            if not response['success']:
                logger.error(f"Support chatbot error for user {user_id}: {response.get('error')}")
                return jsonify({
                    'error': 'Unable to process your message',
                    'fallback_message': 'Please email support@soulbridge.ai for assistance'
                }), 500
            
            return jsonify({
                'success': True,
                'conversation_id': response['conversation_id'],
                'message': response['response'],
                'intent': response.get('intent'),
                'confidence': response.get('confidence'),
                'escalated': response.get('escalated', False),
                'suggested_actions': response.get('suggested_actions', []),
                'ticket_id': response.get('ticket_id')
            })
            
        except Exception as e:
            logger.error(f"Error in chat endpoint: {e}")
            return jsonify({'error': 'Internal server error'}), 500
    
    @support_api.route('/ticket/<ticket_id>', methods=['GET'])
    @require_auth
    def get_ticket_status(ticket_id):
        """Get support ticket status"""
        try:
            user_id = session['user_id']
            
            if not support_chatbot:
                return jsonify({'error': 'Support system temporarily unavailable'}), 503
            
            ticket = support_chatbot.get_ticket_status(ticket_id)
            
            if not ticket:
                return jsonify({'error': 'Ticket not found'}), 404
            
            # Security: Only allow users to view their own tickets (admin check would go here)
            return jsonify({
                'success': True,
                'ticket': ticket
            })
            
        except Exception as e:
            logger.error(f"Error getting ticket status: {e}")
            return jsonify({'error': 'Internal server error'}), 500
    
    @support_api.route('/ticket/<ticket_id>/feedback', methods=['POST'])
    @require_auth
    def submit_feedback(ticket_id):
        """Submit feedback for resolved ticket"""
        try:
            data = request.get_json()
            
            if not data or 'rating' not in data:
                return jsonify({'error': 'Rating is required'}), 400
            
            rating = data['rating']
            feedback = data.get('feedback', '')
            
            if not isinstance(rating, int) or rating < 1 or rating > 5:
                return jsonify({'error': 'Rating must be between 1 and 5'}), 400
            
            user_id = session['user_id']
            
            # Security monitoring (if available)
            if security_monitor:
                security_monitor.log_event(user_id, 'support_feedback', {
                    'ticket_id': ticket_id,
                    'rating': rating
                })
            
            if not support_chatbot:
                return jsonify({'error': 'Support system temporarily unavailable'}), 503
            
            support_chatbot.update_ticket_satisfaction(ticket_id, rating, feedback)
            
            return jsonify({
                'success': True,
                'message': 'Thank you for your feedback!'
            })
            
        except Exception as e:
            logger.error(f"Error submitting feedback: {e}")
            return jsonify({'error': 'Internal server error'}), 500
    
    @support_api.route('/conversation/<conversation_id>/history', methods=['GET'])
    @require_auth
    def get_conversation_history(conversation_id):
        """Get conversation history"""
        try:
            user_id = session['user_id']
            
            if not support_chatbot:
                return jsonify({'error': 'Support system temporarily unavailable'}), 503
            
            history = support_chatbot._get_conversation_history(conversation_id)
            
            return jsonify({
                'success': True,
                'conversation_id': conversation_id,
                'history': history
            })
            
        except Exception as e:
            logger.error(f"Error getting conversation history: {e}")
            return jsonify({'error': 'Internal server error'}), 500
    
    @support_api.route('/faq', methods=['GET'])
    def get_faq():
        """Get frequently asked questions"""
        try:
            faq_data = [
                {
                    'category': 'Account',
                    'questions': [
                        {
                            'question': 'How do I reset my password?',
                            'answer': 'Click on "Forgot Password" on the login page and follow the instructions sent to your email.'
                        },
                        {
                            'question': 'How do I update my profile?',
                            'answer': 'Go to Settings > Profile to update your personal information and preferences.'
                        }
                    ]
                },
                {
                    'category': 'Billing',
                    'questions': [
                        {
                            'question': 'How do I change my subscription plan?',
                            'answer': 'Visit Settings > Billing to view and modify your subscription plan.'
                        },
                        {
                            'question': 'When will I be charged?',
                            'answer': 'Billing occurs monthly on the date you first subscribed. You can view your next billing date in your account settings.'
                        }
                    ]
                },
                {
                    'category': 'Technical',
                    'questions': [
                        {
                            'question': 'The app is running slowly. What should I do?',
                            'answer': 'Try clearing your browser cache, refreshing the page, or using a different browser. Contact support if issues persist.'
                        },
                        {
                            'question': 'How do I report a bug?',
                            'answer': 'Use the chat support feature or email us at support@soulbridge.ai with a detailed description of the issue.'
                        }
                    ]
                }
            ]
            
            return jsonify({
                'success': True,
                'faq': faq_data
            })
            
        except Exception as e:
            logger.error(f"Error getting FAQ: {e}")
            return jsonify({'error': 'Internal server error'}), 500
    
    @support_api.route('/status', methods=['GET'])
    def support_status():
        """Get support system status"""
        try:
            status = {
                'chatbot_available': support_chatbot is not None,
                'average_response_time': '< 1 minute',
                'queue_length': 0,  # Would be dynamic in production
                'operating_hours': '24/7',
                'escalation_available': True
            }
            
            return jsonify({
                'success': True,
                'status': status
            })
            
        except Exception as e:
            logger.error(f"Error getting support status: {e}")
            return jsonify({'error': 'Internal server error'}), 500
    
    return support_api

def init_support_api(support_chatbot, rate_limiter, security_monitor):
    """Initialize and return support API blueprint"""
    try:
        api = create_support_api(support_chatbot, rate_limiter, security_monitor)
        logger.info("Support API initialized successfully")
        return api
    except Exception as e:
        logger.error(f"Error initializing support API: {e}")
        return None