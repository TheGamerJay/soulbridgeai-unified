"""
Smart Companion Router
Routes requests between OpenAI GPT and Local AI based on plan, budget, and preferences
"""
import os
import logging
from typing import Dict, Any, Optional
from openai_clients import get_openai_client
from local_clients import get_local_client, get_hybrid_local_client  
from limits import bump_and_check, get_usage
from studio.cache import get_cached_response, cache_response
from billing.openai_budget import check_budget_safe, get_budget_status, get_budget_window_info
from billing.auto_quota import get_quota_for_plan, auto_quota_tokens
from billing.costing import estimate_cost, add_spend

logger = logging.getLogger(__name__)

class CompanionRouter:
    """Smart router for companion AI requests"""
    
    def __init__(self):
        self.openai_client = get_openai_client()
        self.local_client = get_local_client() 
        self.hybrid_client = get_hybrid_local_client()
        
        # Routing configuration from environment
        self.openai_plans = set(os.getenv("OPENAI_PLANS", "vip,max,pro").split(","))
        self.force_local_plans = set(os.getenv("FORCE_LOCAL_PLANS", "free").split(","))
        self.cache_enabled = os.getenv("CACHE_ENABLED", "true").lower() == "true"
        self.cache_ttl_hours = int(os.getenv("CACHE_TTL_HOURS", "24"))
        
        logger.info(f"Companion router initialized - OpenAI plans: {self.openai_plans}")
    
    def route_request(
        self,
        message: str,
        character: str = "Blayzo",
        context: str = "",
        user_id: str = "anonymous",
        user_plan: str = "free",
        force_provider: Optional[str] = None,  # "openai", "local", or None for auto
        quality_preference: str = "auto"  # "fast", "quality", or "auto"
    ) -> Dict[str, Any]:
        """
        Route companion request to appropriate AI provider
        
        Args:
            message: User message
            character: Character name
            context: Conversation context
            user_id: User identifier
            user_plan: User's subscription plan
            force_provider: Force specific provider (openai/local)
            quality_preference: Quality vs speed preference
            
        Returns:
            Response dict with routing information
        """
        
        # Check cache first if enabled
        if self.cache_enabled:
            cached = get_cached_response(message, character, context, self.cache_ttl_hours)
            if cached:
                cached["cache_hit"] = True
                cached["router_decision"] = "cache"
                logger.info(f"Cache hit for {character} request")
                return cached
        
        # Check quota limits using auto-quota system
        quota_info = get_quota_for_plan(user_plan)
        daily_limit = quota_info["per_user_per_day"]
        used_today, _ = get_usage(user_id, user_plan)
        quota_exceeded = daily_limit > 0 and used_today >= daily_limit
        
        if quota_exceeded:
            return {
                "success": False,
                "error": "quota_exceeded", 
                "message": f"Daily limit of {daily_limit} messages reached. Upgrade your plan for more messages.",
                "used_today": used_today,
                "daily_limit": daily_limit,
                "quota_info": quota_info,
                "router_decision": "quota_blocked"
            }
        
        # Determine provider based on routing logic
        provider = self._determine_provider(user_plan, force_provider, quality_preference)
        
        # Generate response
        if provider == "openai":
            response = self._generate_openai_response(message, character, context, user_plan)
        else:
            response = self._generate_local_response(message, character, context, user_plan, quality_preference)
        
        # Update quota if response was successful
        if response.get("success", False):
            used_today, daily_limit = bump_and_check(user_id, user_plan)
            response["quota_after"] = {"used": used_today, "limit": daily_limit}
            
            # Cache successful responses
            if self.cache_enabled and response.get("success", False):
                cache_response(message, character, response, context)
        
        # Add routing metadata
        response["router_decision"] = provider
        response["cache_hit"] = False
        response["quota_checked"] = True
        
        return response
    
    def _determine_provider(self, user_plan: str, force_provider: Optional[str], quality_preference: str) -> str:
        """Determine which AI provider to use"""
        
        # Honor force provider if specified
        if force_provider == "local":
            return "local"
        elif force_provider == "openai" and self.openai_client.is_available():
            return "openai"
        
        # Check if plan is forced to use local
        if user_plan in self.force_local_plans:
            logger.info(f"Plan {user_plan} forced to local AI")
            return "local"
        
        # Check if plan is eligible for OpenAI
        if user_plan not in self.openai_plans:
            logger.info(f"Plan {user_plan} not eligible for OpenAI")
            return "local"
        
        # Check OpenAI availability and budget
        if not self.openai_client.is_available():
            logger.info("OpenAI not available, routing to local")
            return "local"
        
        # For fast preference, use local even if OpenAI is available
        if quality_preference == "fast":
            logger.info("Fast quality requested, using local AI")
            return "local"
        
        # If we get here, OpenAI is available and plan supports it
        logger.info(f"Routing {user_plan} plan to OpenAI")
        return "openai"
    
    def _generate_openai_response(self, message: str, character: str, context: str, user_plan: str) -> Dict[str, Any]:
        """Generate response using OpenAI with cost tracking"""
        try:
            response = self.openai_client.generate_companion_response(message, character, context, user_plan)
            
            if not response.get("success", False) and response.get("fallback_recommended", False):
                logger.warning("OpenAI failed, falling back to local AI")
                return self._generate_local_response(message, character, context, user_plan, "auto")
            
            # Track actual cost if we have token usage information
            if response.get("success", False) and "tokens_used" in response:
                try:
                    model = response.get("model", "gpt-4o-mini")
                    # For now, estimate 70% input tokens, 30% completion tokens if not detailed
                    total_tokens = response["tokens_used"]
                    prompt_tokens = int(total_tokens * 0.7)
                    completion_tokens = int(total_tokens * 0.3)
                    
                    # Use specific token counts if available (from future OpenAI client enhancement)
                    if "prompt_tokens" in response and "completion_tokens" in response:
                        prompt_tokens = response["prompt_tokens"]
                        completion_tokens = response["completion_tokens"]
                    
                    cost = estimate_cost(model, prompt_tokens, completion_tokens)
                    add_spend(cost)
                    
                    response["cost_tracked"] = cost
                    response["cost_breakdown"] = {
                        "prompt_tokens": prompt_tokens,
                        "completion_tokens": completion_tokens,
                        "model": model
                    }
                    
                    logger.info(f"OpenAI cost tracked: ${cost:.4f} for {total_tokens} tokens")
                    
                except Exception as cost_error:
                    logger.error(f"Error tracking OpenAI cost: {cost_error}")
                    response["cost_tracking_error"] = str(cost_error)
            
            return response
            
        except Exception as e:
            logger.error(f"OpenAI generation error: {e}")
            return self._generate_local_response(message, character, context, user_plan, "auto")
    
    def _generate_local_response(self, message: str, character: str, context: str, user_plan: str, quality_preference: str) -> Dict[str, Any]:
        """Generate response using local AI"""
        try:
            if quality_preference == "fast":
                # Use simple AI directly for faster responses
                return self.local_client.simple_ai.generate_response(message, character, context)
            else:
                # Use full local client with fallbacks
                return self.local_client.generate_companion_response(message, character, context, user_plan)
                
        except Exception as e:
            logger.error(f"Local AI generation error: {e}")
            # Ultimate fallback
            return {
                "success": True,
                "response": f"Hello! I'm {character}, your AI companion. I'm here to support you. What would you like to talk about?",
                "model": "emergency_fallback",
                "character": character,
                "enhancement_level": "fallback"
            }
    
    def get_router_status(self) -> Dict[str, Any]:
        """Get detailed router status and configuration"""
        openai_status = self.openai_client.get_client_status()
        local_status = self.local_client.get_client_status()
        budget_status = get_budget_status()
        budget_window = get_budget_window_info()
        
        # Get auto-quota information
        try:
            auto_quota_info = auto_quota_tokens()
        except Exception as e:
            auto_quota_info = {"error": str(e), "fallback": True}
        
        return {
            "router_config": {
                "openai_plans": list(self.openai_plans),
                "force_local_plans": list(self.force_local_plans), 
                "cache_enabled": self.cache_enabled,
                "cache_ttl_hours": self.cache_ttl_hours
            },
            "providers": {
                "openai": openai_status,
                "local": local_status
            },
            "budget_status": budget_status,
            "budget_window": budget_window,
            "auto_quota": auto_quota_info,
            "routing_available": True
        }
    
    def get_routing_recommendation(self, user_plan: str, user_id: str) -> Dict[str, Any]:
        """Get routing recommendation for a user without making a request"""
        # Get quota info using auto-quota system
        quota_info = get_quota_for_plan(user_plan)
        limit = quota_info["per_user_per_day"]
        used, _ = get_usage(user_id, user_plan)
        quota_ok = limit == 0 or used < limit
        
        if not quota_ok:
            return {
                "recommended_provider": None,
                "reason": "quota_exceeded",
                "quota_status": {"used": used, "limit": limit},
                "quota_info": quota_info
            }
        
        provider = self._determine_provider(user_plan, None, "auto")
        
        return {
            "recommended_provider": provider,
            "reason": f"Plan {user_plan} routing logic",
            "quota_status": {"used": used, "limit": limit},
            "quota_info": quota_info,
            "openai_available": self.openai_client.is_available(),
            "budget_safe": check_budget_safe(),
            "budget_window": get_budget_window_info()
        }

# Global instance
_router_instance = None

def get_companion_router() -> CompanionRouter:
    """Get the companion router instance"""
    global _router_instance
    if _router_instance is None:
        _router_instance = CompanionRouter()
    return _router_instance

if __name__ == "__main__":
    # Test the companion router
    router = get_companion_router()
    
    print("Testing Companion Router...")
    status = router.get_router_status()
    print(f"Router Status: {status}")
    
    print("\n" + "="*50)
    print("Testing routing recommendations...")
    
    test_plans = ["free", "growth", "vip", "max"]
    test_user = "test_user_123"
    
    for plan in test_plans:
        recommendation = router.get_routing_recommendation(plan, test_user)
        print(f"\nPlan '{plan}':")
        print(f"  Recommended: {recommendation['recommended_provider']}")
        print(f"  Reason: {recommendation['reason']}")
    
    print("\n" + "="*50)
    print("Testing actual routing...")
    
    test_message = "I'm feeling a bit overwhelmed today"
    
    # Test different scenarios
    scenarios = [
        {"plan": "free", "force": None, "quality": "auto"},
        {"plan": "vip", "force": None, "quality": "quality"},
        {"plan": "vip", "force": "local", "quality": "fast"},
        {"plan": "max", "force": None, "quality": "auto"}
    ]
    
    for scenario in scenarios:
        print(f"\nScenario: Plan={scenario['plan']}, Force={scenario['force']}, Quality={scenario['quality']}")
        
        response = router.route_request(
            message=test_message,
            character="Blayzo",
            user_id=f"test_{scenario['plan']}",
            user_plan=scenario['plan'],
            force_provider=scenario['force'],
            quality_preference=scenario['quality']
        )
        
        print(f"  Success: {response.get('success', False)}")
        print(f"  Provider: {response.get('router_decision', 'unknown')}")
        print(f"  Cache Hit: {response.get('cache_hit', False)}")
        
        if response.get('success', False):
            print(f"  Response: {response['response'][:60]}...")
            print(f"  Model: {response.get('model', 'unknown')}")
        else:
            print(f"  Error: {response.get('error', 'unknown')}")
            print(f"  Message: {response.get('message', 'No error message')}")
    
    print("\nRouter testing completed!")