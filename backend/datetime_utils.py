#!/usr/bin/env python3
"""
DateTime Utilities for SoulBridge AI
Provides consistent ISO Z datetime serialization to prevent frontend parsing issues
"""

from datetime import datetime, timezone
from typing import Optional, Union
import logging

logger = logging.getLogger(__name__)

def iso_z(dt: Optional[Union[datetime, str]]) -> Optional[str]:
    """
    Convert datetime to ISO Z format for frontend compatibility
    
    Fixes the "2025-08-20 07:55:06.745360+00:00Z" → "2025-08-20T07:55:06Z" issue
    
    Args:
        dt: datetime object, string, or None
        
    Returns:
        ISO Z formatted string like "2025-08-20T07:55:06Z" or None
        
    Examples:
        iso_z(datetime.now()) → "2025-08-20T07:55:06Z" 
        iso_z(None) → None
        iso_z("2025-08-20 07:55:06.745360+00:00") → "2025-08-20T07:55:06Z"
    """
    if dt is None:
        return None
    
    # Handle string input (convert to datetime first)
    if isinstance(dt, str):
        try:
            # Common formats we might receive
            dt = dt.strip()
            if 'T' not in dt and ' ' in dt:
                dt = dt.replace(' ', 'T')
            if dt.endswith('+00:00Z'):
                dt = dt[:-7] + 'Z'
            if dt.endswith('+00:00'):
                dt = dt[:-6] + 'Z'
            
            # Parse the cleaned string
            if dt.endswith('Z'):
                dt = datetime.fromisoformat(dt[:-1] + '+00:00')
            else:
                dt = datetime.fromisoformat(dt)
        except (ValueError, AttributeError) as e:
            logger.warning(f"⚠️ Failed to parse datetime string '{dt}': {e}")
            return None
    
    # Ensure we have a datetime object
    if not isinstance(dt, datetime):
        logger.warning(f"⚠️ Expected datetime, got {type(dt)}: {dt}")
        return None
    
    # Ensure timezone info (assume UTC if naive)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    
    # Format as ISO Z (no microseconds, clean format)
    return dt.strftime('%Y-%m-%dT%H:%M:%SZ')

def parse_iso_z(iso_string: Optional[str]) -> Optional[datetime]:
    """
    Parse ISO Z string back to datetime object
    
    Args:
        iso_string: ISO Z formatted string like "2025-08-20T07:55:06Z"
        
    Returns:
        datetime object in UTC or None
    """
    if not iso_string:
        return None
    
    try:
        # Handle both Z and +00:00 formats
        if iso_string.endswith('Z'):
            return datetime.fromisoformat(iso_string[:-1] + '+00:00')
        else:
            return datetime.fromisoformat(iso_string)
    except (ValueError, AttributeError) as e:
        logger.warning(f"⚠️ Failed to parse ISO Z string '{iso_string}': {e}")
        return None

def utc_now() -> datetime:
    """Get current UTC datetime"""
    return datetime.now(timezone.utc)

def utc_now_z() -> str:
    """Get current UTC datetime as ISO Z string"""
    return iso_z(utc_now())

# Convenience aliases
now_z = utc_now_z
now_utc = utc_now