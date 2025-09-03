"""
SoulBridge AI - Standardized API Response Format
Based on clean SDK patterns for consistent API responses
"""
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
import json

class ResponseStatus(Enum):
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"

@dataclass
class APIResponse:
    """Standardized API response structure"""
    success: bool
    data: Optional[Union[Dict[str, Any], List[Any], str, int, float]] = None
    error: Optional[str] = None
    message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    timestamp: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON response"""
        result = {
            "success": self.success,
            "timestamp": self.timestamp
        }
        
        if self.data is not None:
            result["data"] = self.data
        if self.error is not None:
            result["error"] = self.error
        if self.message is not None:
            result["message"] = self.message
        if self.metadata is not None:
            result["metadata"] = self.metadata
            
        return result
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), default=str)

# Factory functions for common response patterns
def success_response(
    data: Any = None, 
    message: str = None, 
    metadata: Dict[str, Any] = None
) -> APIResponse:
    """Create successful API response"""
    return APIResponse(
        success=True,
        data=data,
        message=message,
        metadata=metadata
    )

def error_response(
    error: str,
    message: str = None,
    metadata: Dict[str, Any] = None
) -> APIResponse:
    """Create error API response"""
    return APIResponse(
        success=False,
        error=error,
        message=message,
        metadata=metadata
    )

def paginated_response(
    items: List[Any],
    page: int = 1,
    per_page: int = 20,
    total: int = None,
    message: str = None
) -> APIResponse:
    """Create paginated API response"""
    total = total or len(items)
    has_next = (page * per_page) < total
    has_prev = page > 1
    
    return APIResponse(
        success=True,
        data={
            "items": items,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total,
                "has_next": has_next,
                "has_prev": has_prev,
                "total_pages": (total + per_page - 1) // per_page
            }
        },
        message=message
    )

def library_content_response(
    content_items: List[Dict[str, Any]],
    user_tier: str,
    total_items: int = None
) -> APIResponse:
    """Create library content response with user context"""
    return APIResponse(
        success=True,
        data={
            "content_items": content_items,
            "count": len(content_items)
        },
        metadata={
            "user_tier": user_tier,
            "total_library_items": total_items or len(content_items),
            "content_types": list(set(item.get("content_type") for item in content_items))
        }
    )

def feature_usage_response(
    feature: str,
    usage_today: int,
    daily_limit: int,
    remaining: int,
    unlimited: bool = False
) -> APIResponse:
    """Create feature usage response"""
    return APIResponse(
        success=True,
        data={
            "feature": feature,
            "usage_today": usage_today,
            "daily_limit": daily_limit,
            "remaining": remaining,
            "unlimited": unlimited,
            "can_use": remaining > 0 or unlimited
        }
    )

def auto_save_response(
    main_response_data: Any,
    auto_saved: bool,
    library_id: Optional[int] = None
) -> APIResponse:
    """Enhance any response with auto-save information"""
    metadata = {
        "auto_saved": auto_saved,
        "saved_message": "✅ Automatically saved to your library" if auto_saved else ""
    }
    
    if library_id:
        metadata["library_id"] = library_id
    
    return APIResponse(
        success=True,
        data=main_response_data,
        metadata=metadata
    )

# Response validation and sanitization
def sanitize_response_data(data: Any) -> Any:
    """Sanitize response data to ensure JSON serialization"""
    if isinstance(data, dict):
        return {k: sanitize_response_data(v) for k, v in data.items()}
    elif isinstance(data, (list, tuple)):
        return [sanitize_response_data(item) for item in data]
    elif isinstance(data, datetime):
        return data.isoformat()
    elif hasattr(data, 'to_dict'):
        return sanitize_response_data(data.to_dict())
    elif hasattr(data, '__dict__'):
        return sanitize_response_data(data.__dict__)
    else:
        return data