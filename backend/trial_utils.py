"""
Trial utility functions for calculating trial status without database columns
"""
from datetime import datetime, timedelta

def is_trial_active(trial_started_at, trial_used_permanently=False):
    """
    Determine if the 5-hour trial is currently active.
    
    Args:
        trial_started_at (datetime): When the trial started
        trial_used_permanently (bool): If the trial was used permanently
        
    Returns:
        bool: True if trial is currently active
    """
    if not trial_started_at or trial_used_permanently:
        return False
    
    elapsed = datetime.utcnow() - trial_started_at
    return elapsed.total_seconds() < 5 * 3600  # 5 hours

def get_trial_time_remaining(trial_started_at):
    """
    Get remaining trial time in seconds.
    
    Args:
        trial_started_at (datetime): When the trial started
        
    Returns:
        int: Seconds remaining (0 if expired)
    """
    if not trial_started_at:
        return 0
        
    elapsed = datetime.utcnow() - trial_started_at
    total_seconds = 5 * 3600  # 5 hours
    remaining = total_seconds - elapsed.total_seconds()
    
    return max(0, int(remaining))