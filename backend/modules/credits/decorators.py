"""
SoulBridge AI - Credit Decorators
Decorators for enforcing artistic time credit requirements
"""
import logging
from functools import wraps
from flask import session, jsonify, request, current_app
from .operations import get_artistic_time, deduct_artistic_time
from .constants import ARTISTIC_TIME_COSTS

logger = logging.getLogger(__name__)

def require_credits(feature_name, custom_cost=None, allow_insufficient=False):
    """
    Decorator to require artistic time credits for a feature
    
    Args:
        feature_name (str): Name of the feature (must match ARTISTIC_TIME_COSTS keys)
        custom_cost (int): Override default cost for this specific usage
        allow_insufficient (bool): Allow execution even with insufficient credits (for free features)
    
    Returns:
        Flask response or continues to decorated function
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                # Get user ID from session
                user_id = session.get('user_id')
                if not user_id:
                    return jsonify({
                        'error': 'Authentication required',
                        'redirect': '/login'
                    }), 401
                
                # Determine cost
                cost = custom_cost if custom_cost is not None else ARTISTIC_TIME_COSTS.get(feature_name, 0)
                
                # If free feature, continue without checks
                if cost == 0:
                    return f(*args, **kwargs)
                
                # Check current balance
                current_balance = get_artistic_time(user_id)
                
                # Log credit check
                logger.info(f"Credit check for user {user_id}: {feature_name} costs {cost}, balance: {current_balance}")
                
                # If insufficient credits and not allowed
                if current_balance < cost and not allow_insufficient:
                    return jsonify({
                        'error': 'Insufficient credits',
                        'feature': feature_name,
                        'cost': cost,
                        'balance': current_balance,
                        'needed': cost - current_balance,
                        'upgrade_required': True
                    }), 402  # Payment Required
                
                # Deduct credits before executing
                if current_balance >= cost:
                    success = deduct_artistic_time(user_id, cost)
                    if not success:
                        return jsonify({
                            'error': 'Failed to deduct credits',
                            'feature': feature_name,
                            'cost': cost
                        }), 500
                    
                    # Add credit info to response context
                    balance_after = get_artistic_time(user_id)
                    logger.info(f"Credits deducted for user {user_id}: {feature_name} (-{cost}), new balance: {balance_after}")
                
                # Execute the original function
                response = f(*args, **kwargs)
                
                # If response is a tuple (response, status_code), modify the response
                if isinstance(response, tuple) and len(response) >= 2:
                    response_data, status_code = response[0], response[1]
                    if hasattr(response_data, 'json') and response_data.json:
                        # Add credit info to JSON response
                        response_json = response_data.get_json()
                        if isinstance(response_json, dict):
                            response_json['credits'] = {
                                'charged': cost,
                                'remaining': get_artistic_time(user_id)
                            }
                            return jsonify(response_json), status_code
                
                # For regular JSON responses
                if hasattr(response, 'json') and response.json:
                    response_json = response.get_json()
                    if isinstance(response_json, dict):
                        response_json['credits'] = {
                            'charged': cost,
                            'remaining': get_artistic_time(user_id)
                        }
                        return jsonify(response_json)
                
                return response
                
            except Exception as e:
                logger.error(f"Error in credit decorator for {feature_name}: {e}")
                return jsonify({
                    'error': 'Credit system error',
                    'message': str(e)
                }), 500
        
        return decorated_function
    return decorator

def check_credits_only(feature_name, custom_cost=None):
    """
    Decorator to only check credits without deducting (for preview/validation)
    
    Args:
        feature_name (str): Name of the feature
        custom_cost (int): Override default cost
    
    Returns:
        Adds credit info to response, continues execution
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                user_id = session.get('user_id')
                if not user_id:
                    return jsonify({
                        'error': 'Authentication required',
                        'redirect': '/login'
                    }), 401
                
                # Determine cost and balance
                cost = custom_cost if custom_cost is not None else ARTISTIC_TIME_COSTS.get(feature_name, 0)
                current_balance = get_artistic_time(user_id)
                
                # Execute function
                response = f(*args, **kwargs)
                
                # Add credit info to response
                if hasattr(response, 'json') and response.json:
                    response_json = response.get_json()
                    if isinstance(response_json, dict):
                        response_json['credits'] = {
                            'cost': cost,
                            'balance': current_balance,
                            'can_afford': current_balance >= cost
                        }
                        return jsonify(response_json)
                
                return response
                
            except Exception as e:
                logger.error(f"Error in credit check decorator for {feature_name}: {e}")
                return f(*args, **kwargs)  # Continue on error
        
        return decorated_function
    return decorator

def credit_info(f):
    """
    Simple decorator to add current credit balance to any response
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            response = f(*args, **kwargs)
            
            user_id = session.get('user_id')
            if user_id:
                current_balance = get_artistic_time(user_id)
                
                if hasattr(response, 'json') and response.json:
                    response_json = response.get_json()
                    if isinstance(response_json, dict):
                        response_json['user_credits'] = current_balance
                        return jsonify(response_json)
            
            return response
            
        except Exception as e:
            logger.error(f"Error adding credit info: {e}")
            return f(*args, **kwargs)  # Continue on error
    
    return decorated_function