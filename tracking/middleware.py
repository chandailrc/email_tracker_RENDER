import logging
import ipaddress
from collections import defaultdict
from time import time
from user_agents import parse

logger = logging.getLogger('tracking')  # Use the custom tracking logger

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

SUSPICIOUS_KEYWORDS = ['security', 'scanner', 'filter', 'proxy', 'agent']

REQUEST_LOG = defaultdict(lambda: {'count': 0, 'timestamp': time()})

TIME_WINDOW = 60  # seconds

def is_prefetch_ip(ip_address):
    for ip_range in KNOWN_PREFETCH_IP_RANGES:
        if ipaddress.ip_address(ip_address) in ipaddress.ip_network(ip_range):
            return True
    return False

def extract_device_fingerprint(user_agent):
    ua = parse(user_agent)
    browser_info = f"{ua.browser.family} {ua.browser.version_string}"
    os_info = f"{ua.os.family} {ua.os.version_string}"
    device_type = 'Mobile' if ua.is_mobile else 'Tablet' if ua.is_tablet else 'Desktop'
    return browser_info, os_info, device_type

class TrackingPixelMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if 'pixel' in request.path:
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            ip_address = request.META.get('REMOTE_ADDR', '')
            headers = request.META

            current_time = time()
            ip_info = REQUEST_LOG[ip_address]
            if current_time - ip_info['timestamp'] < TIME_WINDOW:
                ip_info['count'] += 1
            else:
                ip_info['count'] = 1
                ip_info['timestamp'] = current_time

            if ip_info['count'] > 10:  # Example threshold
                self.log_request(request, 'High request rate detected')
                logger.info(f"High request rate - IP: {ip_address}, User-Agent: {user_agent}")

            # Extract device fingerprint
            browser_info, os_info, device_type = extract_device_fingerprint(user_agent)

            if any(ua in user_agent for ua in KNOWN_PREFETCH_USER_AGENTS) or ip_address in KNOWN_PREFETCH_IP_RANGES:
                logger.info(f"Prefetch detected - IP: {ip_address}, User-Agent: {user_agent}, Browser: {browser_info}, OS: {os_info}, Device: {device_type}")
            elif any(keyword in user_agent.lower() for keyword in SUSPICIOUS_KEYWORDS):
                logger.info(f"Suspicious user agent detected - IP: {ip_address}, User-Agent: {user_agent}, Browser: {browser_info}, OS: {os_info}, Device: {device_type}")
            elif any(keyword in headers.get(key, '').lower() for key in headers for keyword in SUSPICIOUS_KEYWORDS):
                logger.info(f"Suspicious header detected - IP: {ip_address}, User-Agent: {user_agent}, Headers: {headers}, Browser: {browser_info}, OS: {os_info}, Device: {device_type}")
            else:
                logger.info(f"Valid open - IP: {ip_address}, User-Agent: {user_agent}, Browser: {browser_info}, OS: {os_info}, Device: {device_type}")

        response = self.get_response(request)
        return response
