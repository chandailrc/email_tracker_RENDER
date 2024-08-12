import re
import uuid
from django.utils import timezone
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.contrib.auth import get_user_model
from email.utils import make_msgid
from smtplib import SMTPRecipientsRefused, SMTPServerDisconnected
from .models import SentEmail
from receiving.models import ReceivedEmail
from unsubscribers.models import UnsubscribedUser
from tracking.tracking_utils import generate_tracking_url
from conversations.email_processor import process_email
from django.core import signing

import logging

logger = logging.getLogger(__name__)

def generate_unsubscribe_link(recipient_email, sender_username):
    encoded_username = signing.dumps(sender_username, salt='email-unsubscribe-link')
    return f"{settings.BASE_URL}/frontend/unsubscribe/?email={recipient_email}&sender={encoded_username}"

def get_visible_image_url():
    return f"{settings.BASE_URL}/api/sending/serve-image/logo.png"

def tracked_email_sender(user_id, recipient, subject, body, cc=None, bcc=None, in_reply_to_id=None):
    User = get_user_model()
    user = User.objects.get(id=user_id)
    if UnsubscribedUser.objects.filter(email=recipient).exists():
        logger.info(f"sending_utils.py: Email not sent to {recipient} as they have unsubscribed.")
        return False, "Recipient has unsubscribed"
    # try:
    message_id = make_msgid(domain=settings.EMAIL_DOMAIN)
    
    if in_reply_to_id:
        in_reply_to = ReceivedEmail.objects.get(user=user, id=in_reply_to_id)
        thread_id = in_reply_to.thread_id# or str(uuid.uuid4())
        if not subject.lower().startswith('re:'):
            subject = f"Re: {in_reply_to.subject}"
    else:
        in_reply_to = None
        thread_id = str(uuid.uuid4())
    
    email = SentEmail.objects.create(
        user=user,
        recipient=recipient,
        cc=','.join(cc) if cc else '',
        bcc=','.join(bcc) if bcc else '',
        subject=subject,
        body=body,
        sent_at=timezone.now(),
        sender=settings.DEFAULT_FROM_EMAIL,
        message_id=message_id,
        thread_id=thread_id,
        in_reply_to=in_reply_to
    )
    logger.info(f"sending_utils.py: Email db entry created for {recipient} at {timezone.now()}")
    
    def replace_link(match):
        original_url = match.group(0)
        tracked_url = generate_tracking_url(email, 'LINK', original_url)
        return f'<a href="{tracked_url}" style="color: #007bff; text-decoration: none;">{original_url}</a>'
    
    tracked_body = re.sub(r'http[s]?:\/\/[^\s]*', replace_link, body)
    html_body = tracked_body.replace('\n', '<br>')  # Convert newlines to <br> tags
    pixel_url = generate_tracking_url(email, 'PIXEL')
    visible_image_url = get_visible_image_url()
    unsub_url = generate_unsubscribe_link(recipient, user.username)
    
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
            <a href="{unsub_url}" class="unsubscribe">unsubscribe here</a>.</p>
        </div>
    </body>
    </html>
    """
    
    msg = EmailMultiAlternatives(
        subject=subject,
        body=tracked_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[recipient],
        cc=cc,
        bcc=bcc,
        headers={'Message-ID': message_id}
    )
    msg.attach_alternative(email_body, "text/html")
    msg.send()
    logger.info(f"sending_utils.py: Email sent successfully to {recipient}")
    
    process_email(email, 'sent', user_id)
    
    return True, "Email sent successfully"
    # except SMTPRecipientsRefused:
    #     logger.error(f"sending_utils.py: Recipient {recipient} refused")
    #     email.delete()
    #     return False, "Recipient email address refused"
    # except SMTPServerDisconnected:
    #     logger.error(f"sending_utils.py: SMTP server disconnected while sending to {recipient}")
    #     email.delete()
    #     return False, "SMTP server disconnected"
    # except Exception as e:
    #     logger.error(f"sending_utils.py: Error sending email to {recipient}: {e}")
    #     email.delete()
    #     return False, f"Error sending email: {str(e)}"