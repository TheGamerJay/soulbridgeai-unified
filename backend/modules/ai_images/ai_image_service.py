"""
SoulBridge AI - AI Image Generation Service
Handles DALL-E integration and image generation with credit system
Extracted from backend/app.py with improvements
"""
import logging
import openai
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
import base64
import json

logger = logging.getLogger(__name__)

class AIImageService:
    """Service for AI image generation using DALL-E API"""
    
    def __init__(self, openai_client=None, credits_manager=None):
        self.openai_client = openai_client
        self.credits_manager = credits_manager
        self.image_cost = 5  # Default cost from constants
        self.supported_styles = [
            "photorealistic", "artistic", "cartoon", "abstract", 
            "vintage", "modern", "minimalist", "detailed"
        ]
        self.supported_sizes = ["1024x1024", "1792x1024", "1024x1792"]
        
    def check_access_and_limits(self, user_id: int, user_plan: str, 
                               trial_active: bool, user_addons: list = None) -> Dict[str, Any]:
        """Check if user has access and hasn't exceeded limits"""
        try:
            user_addons = user_addons or []
            
            # Check basic access
            if user_plan not in ['silver', 'gold'] and not trial_active and 'ai-image-generation' not in user_addons:
                return {
                    'has_access': False,
                    'error': 'AI Image Generation requires Silver/Gold tier, addon, or trial'
                }
            
            # Determine effective tier for AI images
            if trial_active and user_plan == 'bronze':
                ai_image_tier = 'silver'  # Bronze trial users get Silver-level access
            else:
                ai_image_tier = user_plan
            
            # Get tier-based limits
            from ..tiers.artistic_time import AI_IMAGE_LIMITS
            monthly_limit = AI_IMAGE_LIMITS.get(ai_image_tier, 0)
            
            # Check monthly usage (session-based for now, should be DB in production)
            current_month = datetime.now().strftime('%Y-%m')
            monthly_usage = self._get_monthly_usage(user_id, current_month)
            
            if monthly_limit < 999999 and monthly_usage >= monthly_limit:
                tier_name = {"bronze": "Bronze", "silver": "Silver", "gold": "Gold"}[ai_image_tier]
                return {
                    'has_access': False,
                    'error': f'Monthly AI image limit reached ({monthly_limit} images for {tier_name} tier)'
                }
            
            # Check artistic time credits
            if self.credits_manager:
                current_credits = self.credits_manager.get_artistic_time(user_id)
                if current_credits < self.image_cost:
                    return {
                        'has_access': False,
                        'error': f'Insufficient artistic time. Need {self.image_cost} artistic time, you have {current_credits}.'
                    }
            
            return {
                'has_access': True,
                'ai_image_tier': ai_image_tier,
                'monthly_limit': monthly_limit,
                'monthly_usage': monthly_usage,
                'credits_available': current_credits if self.credits_manager else 0
            }
            
        except Exception as e:
            logger.error(f"Failed to check AI image access: {e}")
            return {
                'has_access': False,
                'error': 'Failed to check access permissions'
            }
    
    def generate_image(self, user_id: int, prompt: str, style: str = "photorealistic", 
                      size: str = "1024x1024", quality: str = "standard") -> Dict[str, Any]:
        """Generate AI image using DALL-E API"""
        try:
            if not self.openai_client:
                return {
                    'success': False,
                    'error': 'OpenAI client not configured'
                }
            
            if not prompt or len(prompt.strip()) < 10:
                return {
                    'success': False,
                    'error': 'Prompt must be at least 10 characters long'
                }
            
            # Validate inputs
            if style not in self.supported_styles:
                style = "photorealistic"
            
            if size not in self.supported_sizes:
                size = "1024x1024"
            
            # Deduct credits first (prevents abuse)
            if self.credits_manager:
                if not self.credits_manager.deduct_artistic_time(user_id, self.image_cost):
                    return {
                        'success': False,
                        'error': 'Failed to deduct artistic time. Please try again.'
                    }
                
                logger.info(f"🎨 Deducted {self.image_cost} artistic time from user {user_id} for AI image generation")
            
            # Enhance prompt with style
            enhanced_prompt = self._enhance_prompt(prompt, style)
            
            logger.info(f"🎨 Generating image with DALL-E: {enhanced_prompt[:100]}...")
            
            # Generate image using DALL-E
            response = self.openai_client.images.generate(
                model="dall-e-3",
                prompt=enhanced_prompt,
                size=size,
                quality=quality,
                n=1
            )
            
            image_url = response.data[0].url
            revised_prompt = getattr(response.data[0], 'revised_prompt', enhanced_prompt)
            
            logger.info(f"✅ DALL-E image generated successfully")
            
            # Record usage
            self._record_usage(user_id)
            
            return {
                'success': True,
                'image_url': image_url,
                'original_prompt': prompt,
                'enhanced_prompt': enhanced_prompt,
                'revised_prompt': revised_prompt,
                'style': style,
                'size': size,
                'generation_time': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ DALL-E generation failed: {e}")
            
            # Refund credits since generation failed
            if self.credits_manager:
                if self.credits_manager.refund_artistic_time(user_id, self.image_cost, "AI image generation failed"):
                    logger.info(f"💰 Refunded {self.image_cost} artistic time to user {user_id} due to generation failure")
                else:
                    logger.error(f"❌ Failed to refund artistic time to user {user_id}")
            
            return {
                'success': False,
                'error': f'Image generation failed: {str(e)}'
            }
    
    def analyze_reference_image(self, image_data: str, user_id: int) -> Dict[str, Any]:
        """Analyze reference image using GPT-4 Vision to create detailed description"""
        try:
            if not self.openai_client:
                return {
                    'success': False,
                    'error': 'OpenAI client not configured'
                }
            
            if not image_data:
                return {
                    'success': False,
                    'error': 'No image data provided'
                }
            
            logger.info(f"🔍 Analyzing reference image for user {user_id}")
            
            # Create vision prompt
            vision_prompt = (
                "Analyze this image and create a concise but detailed description that could be used "
                "to generate a similar image with DALL-E. Focus on: style, composition, colors, mood, "
                "objects, characters, lighting, and artistic techniques. Keep it under 3000 characters "
                "while being descriptive and specific."
            )
            
            # Call GPT-4 Vision API
            response = self.openai_client.chat.completions.create(
                model="gpt-4-vision-preview",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": vision_prompt},
                            {"type": "image_url", "image_url": {"url": image_data}}
                        ]
                    }
                ],
                max_tokens=1000
            )
            
            description = response.choices[0].message.content
            logger.info(f"✅ GPT-4 Vision analysis completed: {len(description)} characters")
            
            # DALL-E 3 has a 4000 character limit, so truncate if needed
            if len(description) > 3800:
                logger.info(f"🔄 Truncating description from {len(description)} to 3800 characters")
                description = description[:3800] + "..."
            
            return {
                'success': True,
                'description': description,
                'analysis_time': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Reference image analysis error: {e}")
            return {
                'success': False,
                'error': f'Failed to analyze reference image: {str(e)}'
            }
    
    def get_usage_stats(self, user_id: int, user_plan: str, trial_active: bool, 
                       requested_tier: str = None) -> Dict[str, Any]:
        """Get user's AI image generation usage statistics"""
        try:
            # Determine AI image tier
            if requested_tier and trial_active and user_plan == 'bronze':
                ai_image_tier = requested_tier if requested_tier in ['silver', 'gold'] else user_plan
            elif trial_active and user_plan == 'bronze':
                ai_image_tier = 'silver'
            else:
                ai_image_tier = user_plan
            
            # Get limits and usage
            from ..tiers.artistic_time import AI_IMAGE_LIMITS
            
            # Get artistic time for credit-based features
            artistic_time = self.credits_manager.get_artistic_time(user_id) if self.credits_manager else 0
            
            # Determine monthly limit
            if ai_image_tier == 'gold' and not (trial_active and user_plan == 'bronze'):
                monthly_limit = AI_IMAGE_LIMITS.get('gold', 999999)
            elif artistic_time > 0:
                monthly_limit = artistic_time // self.image_cost
            else:
                monthly_limit = AI_IMAGE_LIMITS.get(ai_image_tier, 0)
            
            current_month = datetime.now().strftime('%Y-%m')
            monthly_usage = self._get_monthly_usage(user_id, current_month)
            
            # Display limit for UI
            if ai_image_tier == 'gold':
                display_limit = 999
            else:
                display_limit = monthly_limit
            
            return {
                'success': True,
                'tier': ai_image_tier,
                'monthly_limit': monthly_limit,
                'display_limit': display_limit,
                'monthly_usage': monthly_usage,
                'remaining': max(0, monthly_limit - monthly_usage) if monthly_limit < 999999 else 999,
                'artistic_time': artistic_time,
                'cost_per_image': self.image_cost,
                'reset_date': self._get_next_reset_date()
            }
            
        except Exception as e:
            logger.error(f"Failed to get usage stats: {e}")
            return {
                'success': False,
                'error': 'Failed to get usage statistics'
            }
    
    def _enhance_prompt(self, prompt: str, style: str) -> str:
        """Enhance user prompt with style information"""
        try:
            style_enhancements = {
                "photorealistic": "High quality, photorealistic, detailed",
                "artistic": "Artistic, expressive, creative",
                "cartoon": "Cartoon style, animated, colorful",
                "abstract": "Abstract art, conceptual, artistic",
                "vintage": "Vintage style, retro, classic",
                "modern": "Modern, contemporary, sleek",
                "minimalist": "Minimalist, clean, simple",
                "detailed": "Highly detailed, intricate, complex"
            }
            
            enhancement = style_enhancements.get(style, "High quality, detailed")
            return f"{prompt}. {enhancement}, {style} style."
            
        except Exception:
            return f"{prompt}. High quality, detailed, {style} style."
    
    def _get_monthly_usage(self, user_id: int, current_month: str) -> int:
        """Get user's monthly usage (placeholder for session/DB implementation)"""
        # TODO: Implement proper database storage for usage tracking
        # For now, this would need to be implemented in the route handler using session
        return 0
    
    def _record_usage(self, user_id: int) -> None:
        """Record image generation usage (placeholder for session/DB implementation)"""
        # TODO: Implement proper usage recording in database
        # For now, this would need to be implemented in the route handler using session
        pass
    
    def _get_next_reset_date(self) -> str:
        """Get next monthly reset date"""
        try:
            now = datetime.now()
            if now.month == 12:
                next_month = now.replace(year=now.year + 1, month=1, day=1)
            else:
                next_month = now.replace(month=now.month + 1, day=1)
            return next_month.strftime('%Y-%m-%d')
        except Exception:
            return "Next month"
    
    def validate_prompt(self, prompt: str) -> Dict[str, Any]:
        """Validate image generation prompt"""
        try:
            if not prompt or not prompt.strip():
                return {'valid': False, 'error': 'Prompt cannot be empty'}
            
            prompt = prompt.strip()
            
            if len(prompt) < 10:
                return {'valid': False, 'error': 'Prompt must be at least 10 characters long'}
            
            if len(prompt) > 3000:
                return {'valid': False, 'error': 'Prompt must be less than 3000 characters'}
            
            # Check for potentially problematic content (basic filter)
            forbidden_keywords = ['nude', 'naked', 'explicit', 'sexual', 'violence', 'gore']
            prompt_lower = prompt.lower()
            
            for keyword in forbidden_keywords:
                if keyword in prompt_lower:
                    return {
                        'valid': False, 
                        'error': f'Prompt contains inappropriate content. Please revise and try again.'
                    }
            
            return {
                'valid': True,
                'cleaned_prompt': prompt,
                'estimated_tokens': len(prompt.split())
            }
            
        except Exception as e:
            logger.error(f"Prompt validation error: {e}")
            return {'valid': False, 'error': 'Failed to validate prompt'}