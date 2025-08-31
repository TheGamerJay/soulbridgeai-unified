"""
SoulBridge AI - Page Renderer
Handles template rendering and page context for core routes
Extracted from monolith app.py with improvements
"""
import logging
from typing import Dict, Any, Optional
from flask import render_template, session

logger = logging.getLogger(__name__)

class PageRenderer:
    """Handles page rendering with proper context and data"""
    
    def __init__(self):
        self.template_cache = {}
        
    def render_intro_page(self) -> str:
        """Render the intro/welcome page"""
        try:
            # Get user context
            user_context = self._get_user_context()
            
            # Get navigation menu
            from .navigation_service import NavigationService
            nav_service = NavigationService()
            navigation = nav_service.get_navigation_menu()
            
            # Get dashboard data
            dashboard_data = nav_service.get_user_dashboard_data()
            
            return render_template('intro.html',
                                 user_context=user_context,
                                 navigation=navigation,
                                 dashboard_data=dashboard_data,
                                 page_title="Welcome to SoulBridge AI")
            
        except Exception as e:
            logger.error(f"Error rendering intro page: {e}")
            return render_template('error.html', error="Failed to load welcome page")
    
    def render_login_page(self, error_message: Optional[str] = None, 
                         return_to: Optional[str] = None) -> str:
        """Render the login page"""
        try:
            return render_template('login.html',
                                 error=error_message,
                                 return_to=return_to,
                                 page_title="Login - SoulBridge AI")
            
        except Exception as e:
            logger.error(f"Error rendering login page: {e}")
            return f"<h1>Login Error</h1><p>{str(e)}</p>"
    
    def render_register_page(self, error_message: Optional[str] = None) -> str:
        """Render the registration page"""
        try:
            return render_template('register.html',
                                 error=error_message,
                                 page_title="Register - SoulBridge AI")
            
        except Exception as e:
            logger.error(f"Error rendering register page: {e}")
            return f"<h1>Registration Error</h1><p>{str(e)}</p>"
    
    def render_terms_acceptance_page(self) -> str:
        """Render the terms acceptance page"""
        try:
            # Get latest terms
            from ..legal.terms_service import TermsService
            terms_service = TermsService()
            terms_data = terms_service.get_current_terms()
            
            return render_template('terms_acceptance.html',
                                 terms_data=terms_data,
                                 page_title="Accept Terms - SoulBridge AI")
            
        except Exception as e:
            logger.error(f"Error rendering terms page: {e}")
            return render_template('error.html', error="Failed to load terms page")
    
    def render_error_page(self, error_message: str, status_code: int = 500) -> str:
        """Render error page with proper context"""
        try:
            user_context = self._get_user_context()
            
            return render_template('error.html',
                                 error=error_message,
                                 status_code=status_code,
                                 user_context=user_context,
                                 page_title=f"Error {status_code} - SoulBridge AI")
            
        except Exception as e:
            logger.error(f"Error rendering error page: {e}")
            return f"<h1>Error {status_code}</h1><p>{error_message}</p><p>Additional error: {str(e)}</p>"
    
    def render_tier_lock_page(self, feature_name: str, required_tier: str) -> str:
        """Render tier lock/upgrade page"""
        try:
            user_context = self._get_user_context()
            
            tier_info = {
                "feature": feature_name,
                "required_tier": required_tier,
                "current_tier": user_context.get('user_plan', 'bronze'),
                "trial_active": user_context.get('trial_active', False)
            }
            
            return render_template('tier_lock_demo.html',
                                 tier_info=tier_info,
                                 user_context=user_context,
                                 page_title=f"{feature_name} - Upgrade Required")
            
        except Exception as e:
            logger.error(f"Error rendering tier lock page: {e}")
            return render_template('error.html', error="Feature requires upgrade")
    
    def render_subscription_page(self, feature: Optional[str] = None) -> str:
        """Render subscription/upgrade page"""
        try:
            user_context = self._get_user_context()
            
            # Get subscription options and pricing
            subscription_data = {
                "feature_requested": feature,
                "current_plan": user_context.get('user_plan', 'bronze'),
                "trial_active": user_context.get('trial_active', False),
                "pricing": self._get_pricing_info(),
                "features_comparison": self._get_features_comparison()
            }
            
            return render_template('subscription.html',
                                 subscription_data=subscription_data,
                                 user_context=user_context,
                                 page_title="Upgrade Your Plan - SoulBridge AI")
            
        except Exception as e:
            logger.error(f"Error rendering subscription page: {e}")
            return render_template('error.html', error="Failed to load subscription page")
    
    def _get_user_context(self) -> Dict[str, Any]:
        """Get user context for template rendering"""
        try:
            if not session.get('user_authenticated'):
                return {"authenticated": False}
            
            return {
                "authenticated": True,
                "user_id": session.get('user_id'),
                "user_email": session.get('user_email'),
                "user_plan": session.get('user_plan', 'bronze'),
                "trial_active": session.get('trial_active', False),
                "referrals": session.get('referrals', 0),
                "credits": session.get('artistic_time', 0)
            }
            
        except Exception as e:
            logger.error(f"Error getting user context: {e}")
            return {"authenticated": False}
    
    def _get_pricing_info(self) -> Dict[str, Any]:
        """Get pricing information for subscription page"""
        return {
            "silver": {
                "monthly": "$12.99",
                "yearly": "$117.00",
                "savings": "25%"
            },
            "gold": {
                "monthly": "$19.99", 
                "yearly": "$180.00",
                "savings": "25%"
            },
            "trial": {
                "duration": "5 hours",
                "credits": 60,
                "description": "Try Silver & Gold features"
            }
        }
    
    def _get_features_comparison(self) -> Dict[str, Any]:
        """Get features comparison for subscription page"""
        return {
            "bronze": {
                "name": "Bronze",
                "price": "Free",
                "features": ["3 daily decoder uses", "2 daily fortune uses", "3 daily horoscope uses", "Basic AI companions", "Ads supported"]
            },
            "silver": {
                "name": "Silver", 
                "price": "$12.99/month",
                "features": ["15 daily decoder uses", "8 daily fortune uses", "10 daily horoscope uses", "Premium AI companions", "Analytics dashboard", "AI image creation", "Voice journaling", "Meditations", "No ads"]
            },
            "gold": {
                "name": "Gold",
                "price": "$19.99/month", 
                "features": ["Unlimited daily uses", "All premium companions", "Voice chat", "Mini Studio", "Priority support", "All Silver features", "No ads"]
            }
        }