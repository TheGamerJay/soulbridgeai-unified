"""
SoulBridge AI - Content Moderator
AI-powered content moderation for wellness gallery and community features
Extracted from backend/app.py with improvements
"""
import logging
from typing import Dict, Any, List
import re

logger = logging.getLogger(__name__)

class ContentModerator:
    """AI-powered content moderation service for community content"""
    
    def __init__(self, openai_client=None):
        self.openai_client = openai_client
        self.wellness_keywords = [
            'grateful', 'thankful', 'healing', 'growth', 'mindful', 'peace', 
            'love', 'hope', 'strength', 'courage', 'inspire', 'positive',
            'meditation', 'wellness', 'support', 'community', 'journey',
            'recovery', 'progress', 'breakthrough', 'transformation', 'balance'
        ]
        self.negative_keywords = [
            'hate', 'violence', 'harmful', 'dangerous', 'illegal', 'inappropriate',
            'offensive', 'discrimination', 'harassment', 'threat', 'abuse'
        ]
        self.blocked_patterns = [
            r'\b(?:contact|call|email|phone|website|http|www\.)\b',  # Contact info
            r'\b(?:buy|sell|price|money|payment|cash)\b',  # Commercial content
            r'\b(?:adult|explicit|sexual)\b'  # Adult content
        ]
    
    def moderate_content(self, content: str, content_type: str = "text") -> Dict[str, Any]:
        """
        Moderate content using AI and rule-based filtering
        Returns: {'is_safe': bool, 'reason': str, 'confidence': float, 'is_wellness_focused': bool}
        """
        try:
            # First, run basic rule-based filtering
            basic_result = self._basic_content_filter(content)
            
            if not basic_result['is_safe']:
                return basic_result
            
            # If OpenAI is available, use AI moderation
            if self.openai_client:
                ai_result = self._ai_moderation(content, content_type)
                
                # Combine results (AI takes precedence but basic rules can override)
                if not ai_result['is_safe']:
                    return ai_result
                
                # Use AI wellness assessment but combine confidence
                final_result = {
                    'is_safe': True,
                    'reason': ai_result['reason'],
                    'confidence': min(basic_result['confidence'], ai_result['confidence']),
                    'is_wellness_focused': ai_result.get('is_wellness_focused', basic_result.get('is_wellness_focused', False))
                }
                
                return final_result
            
            # Fallback to basic filtering only
            return basic_result
            
        except Exception as e:
            logger.error(f"Content moderation error: {e}")
            # Fail safe - if moderation fails, reject content
            return {
                'is_safe': False,
                'reason': 'Moderation system unavailable',
                'confidence': 0.0,
                'is_wellness_focused': False
            }
    
    def _basic_content_filter(self, content: str) -> Dict[str, Any]:
        """Basic rule-based content filtering"""
        try:
            content_lower = content.lower()
            
            # Check for blocked patterns
            for pattern in self.blocked_patterns:
                if re.search(pattern, content_lower):
                    return {
                        'is_safe': False,
                        'reason': 'Content contains blocked patterns (contact info, commercial, etc.)',
                        'confidence': 0.9,
                        'is_wellness_focused': False
                    }
            
            # Check for negative keywords
            negative_count = sum(1 for keyword in self.negative_keywords if keyword in content_lower)
            if negative_count > 0:
                return {
                    'is_safe': False,
                    'reason': 'Content contains negative or inappropriate language',
                    'confidence': 0.8,
                    'is_wellness_focused': False
                }
            
            # Check content length
            if len(content.strip()) < 10:
                return {
                    'is_safe': False,
                    'reason': 'Content too short',
                    'confidence': 0.9,
                    'is_wellness_focused': False
                }
            
            if len(content) > 2000:
                return {
                    'is_safe': False,
                    'reason': 'Content too long',
                    'confidence': 0.9,
                    'is_wellness_focused': False
                }
            
            # Assess wellness focus
            wellness_score = sum(1 for keyword in self.wellness_keywords if keyword in content_lower)
            total_words = len(content.split())
            wellness_ratio = wellness_score / max(total_words, 1)
            
            is_wellness_focused = wellness_score >= 2 or wellness_ratio > 0.1
            
            # Basic safety check passed
            base_confidence = 0.6
            
            # Boost confidence for wellness content
            if is_wellness_focused:
                confidence = min(0.9, base_confidence + (wellness_ratio * 0.3))
            else:
                confidence = base_confidence
            
            return {
                'is_safe': True,
                'reason': 'Content appears wellness-focused and safe' if is_wellness_focused else 'Content appears safe',
                'confidence': confidence,
                'is_wellness_focused': is_wellness_focused
            }
            
        except Exception as e:
            logger.error(f"Basic content filter error: {e}")
            return {
                'is_safe': False,
                'reason': 'Content filtering failed',
                'confidence': 0.0,
                'is_wellness_focused': False
            }
    
    def _ai_moderation(self, content: str, content_type: str) -> Dict[str, Any]:
        """AI-powered content moderation using OpenAI"""
        try:
            # First, use OpenAI's built-in moderation endpoint
            moderation_response = self.openai_client.moderations.create(input=content)
            moderation_result = moderation_response.results[0]
            
            if moderation_result.flagged:
                flagged_categories = [
                    category for category, flagged in moderation_result.categories.__dict__.items() 
                    if flagged
                ]
                
                return {
                    'is_safe': False,
                    'reason': f'Content flagged for: {", ".join(flagged_categories)}',
                    'confidence': 0.95,
                    'is_wellness_focused': False
                }
            
            # If not flagged, assess wellness focus with custom prompt
            wellness_prompt = f"""
            Analyze this {content_type} content for a wellness community platform:

            Content: "{content}"

            Please evaluate:
            1. Is this content positive, supportive, and appropriate for a wellness community?
            2. Does it align with themes of personal growth, healing, mindfulness, or emotional wellbeing?
            3. Rate the wellness focus from 0-10 (10 being highly wellness-focused)
            4. Overall safety assessment

            Respond in this exact format:
            SAFETY: [SAFE/UNSAFE]
            WELLNESS_SCORE: [0-10]
            REASON: [Brief explanation]
            """
            
            chat_response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a content moderator for a wellness community. Be thorough but fair in your assessment."
                    },
                    {
                        "role": "user",
                        "content": wellness_prompt
                    }
                ],
                max_tokens=200,
                temperature=0.1
            )
            
            response_text = chat_response.choices[0].message.content
            
            # Parse AI response
            safety_safe = "SAFE" in response_text.upper()
            
            # Extract wellness score
            wellness_score = 5  # Default
            if "WELLNESS_SCORE:" in response_text:
                try:
                    score_part = response_text.split("WELLNESS_SCORE:")[1].split("\n")[0].strip()
                    wellness_score = int(score_part.split()[0])
                except:
                    pass
            
            # Extract reason
            reason = "AI assessment completed"
            if "REASON:" in response_text:
                try:
                    reason = response_text.split("REASON:")[1].strip()
                except:
                    pass
            
            # Calculate confidence based on wellness score and safety
            if safety_safe:
                confidence = 0.7 + (wellness_score / 10 * 0.2)  # 0.7-0.9 range
            else:
                confidence = 0.9  # High confidence in unsafe assessment
            
            is_wellness_focused = wellness_score >= 6
            
            return {
                'is_safe': safety_safe,
                'reason': reason,
                'confidence': confidence,
                'is_wellness_focused': is_wellness_focused,
                'wellness_score': wellness_score
            }
            
        except Exception as e:
            logger.error(f"AI moderation error: {e}")
            # If AI fails, fall back to conservative approach
            return {
                'is_safe': False,
                'reason': 'AI moderation unavailable - content rejected for safety',
                'confidence': 0.5,
                'is_wellness_focused': False
            }
    
    def batch_moderate_content(self, content_items: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """Moderate multiple content items in batch"""
        try:
            results = []
            
            for item in content_items:
                content = item.get('content', '')
                content_type = item.get('content_type', 'text')
                item_id = item.get('id', 'unknown')
                
                moderation_result = self.moderate_content(content, content_type)
                moderation_result['item_id'] = item_id
                
                results.append(moderation_result)
            
            logger.info(f"🛡️ Batch moderated {len(content_items)} items")
            
            return results
            
        except Exception as e:
            logger.error(f"Batch moderation error: {e}")
            return []
    
    def get_moderation_stats(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get statistics from moderation results"""
        try:
            if not results:
                return {
                    'total_items': 0,
                    'approved_items': 0,
                    'rejected_items': 0,
                    'wellness_focused_items': 0,
                    'approval_rate': 0.0,
                    'wellness_rate': 0.0,
                    'average_confidence': 0.0
                }
            
            total_items = len(results)
            approved_items = sum(1 for r in results if r.get('is_safe', False))
            rejected_items = total_items - approved_items
            wellness_focused_items = sum(1 for r in results if r.get('is_wellness_focused', False))
            
            # Calculate rates
            approval_rate = (approved_items / total_items) * 100
            wellness_rate = (wellness_focused_items / total_items) * 100
            
            # Calculate average confidence
            confidences = [r.get('confidence', 0.0) for r in results]
            average_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            
            return {
                'total_items': total_items,
                'approved_items': approved_items,
                'rejected_items': rejected_items,
                'wellness_focused_items': wellness_focused_items,
                'approval_rate': round(approval_rate, 2),
                'wellness_rate': round(wellness_rate, 2),
                'average_confidence': round(average_confidence, 3)
            }
            
        except Exception as e:
            logger.error(f"Failed to calculate moderation stats: {e}")
            return {}
    
    def is_wellness_content(self, content: str) -> bool:
        """Quick check if content is wellness-focused"""
        try:
            content_lower = content.lower()
            wellness_score = sum(1 for keyword in self.wellness_keywords if keyword in content_lower)
            total_words = len(content.split())
            wellness_ratio = wellness_score / max(total_words, 1)
            
            return wellness_score >= 2 or wellness_ratio > 0.1
            
        except Exception:
            return False
    
    def get_wellness_suggestions(self, content: str) -> List[str]:
        """Get suggestions to make content more wellness-focused"""
        try:
            suggestions = []
            content_lower = content.lower()
            
            # Check for wellness keywords
            wellness_count = sum(1 for keyword in self.wellness_keywords if keyword in content_lower)
            
            if wellness_count == 0:
                suggestions.append("Consider adding words related to wellness, growth, or healing")
            
            # Check for positive language
            positive_words = ['positive', 'good', 'better', 'improve', 'growth', 'learning']
            positive_count = sum(1 for word in positive_words if word in content_lower)
            
            if positive_count == 0:
                suggestions.append("Try using more positive and uplifting language")
            
            # Check for personal growth themes
            growth_words = ['learn', 'grow', 'develop', 'improve', 'progress', 'journey']
            growth_count = sum(1 for word in growth_words if word in content_lower)
            
            if growth_count == 0:
                suggestions.append("Consider sharing insights about personal growth or learning")
            
            # Check for community connection
            community_words = ['share', 'together', 'support', 'community', 'connect', 'help']
            community_count = sum(1 for word in community_words if word in content_lower)
            
            if community_count == 0:
                suggestions.append("Think about how your content can connect with and support others")
            
            return suggestions[:3]  # Limit to 3 suggestions
            
        except Exception as e:
            logger.error(f"Failed to generate wellness suggestions: {e}")
            return []