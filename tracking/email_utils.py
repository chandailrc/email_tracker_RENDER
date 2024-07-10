import uuid
from django.utils import timezone
from datetime import timedelta
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
import re
from urllib.parse import urlparse
from .models import Email, Link, UnsubscribedUser, TrackingPixelToken
import time

import logging

logger = logging.getLogger(__name__)

def generate_tracking_urls(email):
    unique_id = uuid.uuid4().hex
    expiration = timezone.now() + timedelta(hours=24)  # URL valid for 24 hours

    TrackingPixelToken.objects.create(
        email=email,
        token=unique_id,
        expires_at=expiration
    )

    base_url = f"{settings.BASE_URL}/track/{unique_id}"
    pixel_url = f"{base_url}/pixel.png"
    css_url = f"{base_url}/style.css"

    return pixel_url, css_url

def send_tracked_email(recipient, subject, body):
    if UnsubscribedUser.objects.filter(email=recipient).exists():
        logger.info(f"email_utils.py: Email not sent to {recipient} as they have unsubscribed.")
        return False
    # time.sleep(10)

    try:
        email = Email.objects.create(recipient=recipient, subject=subject, body=body, sent_at=timezone.now())
        #tracking_id = email.id

        logger.info(f"email_utils.py: Email db entry created for {recipient} at {timezone.now()}")

        def replace_link(match):
            original_url = match.group(0)
            parsed_url = urlparse(original_url)
            link = Link.objects.create(email=email, url=original_url)
            tracked_url = f"{settings.BASE_URL}/track-link/{link.id}/"
            return f'<a href="{tracked_url}">Link</a>'

        tracked_body = re.sub(r'http[s]?:\/\/[^\s]*', replace_link, body)
        html_body = tracked_body.replace('\n', '<br>')  # Convert newlines to <br> tags

        pixel_url, css_url = generate_tracking_urls(email)

        email_body = f"""
            <html>
              <head>
              </head>
              <body>
                <img src="{pixel_url}" alt="" width="1" height="1" style="display:none;">
                <p>{html_body}</p>
                <p>If you wish to unsubscribe, click <a href="{settings.BASE_URL}/unsubscribe/?email={recipient}">here</a>.</p>
              </body>
            </html>
        """

        msg = EmailMultiAlternatives(
            subject=subject,
            body=tracked_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[recipient]
        )
        msg.attach_alternative(email_body, "text/html")
        msg.send()

        logger.info(f"email_utils.py: Email sent successfully to {recipient}")
        return True

    except Exception as e:
        logger.error(f"email_utils.py: Error sending email to {recipient}: {e}")
        email.delete()  # Remove the database entry if email sending fails
        return False