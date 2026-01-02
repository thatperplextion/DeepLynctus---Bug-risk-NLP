"""
Validators
Input validation functions
"""

import re
from typing import Optional


def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_password(password: str) -> tuple[bool, Optional[str]]:
    """
    Validate password strength
    
    Returns:
        (is_valid, error_message)
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters"
    
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r'[0-9]', password):
        return False, "Password must contain at least one number"
    
    return True, None


def validate_url(url: str) -> bool:
    """Validate URL format"""
    pattern = r'https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&\/=]*)'
    return bool(re.match(pattern, url))


def validate_project_id(project_id: str) -> bool:
    """Validate project ID format"""
    # Must be alphanumeric with underscores, 3-50 characters
    pattern = r'^[a-zA-Z0-9_]{3,50}$'
    return bool(re.match(pattern, project_id))


def validate_risk_score(score: float) -> bool:
    """Validate risk score is between 0 and 1"""
    return 0.0 <= score <= 1.0


def validate_severity(severity: str) -> bool:
    """Validate severity level"""
    valid_severities = ['low', 'medium', 'high', 'critical']
    return severity.lower() in valid_severities


def sanitize_input(text: str) -> str:
    """Sanitize user input to prevent injection attacks"""
    # Remove dangerous characters
    dangerous_patterns = [
        r'<script[^>]*>.*?</script>',  # XSS
        r'javascript:',  # JavaScript protocol
        r'on\w+\s*=',  # Event handlers
        r'<iframe',  # Iframes
        r'eval\(',  # Eval
    ]
    
    for pattern in dangerous_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    
    return text.strip()


def validate_file_path(path: str) -> bool:
    """Validate file path doesn't contain directory traversal"""
    # Check for directory traversal attempts
    dangerous_patterns = ['..',  '~/', '//']
    return not any(pattern in path for pattern in dangerous_patterns)


def validate_file_size(size_bytes: int, max_size_mb: int = 100) -> bool:
    """Validate file size is within limits"""
    max_bytes = max_size_mb * 1024 * 1024
    return 0 < size_bytes <= max_bytes
