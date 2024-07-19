import uuid
from django.utils import timezone
from datetime import timedelta
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
import re
from .models import Email, Link, TrackingPixelToken
from unsubscribers.models import UnsubscribedUser

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

    base_url = f"{settings.BASE_URL}/api/tracking/track-pixel/{unique_id}"
    pixel_url = f"{base_url}/pixel.png"
    css_url = f"{base_url}/style.css"

    return pixel_url, css_url

def tracked_email_sender(recipient, subject, body):
    if UnsubscribedUser.objects.filter(email=recipient).exists():
        logger.info(f"email_utils.py: Email not sent to {recipient} as they have unsubscribed.")
        return False
    # time.sleep(10)

    try:
        email = Email.objects.create(recipient=recipient, subject=subject, body=body, sent_at=timezone.now(), sender=settings.DEFAULT_FROM_EMAIL)
        #tracking_id = email.id

        logger.info(f"email_utils.py: Email db entry created for {recipient} at {timezone.now()}")
        
        def replace_link(match):
            original_url = match.group(0)
            link = Link.objects.create(email=email, url=original_url)
            tracked_url = f"{settings.BASE_URL}/api/tracking/track-link/{link.id}/"
            return f'<a href="{tracked_url}" style="color: #007bff; text-decoration: none;">{original_url}</a>'
        
        tracked_body = re.sub(r'http[s]?:\/\/[^\s]*', replace_link, body)
        html_body = tracked_body.replace('\n', '<br>')  # Convert newlines to <br> tags
        pixel_url, css_url = generate_tracking_urls(email)
        visible_image_url = f"{settings.BASE_URL}/api/tracking/serve-image/logo.png"  # Adjust this URL to point to your logo image
        
        email_body = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{subject}</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .logo {{
                    display: block;
                    margin-bottom: 20px;
                }}
                .footer {{
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 1px solid #eeeeee;
                    font-size: 12px;
                    color: #666666;
                }}
                .unsubscribe {{
                    color: #999999;
                    text-decoration: none;
                }}
                .unsubscribe:hover {{
                    text-decoration: underline;
                }}
            </style>
        </head>
        <body>
            <img src="{pixel_url}" alt="" width="1px" height="1px">
            <img src="{visible_image_url}" alt="Company Logo" width="44" height="55" class="logo">
            <div>{html_body}</div>
            <div class="footer">
                <p>This email was sent to {recipient}. If you no longer wish to receive these emails, you can 
                <a href="{settings.BASE_URL}/frontend/unsubscribe/?email={recipient}" class="unsubscribe">unsubscribe here</a>.</p>
            </div>
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