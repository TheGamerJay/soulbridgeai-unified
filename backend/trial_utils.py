"""
Trial utility functions for calculating trial status without database columns
"""
from datetime import datetime, timedelta
from constants import TRIAL_DURATION_HOURS, TRIAL_DURATION_SECONDS

def is_trial_active(trial_started_at, trial_used_permanently=False):
    """
    Determine if the trial is currently active.
    
    Args:
        trial_started_at (datetime): When the trial started
        trial_used_permanently (bool): If the trial was used permanently
        
    Returns:
        bool: True if trial is currently active
    """
    if not trial_started_at:
        return False
    
    # If trial was used permanently, it means they started the trial
    # Check if it's still within the trial duration window
    elapsed = datetime.utcnow() - trial_started_at
    return elapsed.total_seconds() < TRIAL_DURATION_SECONDS

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
    remaining = TRIAL_DURATION_SECONDS - elapsed.total_seconds()
    
    return max(0, int(remaining))