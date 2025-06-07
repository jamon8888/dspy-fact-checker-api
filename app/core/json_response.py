"""
Custom JSON response utilities for handling datetime and other complex objects.
"""

import json
from datetime import datetime, date, time
from decimal import Decimal
from uuid import UUID
from enum import Enum
from fastapi.responses import JSONResponse
from typing import Any, Dict, Optional


class CustomJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle datetime, decimal, UUID, and enum objects."""
    
    def default(self, obj):
        """Convert objects to JSON-serializable format."""
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, date):
            return obj.isoformat()
        elif isinstance(obj, time):
            return obj.isoformat()
        elif isinstance(obj, Decimal):
            return float(obj)
        elif isinstance(obj, UUID):
            return str(obj)
        elif isinstance(obj, Enum):
            return obj.value
        elif hasattr(obj, '__dict__'):
            # Handle custom objects with __dict__
            return obj.__dict__
        return super().default(obj)


def create_json_response(
    content: Any, 
    status_code: int = 200, 
    headers: Optional[Dict[str, str]] = None
) -> JSONResponse:
    """
    Create a JSONResponse with custom encoder for datetime and other objects.
    
    Args:
        content: The content to serialize
        status_code: HTTP status code
        headers: Optional headers
        
    Returns:
        JSONResponse with properly serialized content
    """
    try:
        # Serialize with custom encoder
        json_content = json.dumps(content, cls=CustomJSONEncoder, ensure_ascii=False)
        # Parse back to ensure it's valid JSON
        parsed_content = json.loads(json_content)
        
        return JSONResponse(
            content=parsed_content,
            status_code=status_code,
            headers=headers
        )
    except Exception as e:
        # Fallback for serialization errors
        fallback_content = {
            "error": "Serialization error",
            "message": str(e),
            "original_type": str(type(content).__name__)
        }
        return JSONResponse(
            content=fallback_content,
            status_code=500,
            headers=headers
        )


def safe_json_dumps(obj: Any) -> str:
    """
    Safely serialize an object to JSON string.
    
    Args:
        obj: Object to serialize
        
    Returns:
        JSON string
    """
    try:
        return json.dumps(obj, cls=CustomJSONEncoder, ensure_ascii=False)
    except Exception as e:
        return json.dumps({
            "error": "Serialization failed",
            "message": str(e),
            "type": str(type(obj).__name__)
        })


def is_json_serializable(obj: Any) -> bool:
    """
    Check if an object is JSON serializable with our custom encoder.
    
    Args:
        obj: Object to check
        
    Returns:
        True if serializable, False otherwise
    """
    try:
        json.dumps(obj, cls=CustomJSONEncoder)
        return True
    except (TypeError, ValueError):
        return False
