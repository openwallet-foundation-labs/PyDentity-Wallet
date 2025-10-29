"""Device detection utilities"""
from flask import request


def is_mobile():
    """
    Detect if the request is from a mobile device.
    Returns True for mobile/tablet devices, False for desktop browsers.
    """
    user_agent = request.headers.get('User-Agent', '').lower()
    
    # Mobile device indicators
    mobile_indicators = [
        'mobile', 'android', 'iphone', 'ipad', 'ipod',
        'blackberry', 'windows phone', 'webos',
        'opera mini', 'opera mobi'
    ]
    
    # Check if any mobile indicator is in the user agent
    return any(indicator in user_agent for indicator in mobile_indicators)


def get_device_type():
    """
    Get the device type as a string.
    Returns 'mobile', 'tablet', or 'desktop'.
    """
    user_agent = request.headers.get('User-Agent', '').lower()
    
    if 'ipad' in user_agent or 'tablet' in user_agent:
        return 'tablet'
    elif is_mobile():
        return 'mobile'
    else:
        return 'desktop'

