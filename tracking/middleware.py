# tracking/middleware.py
import logging
import ipaddress

logger = logging.getLogger(__name__)

KNOWN_PREFETCH_USER_AGENTS = [
    'Proofpoint', 'Barracuda', 'Mimecast', 'Symantec', 'GoogleImageProxy', 'Outlook', 'YMail'
]

KNOWN_PREFETCH_IP_RANGES = [
    # Proofpoint
    '67.231.152.0/24', '67.231.153.0/24', '67.231.154.0/24', '67.231.155.0/24', '67.231.156.0/24',
    # Barracuda
    '64.235.144.0/20', '209.222.80.0/21',
    # Mimecast
    '205.139.110.0/24', '91.220.42.0/24', '91.220.43.0/24',
    # Symantec (Broadcom)
    '208.65.144.0/24', '208.65.145.0/24', '208.65.146.0/24', '208.65.147.0/24',
    # GoogleImageProxy
    '66.102.0.0/20', '74.125.0.0/16', '64.233.160.0/19', '66.249.80.0/20', '72.14.192.0/18',
    # Outlook
    '40.92.0.0/15', '40.107.0.0/16', '52.100.0.0/14', '104.47.0.0/17',
    # Yahoo
    '67.195.0.0/16', '72.30.0.0/16', '98.136.0.0/14'
]

def is_prefetch_ip(ip_address):
    for ip_range in KNOWN_PREFETCH_IP_RANGES:
        if ipaddress.ip_address(ip_address) in ipaddress.ip_network(ip_range):
            return True
    return False

class TrackingPixelMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if 'pixel' in request.path:  # Assuming your tracking pixel endpoint contains 'pixel'
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            ip_address = request.META.get('REMOTE_ADDR', '')
            
            if any(ua in user_agent for ua in KNOWN_PREFETCH_USER_AGENTS) or is_prefetch_ip(ip_address):
                logger.info(f"Prefetch detected - IP: {ip_address}, User-Agent: {user_agent}")
                # Do not log this as a valid open
            else:
                logger.info(f"Valid open - IP: {ip_address}, User-Agent: {user_agent}")
                # Log this as a valid open
                
        response = self.get_response(request)
        return response
# -*- coding: utf-8 -*-

