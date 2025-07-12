import re
import bleach

def sanitize_input(text):
    """Sanitize user input to prevent XSS attacks"""
    if not text:
        return text
    
    # Allow only safe HTML tags
    allowed_tags = []  # No HTML tags allowed in our food app
    allowed_attributes = {}
    
    return bleach.clean(text, tags=allowed_tags, attributes=allowed_attributes, strip=True)

def sanitize_form_data(form_data):
    """Sanitize all form data"""
    sanitized = {}
    for key, value in form_data.items():
        if isinstance(value, str):
            sanitized[key] = sanitize_input(value)
        else:
            sanitized[key] = value
    return sanitized

def validate_email(email):
    """Basic email validation"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_username(username):
    """Validate username format"""
    if not username:
        return False
    
    # Username must be 3-20 characters, alphanumeric and underscore only
    pattern = r'^[a-zA-Z0-9_]{3,20}$'
    return re.match(pattern, username) is not None