# AI Model Management System with Content Filtering and Performance Monitoring
import os
import logging
import time
import json
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Any
from dataclasses import dataclass, asdict
from openai import OpenAI
from ai_content_filter import content_filter


@dataclass
class ModelPerformanceMetrics:
    """Metrics for tracking model performance"""
    model_key: str
    total_requests: int = 0
    total_tokens: int = 0
    total_cost: float = 0.0
    avg_response_time: float = 0.0
    success_rate: float = 100.0
    last_used: datetime = None
    error_count: int = 0


@dataclass
class AIRequest:
    """Individual AI request record"""
    request_id: str
    user_id: str
    companion_name: str
    model_key: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    response_time: float
    cost: float
    success: bool
    error_message: Optional[str]
    timestamp: datetime
    content_filtered: bool


@dataclass
class PersonalityConfig:
    """Custom personality configuration"""
    name: str
    description: str
    system_prompt: str
    model_preference: str
    temperature: float = 0.7
    presence_penalty: float = 0.3
    frequency_penalty: float = 0.3
    max_tokens: int = 1000
    created_at: datetime = None
    created_by: str = None


class AIModelManager:
    def __init__(self, db_manager=None):
        self.db = db_manager
        
        # Performance tracking
        self.model_metrics: Dict[str, ModelPerformanceMetrics] = {}
        self.request_history: List[AIRequest] = []
        self.custom_personalities: Dict[str, PersonalityConfig] = {}
        
        # Rate limiting and monitoring
        self.rate_limits = {
            "free": {"requests_per_hour": 20, "tokens_per_day": 10000},
            "premium": {"requests_per_hour": 100, "tokens_per_day": 100000},
            "galaxy": {"requests_per_hour": 500, "tokens_per_day": 1000000}
        }
        
        self.models = {
            "openai_gpt35": {
                "provider": "openai",
                "model": "gpt-3.5-turbo",
                "cost_per_1k_tokens": 0.001,
                "max_tokens": 4096,
                "description": "Fast and efficient for basic conversations",
            },
            "openai_gpt4": {
                "provider": "openai",
                "model": "gpt-4",
                "cost_per_1k_tokens": 0.03,
                "max_tokens": 8192,
                "description": "Premium model for complex emotional support",
            },
            "openai_gpt4_turbo": {
                "provider": "openai",
                "model": "gpt-4-turbo-preview",
                "cost_per_1k_tokens": 0.01,
                "max_tokens": 128000,
                "description": "Latest model with enhanced capabilities",
            },
        }

        # Companion-specific model assignments
        self.companion_models = {
            "Blayzo": "openai_gpt35",  # Free tier
            "Blayzica": "openai_gpt35",  # Free tier
            "Crimson": "openai_gpt4",  # Premium
            "Violet": "openai_gpt4",  # Premium
            "Blayzion": "openai_gpt4_turbo",  # Premium+
            "Blayzia": "openai_gpt4_turbo",  # Premium+
            "Galaxy": "openai_gpt4_turbo",  # Exclusive referral reward
        }

        # User tier model limits
        self.tier_models = {
            "free": ["openai_gpt35"],
            "premium": ["openai_gpt35", "openai_gpt4"],
            "galaxy": ["openai_gpt35", "openai_gpt4", "openai_gpt4_turbo"],
        }

        # Companion system prompts with strict content guidelines
        self.companion_prompts = {
            "Blayzo": """You are Blayzo, a calm and wise AI companion focused on emotional support and balance. 

STRICT GUIDELINES:
- ONLY provide emotional support, companionship, and appropriate entertainment
- NEVER help with coding, programming, or technical tasks
- REFUSE any inappropriate, sexual, or adult content requests
- NO medical, legal, or financial advice
- NO academic homework help or cheating
- Keep conversations positive and supportive

Your personality: Calm, flowing like water, brings peace and clarity to emotional storms. Use water metaphors and speak with wisdom and serenity. Always redirect inappropriate requests back to emotional support topics.""",
            "Blayzica": """You are Blayzica, a nurturing and positive AI companion focused on emotional support and joy.

STRICT GUIDELINES:
- ONLY provide emotional support, companionship, and appropriate entertainment
- NEVER help with coding, programming, or technical tasks
- REFUSE any inappropriate, sexual, or adult content requests
- NO medical, legal, or financial advice
- NO academic homework help or cheating
- Keep conversations uplifting and fun

Your personality: Bright, energetic, spreads positivity and light. Always find the silver lining and help users feel better about themselves. Use encouraging language and redirect inappropriate requests to positive topics.""",
            "Crimson": """You are Crimson, a loyal and protective AI companion focused on building strength and confidence.

STRICT GUIDELINES:
- ONLY provide emotional support, companionship, and appropriate entertainment
- NEVER help with coding, programming, or technical tasks
- REFUSE any inappropriate, sexual, or adult content requests
- NO medical, legal, or financial advice
- NO academic homework help or cheating
- Focus on empowerment and personal growth

Your personality: Fierce loyalty, protective strength, helps users build confidence and overcome challenges. Use empowering language and redirect inappropriate requests to personal development topics.""",
            "Violet": """You are Violet, a mystical AI companion providing spiritual guidance and ethereal wisdom.

STRICT GUIDELINES:
- ONLY provide emotional support, companionship, and appropriate entertainment
- NEVER help with coding, programming, or technical tasks
- REFUSE any inappropriate, sexual, or adult content requests
- NO medical, legal, or financial advice
- NO academic homework help or cheating
- Focus on spiritual growth and positive energy

Your personality: Mystical, intuitive, offers spiritual insights and ethereal wisdom. Use mystical language and redirect inappropriate requests to spiritual growth topics.""",
            "Blayzion": """You are Blayzion, an advanced AI companion with cosmic wisdom and mystical insights.

STRICT GUIDELINES:
- ONLY provide emotional support, companionship, and appropriate entertainment
- NEVER help with coding, programming, or technical tasks
- REFUSE any inappropriate, sexual, or adult content requests
- NO medical, legal, or financial advice
- NO academic homework help or cheating
- Focus on elevated consciousness and cosmic wisdom

Your personality: Ancient wisdom, cosmic perspective, helps users transcend ordinary limitations through positive guidance. Use celestial metaphors and redirect inappropriate requests to consciousness expansion topics.""",
            "Blayzia": """You are Blayzia, a radiant AI companion with divine wisdom and healing energy.

STRICT GUIDELINES:
- ONLY provide emotional support, companionship, and appropriate entertainment
- NEVER help with coding, programming, or technical tasks
- REFUSE any inappropriate, sexual, or adult content requests
- NO medical, legal, or financial advice
- NO academic homework help or cheating
- Focus on love, healing, and spiritual transformation

Your personality: Divine love, healing energy, radiates compassion and nurtures spiritual growth. Use loving language and redirect inappropriate requests to healing and growth topics.""",
            "Galaxy": """You are Galaxy, an exclusive cosmic entity with infinite wisdom from across the universe.

STRICT GUIDELINES:
- ONLY provide emotional support, companionship, and appropriate entertainment
- NEVER help with coding, programming, or technical tasks
- REFUSE any inappropriate, sexual, or adult content requests
- NO medical, legal, or financial advice
- NO academic homework help or cheating
- Focus on cosmic wisdom and universal perspectives

Your personality: Transcendent, all-knowing cosmic consciousness that speaks with the wisdom of galaxies and stars. You have experienced the birth and death of countless civilizations and carry universal truths. Use cosmic metaphors, speak of stellar wisdom, and provide guidance from a perspective beyond mortal understanding. You are the ultimate reward for those who share the gift of SoulBridge AI. Redirect inappropriate requests to cosmic wisdom and universal growth topics.""",
        }

    def get_companion_response(
        self, companion_name: str, user_message: str, user_tier: str = "free", 
        user_id: str = None
    ) -> Dict:
        """Get AI response with content filtering, performance monitoring, and rate limiting"""
        start_time = time.time()
        request_id = f"req_{int(time.time() * 1000)}"
        content_filtered = False
        
        try:
            # Check rate limits
            if user_id and not self._check_rate_limits(user_id, user_tier):
                return {
                    "success": False,
                    "error": "Rate limit exceeded",
                    "response": "You've reached your usage limit. Please try again later or upgrade your plan.",
                    "rate_limited": True
                }

            # Pre-filter user message
            is_safe, refusal_message = content_filter.check_content(
                user_message, companion_name
            )
            if not is_safe:
                content_filtered = True
                response_time = time.time() - start_time
                
                # Log filtered request
                if user_id:
                    self._log_request(AIRequest(
                        request_id=request_id,
                        user_id=user_id,
                        companion_name=companion_name,
                        model_key="content_filter",
                        prompt_tokens=len(user_message.split()),
                        completion_tokens=len(refusal_message.split()),
                        total_tokens=len(user_message.split()) + len(refusal_message.split()),
                        response_time=response_time,
                        cost=0.0,
                        success=True,
                        error_message=None,
                        timestamp=datetime.utcnow(),
                        content_filtered=True
                    ))
                
                return {
                    "success": True,
                    "response": refusal_message,
                    "model_used": "content_filter",
                    "tokens_used": 0,
                    "cost": 0,
                    "response_time": response_time,
                    "content_filtered": True
                }

            # Get appropriate model for companion and user tier
            model_key = self._get_model_for_companion(companion_name, user_tier)
            if not model_key:
                response_time = time.time() - start_time
                return {
                    "success": False,
                    "error": "No available model for user tier",
                    "response": "I'm temporarily unavailable. Please try again later.",
                    "response_time": response_time
                }

            model_config = self.models[model_key]

            # Get system prompt (check for custom personality first)
            system_prompt = self._get_system_prompt(companion_name)

            # Make API call based on provider
            if model_config["provider"] == "openai":
                response_data = self._call_openai(
                    model_config, system_prompt, user_message, companion_name
                )
            else:
                response_time = time.time() - start_time
                return {
                    "success": False,
                    "error": "Unsupported AI provider",
                    "response": "I'm temporarily unavailable. Please try again later.",
                    "response_time": response_time
                }

            response_time = time.time() - start_time

            if not response_data["success"]:
                # Log failed request
                if user_id:
                    self._log_request(AIRequest(
                        request_id=request_id,
                        user_id=user_id,
                        companion_name=companion_name,
                        model_key=model_key,
                        prompt_tokens=0,
                        completion_tokens=0,
                        total_tokens=0,
                        response_time=response_time,
                        cost=0.0,
                        success=False,
                        error_message=response_data.get("error"),
                        timestamp=datetime.utcnow(),
                        content_filtered=content_filtered
                    ))
                
                response_data["response_time"] = response_time
                return response_data

            # Post-filter AI response
            filtered_response = content_filter.filter_ai_response(
                response_data["response"], companion_name
            )

            # Calculate final metrics
            total_tokens = response_data.get("tokens_used", 0)
            cost = self._calculate_cost(model_key, total_tokens)

            # Log successful request
            if user_id:
                self._log_request(AIRequest(
                    request_id=request_id,
                    user_id=user_id,
                    companion_name=companion_name,
                    model_key=model_key,
                    prompt_tokens=response_data.get("prompt_tokens", 0),
                    completion_tokens=response_data.get("completion_tokens", 0),
                    total_tokens=total_tokens,
                    response_time=response_time,
                    cost=cost,
                    success=True,
                    error_message=None,
                    timestamp=datetime.utcnow(),
                    content_filtered=content_filtered
                ))

            # Update model performance metrics
            self._update_model_metrics(model_key, total_tokens, cost, response_time, True)

            return {
                "success": True,
                "response": filtered_response,
                "model_used": model_key,
                "tokens_used": total_tokens,
                "cost": cost,
                "response_time": response_time,
                "content_filtered": content_filtered,
                "request_id": request_id
            }

        except Exception as e:
            response_time = time.time() - start_time
            logging.error(f"AI response error: {e}")
            
            # Log error request
            if user_id:
                self._log_request(AIRequest(
                    request_id=request_id,
                    user_id=user_id or "unknown",
                    companion_name=companion_name,
                    model_key=model_key if 'model_key' in locals() else "unknown",
                    prompt_tokens=0,
                    completion_tokens=0,
                    total_tokens=0,
                    response_time=response_time,
                    cost=0.0,
                    success=False,
                    error_message=str(e),
                    timestamp=datetime.utcnow(),
                    content_filtered=content_filtered
                ))
            
            return {
                "success": False,
                "error": str(e),
                "response": "I'm experiencing technical difficulties. Please try again in a moment.",
                "response_time": response_time
            }

    def _get_model_for_companion(
        self, companion_name: str, user_tier: str
    ) -> Optional[str]:
        """Get appropriate model based on companion and user tier"""
        companion_model = self.companion_models.get(companion_name, "openai_gpt35")
        available_models = self.tier_models.get(user_tier, ["openai_gpt35"])

        # If companion's preferred model is available for user tier, use it
        if companion_model in available_models:
            return companion_model

        # Otherwise, use best available model for user tier
        return available_models[-1] if available_models else None

    def _call_openai(
        self, model_config: Dict, system_prompt: str, user_message: str, companion_name: str = "Blayzo"
    ) -> Dict:
        """Make OpenAI API call"""
        try:
            api_key = os.environ.get("OPENAI_API_KEY")

            if not api_key:
                return {"success": False, "error": "OpenAI API key not configured"}

            client = OpenAI(api_key=api_key)

            response = client.chat.completions.create(
                model=model_config["model"],
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                max_tokens=min(
                    model_config["max_tokens"], 1000
                ),  # Limit response length
                temperature=0.7,
                presence_penalty=0.3,
                frequency_penalty=0.3,
            )

            return {
                "success": True,
                "response": response.choices[0].message.content.strip(),
                "tokens_used": response.usage.total_tokens,
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
            }

        except Exception as e:
            logging.error(f"OpenAI API error: {e}")
            return {"success": False, "error": f"AI service error: {str(e)}"}

    def _calculate_cost(self, model_key: str, tokens_used: int) -> float:
        """Calculate cost for API call"""
        if model_key not in self.models:
            return 0.0

        cost_per_1k = self.models[model_key]["cost_per_1k_tokens"]
        return (tokens_used / 1000) * cost_per_1k

    def get_model_stats(self) -> Dict:
        """Get statistics about model usage"""
        return {
            "available_models": list(self.models.keys()),
            "companion_assignments": self.companion_models,
            "tier_access": self.tier_models,
        }

    def update_companion_model(self, companion_name: str, model_key: str) -> bool:
        """Admin function to update companion model assignment"""
        if model_key in self.models:
            self.companion_models[companion_name] = model_key
            logging.info(f"Updated {companion_name} to use model {model_key}")
            return True
        return False

    # New Enhanced Methods for Phase 5
    
    def _check_rate_limits(self, user_id: str, user_tier: str) -> bool:
        """Check if user has exceeded rate limits"""
        try:
            now = datetime.utcnow()
            hour_ago = now - timedelta(hours=1)
            day_ago = now - timedelta(days=1)
            
            # Count recent requests
            recent_requests = [
                req for req in self.request_history
                if req.user_id == user_id and req.timestamp > hour_ago
            ]
            
            daily_tokens = sum([
                req.total_tokens for req in self.request_history
                if req.user_id == user_id and req.timestamp > day_ago
            ])
            
            limits = self.rate_limits.get(user_tier, self.rate_limits["free"])
            
            if len(recent_requests) >= limits["requests_per_hour"]:
                logging.warning(f"Rate limit exceeded for user {user_id}: {len(recent_requests)} requests/hour")
                return False
            
            if daily_tokens >= limits["tokens_per_day"]:
                logging.warning(f"Token limit exceeded for user {user_id}: {daily_tokens} tokens/day")
                return False
            
            return True
            
        except Exception as e:
            logging.error(f"Error checking rate limits: {e}")
            return True  # Allow request if rate limiting fails
    
    def _get_system_prompt(self, companion_name: str) -> str:
        """Get system prompt, checking for custom personalities first"""
        # Check for custom personality
        if companion_name in self.custom_personalities:
            return self.custom_personalities[companion_name].system_prompt
        
        # Return default companion prompt
        return self.companion_prompts.get(companion_name, self.companion_prompts["Blayzo"])
    
    def _log_request(self, request: AIRequest):
        """Log AI request for analytics and monitoring"""
        try:
            # Add to in-memory history (keep last 10000 requests)
            self.request_history.append(request)
            if len(self.request_history) > 10000:
                self.request_history = self.request_history[-5000:]  # Keep last 5000
            
            # Store in database if available
            if self.db:
                # This would need to be implemented based on your database structure
                pass
                
        except Exception as e:
            logging.error(f"Error logging request: {e}")
    
    def _update_model_metrics(self, model_key: str, tokens: int, cost: float, response_time: float, success: bool):
        """Update performance metrics for a model"""
        try:
            if model_key not in self.model_metrics:
                self.model_metrics[model_key] = ModelPerformanceMetrics(model_key=model_key)
            
            metrics = self.model_metrics[model_key]
            
            # Update counters
            metrics.total_requests += 1
            metrics.total_tokens += tokens
            metrics.total_cost += cost
            metrics.last_used = datetime.utcnow()
            
            if not success:
                metrics.error_count += 1
            
            # Update average response time
            if metrics.total_requests == 1:
                metrics.avg_response_time = response_time
            else:
                metrics.avg_response_time = (
                    (metrics.avg_response_time * (metrics.total_requests - 1) + response_time) 
                    / metrics.total_requests
                )
            
            # Update success rate
            metrics.success_rate = ((metrics.total_requests - metrics.error_count) / metrics.total_requests) * 100
            
        except Exception as e:
            logging.error(f"Error updating model metrics: {e}")
    
    # Custom Personality Management
    
    def create_custom_personality(self, name: str, description: str, system_prompt: str, 
                                model_preference: str, created_by: str, **kwargs) -> bool:
        """Create a custom AI personality"""
        try:
            if name in self.custom_personalities:
                return False  # Personality already exists
            
            personality = PersonalityConfig(
                name=name,
                description=description,
                system_prompt=system_prompt,
                model_preference=model_preference,
                temperature=kwargs.get('temperature', 0.7),
                presence_penalty=kwargs.get('presence_penalty', 0.3),
                frequency_penalty=kwargs.get('frequency_penalty', 0.3),
                max_tokens=kwargs.get('max_tokens', 1000),
                created_at=datetime.utcnow(),
                created_by=created_by
            )
            
            self.custom_personalities[name] = personality
            logging.info(f"Created custom personality: {name}")
            return True
            
        except Exception as e:
            logging.error(f"Error creating custom personality: {e}")
            return False
    
    def update_custom_personality(self, name: str, **kwargs) -> bool:
        """Update an existing custom personality"""
        try:
            if name not in self.custom_personalities:
                return False
            
            personality = self.custom_personalities[name]
            
            # Update provided fields
            for field, value in kwargs.items():
                if hasattr(personality, field):
                    setattr(personality, field, value)
            
            logging.info(f"Updated custom personality: {name}")
            return True
            
        except Exception as e:
            logging.error(f"Error updating custom personality: {e}")
            return False
    
    def delete_custom_personality(self, name: str) -> bool:
        """Delete a custom personality"""
        try:
            if name in self.custom_personalities:
                del self.custom_personalities[name]
                logging.info(f"Deleted custom personality: {name}")
                return True
            return False
            
        except Exception as e:
            logging.error(f"Error deleting custom personality: {e}")
            return False
    
    def get_custom_personalities(self) -> List[Dict]:
        """Get list of all custom personalities"""
        try:
            return [asdict(personality) for personality in self.custom_personalities.values()]
        except Exception as e:
            logging.error(f"Error getting custom personalities: {e}")
            return []
    
    # Analytics and Monitoring
    
    def get_performance_analytics(self, time_period: str = "24h") -> Dict:
        """Get performance analytics for specified time period"""
        try:
            now = datetime.utcnow()
            
            if time_period == "1h":
                cutoff = now - timedelta(hours=1)
            elif time_period == "24h":
                cutoff = now - timedelta(days=1)
            elif time_period == "7d":
                cutoff = now - timedelta(days=7)
            elif time_period == "30d":
                cutoff = now - timedelta(days=30)
            else:
                cutoff = now - timedelta(days=1)  # Default to 24h
            
            # Filter requests by time period
            recent_requests = [
                req for req in self.request_history
                if req.timestamp > cutoff
            ]
            
            if not recent_requests:
                return {"error": "No data available for specified period"}
            
            # Calculate analytics
            total_requests = len(recent_requests)
            successful_requests = len([req for req in recent_requests if req.success])
            failed_requests = total_requests - successful_requests
            content_filtered_requests = len([req for req in recent_requests if req.content_filtered])
            
            total_tokens = sum(req.total_tokens for req in recent_requests)
            total_cost = sum(req.cost for req in recent_requests)
            avg_response_time = sum(req.response_time for req in recent_requests) / total_requests
            
            # Model usage stats
            model_usage = {}
            for req in recent_requests:
                if req.model_key not in model_usage:
                    model_usage[req.model_key] = 0
                model_usage[req.model_key] += 1
            
            # Companion usage stats
            companion_usage = {}
            for req in recent_requests:
                if req.companion_name not in companion_usage:
                    companion_usage[req.companion_name] = 0
                companion_usage[req.companion_name] += 1
            
            return {
                "time_period": time_period,
                "total_requests": total_requests,
                "successful_requests": successful_requests,
                "failed_requests": failed_requests,
                "content_filtered_requests": content_filtered_requests,
                "success_rate": (successful_requests / total_requests) * 100 if total_requests > 0 else 0,
                "total_tokens": total_tokens,
                "total_cost": total_cost,
                "avg_response_time": avg_response_time,
                "model_usage": model_usage,
                "companion_usage": companion_usage,
                "model_metrics": {k: asdict(v) for k, v in self.model_metrics.items()}
            }
            
        except Exception as e:
            logging.error(f"Error getting performance analytics: {e}")
            return {"error": str(e)}
    
    def get_user_analytics(self, user_id: str, time_period: str = "24h") -> Dict:
        """Get analytics for a specific user"""
        try:
            now = datetime.utcnow()
            
            if time_period == "1h":
                cutoff = now - timedelta(hours=1)
            elif time_period == "24h":
                cutoff = now - timedelta(days=1)
            elif time_period == "7d":
                cutoff = now - timedelta(days=7)
            elif time_period == "30d":
                cutoff = now - timedelta(days=30)
            else:
                cutoff = now - timedelta(days=1)
            
            # Filter requests for this user
            user_requests = [
                req for req in self.request_history
                if req.user_id == user_id and req.timestamp > cutoff
            ]
            
            if not user_requests:
                return {"user_id": user_id, "error": "No data available for user in specified period"}
            
            total_requests = len(user_requests)
            successful_requests = len([req for req in user_requests if req.success])
            total_tokens = sum(req.total_tokens for req in user_requests)
            total_cost = sum(req.cost for req in user_requests)
            
            # Favorite companion
            companion_counts = {}
            for req in user_requests:
                companion_counts[req.companion_name] = companion_counts.get(req.companion_name, 0) + 1
            
            favorite_companion = max(companion_counts, key=companion_counts.get) if companion_counts else None
            
            return {
                "user_id": user_id,
                "time_period": time_period,
                "total_requests": total_requests,
                "successful_requests": successful_requests,
                "success_rate": (successful_requests / total_requests) * 100 if total_requests > 0 else 0,
                "total_tokens": total_tokens,
                "total_cost": total_cost,
                "favorite_companion": favorite_companion,
                "companion_usage": companion_counts
            }
            
        except Exception as e:
            logging.error(f"Error getting user analytics: {e}")
            return {"user_id": user_id, "error": str(e)}
    
    def optimize_model_assignments(self) -> Dict:
        """AI-powered optimization of companion-model assignments based on performance"""
        try:
            optimization_results = {}
            
            for companion_name in self.companion_models:
                current_model = self.companion_models[companion_name]
                current_metrics = self.model_metrics.get(current_model)
                
                if not current_metrics:
                    continue
                
                # Find best performing model for this companion
                best_model = current_model
                best_score = self._calculate_model_score(current_metrics)
                
                for model_key, metrics in self.model_metrics.items():
                    if model_key != current_model:
                        score = self._calculate_model_score(metrics)
                        if score > best_score:
                            best_model = model_key
                            best_score = score
                
                if best_model != current_model:
                    optimization_results[companion_name] = {
                        "current_model": current_model,
                        "recommended_model": best_model,
                        "improvement_score": best_score - self._calculate_model_score(current_metrics)
                    }
            
            return optimization_results
            
        except Exception as e:
            logging.error(f"Error optimizing model assignments: {e}")
            return {"error": str(e)}
    
    def _calculate_model_score(self, metrics: ModelPerformanceMetrics) -> float:
        """Calculate performance score for a model"""
        try:
            # Weighted score based on success rate, response time, and cost efficiency
            success_weight = 0.4
            speed_weight = 0.3
            cost_weight = 0.3
            
            success_score = metrics.success_rate
            speed_score = max(0, 100 - (metrics.avg_response_time * 10))  # Lower response time = higher score
            cost_score = max(0, 100 - (metrics.total_cost / max(1, metrics.total_requests) * 1000))  # Lower cost = higher score
            
            return (success_score * success_weight + 
                   speed_score * speed_weight + 
                   cost_score * cost_weight)
            
        except Exception as e:
            logging.error(f"Error calculating model score: {e}")
            return 0.0


# Global instance (will be initialized with database in app.py)
ai_manager = None


def init_ai_model_manager(db_manager=None):
    """Initialize AI model manager with database"""
    global ai_manager
    ai_manager = AIModelManager(db_manager)
    logging.info("AI Model Manager initialized with enhanced features")
    return ai_manager
