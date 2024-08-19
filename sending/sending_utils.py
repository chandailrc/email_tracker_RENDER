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
from conversations.models import Conversation, ConversationMessage
from unsubscribers.models import UnsubscribedUser
from tracking.tracking_utils import generate_tracking_url
from conversations.email_processor import process_email
from django.core import signing

import logging

logger = logging.getLogger(__name__)

def format_email_history(previous_messages, user_email):
    history = []
    html_history = []
    quote_level = 0

    for msg in reversed(previous_messages):
        sender = msg.sender
        timestamp = msg.timestamp.strftime('%a, %b %d, %Y at %I:%M %p')
        content_plain = msg.content.replace('\n', '\n' + '>' * (quote_level + 1) + ' ')  # Adjusted quoting for plain text
        content_html = msg.content.replace('\n', '<br>' + '>' * (quote_level + 1) + ' ')  # Adjusted HTML version with <br> tags

        opening_blockquotes = "<blockquote>" * quote_level
        closing_blockquotes = "</blockquote>" * quote_level


        if sender != user_email:  # This is a sent email
            header_plain = (f"{'>' * quote_level}________________________________\n"
                      f"{'>' * quote_level}*From:* {sender}\n"
                      f"{'>' * quote_level}*Sent:* {timestamp}\n"
                      f"{'>' * quote_level}*To:* {msg.received_email.recipient}\n"
                      f"{'>' * quote_level}*Subject:* {msg.received_email.subject}\n"
                      )
            
            # Create the email header
            header_html = (
                    f"{opening_blockquotes}"
                    f"<div>________________________________</div>"
                    f"<div><strong>From:</strong> {sender}</div>"
                    f"<div><strong>Sent:</strong> {timestamp}</div>"
                    f"<div><strong>To:</strong> {msg.received_email.recipient}</div>"
                    f"<div><strong>Subject:</strong> {msg.received_email.subject}</div>"
                    f"{closing_blockquotes}"
                    )
        else:  # This is a received email
            header_plain = f"{'>' * quote_level}On {timestamp} {sender} wrote:\n"
            header_html = (f"{opening_blockquotes}"
                           f"{'>' * quote_level}On {timestamp} {sender} wrote:<br>"
                           f"{closing_blockquotes}")
        
        quoted_message_plain = f"{header_plain}\n{'>' * quote_level}{content_plain}"
        quoted_message_html = (f"{header_html}"
                               f"{opening_blockquotes}"
                               f"{content_html}"
                               f"{closing_blockquotes}")

        history.append(quoted_message_plain)
        html_history.append(quoted_message_html)
        quote_level += 1

    plain_history = '\n\n'.join(history)
    html_history = '<br><br>'.join(html_history)  # Ensure correct spacing between messages in HTML

    return plain_history, html_history

def generate_unsubscribe_link(recipient_email, sender_username):
    encoded_username = signing.dumps(sender_username, salt='email-unsubscribe-link')
    return f"{settings.BASE_URL}/frontend/unsubscribe/?email={recipient_email}&sender={encoded_username}"

def get_visible_image_url():
    return f"{settings.BASE_URL}/api/sending/serve-image/logo.png"

def tracked_email_sender(user_id, recipient, subject, body, cc=None, bcc=None, in_reply_to_message_id=None, in_reply_sendOrRec=None):
    User = get_user_model()
    user = User.objects.get(id=user_id)
    if UnsubscribedUser.objects.filter(email=recipient).exists():
        logger.info(f"sending_utils.py: Email not sent to {recipient} as they have unsubscribed.")
        return False, "Recipient has unsubscribed"

    # try:
    message_id = make_msgid(domain=settings.EMAIL_DOMAIN)
    
    if in_reply_to_message_id:
        if in_reply_sendOrRec == 'send': # Whether we are adding to or replying to our own email that we had sent
            # original_email - Email being responded to
            original_email = SentEmail.objects.get(user=user, message_id=in_reply_to_message_id)
        else: # Whether we are responding to an email we have received
            original_email = ReceivedEmail.objects.get(user=user, message_id=in_reply_to_message_id)
        
        thread_id = original_email.thread_id
        
        if not subject.lower().startswith('re:'):
            subject = f"Re: {subject}"
        
        # Fetch the conversation and previous messages
        try:
            conversation = Conversation.objects.get(
                user=user,
                conversationmessage__sent_email__message_id=in_reply_to_message_id
            ) if in_reply_sendOrRec == 'send' else Conversation.objects.get(
                user=user,
                conversationmessage__received_email__message_id=in_reply_to_message_id
            )
            previous_messages = ConversationMessage.objects.filter(
                conversation=conversation
            ).order_by('-timestamp')[:6][::-1]  # Limit to first 5 messages

            # Format the email history with progressive quoting
            
            quoted_history_plain, quoted_history_html = format_email_history(previous_messages, settings.DEFAULT_FROM_EMAIL)

            # Append the history to the new email body
            full_body = f"{body}\n\n\n\n{quoted_history_plain}"
            
            if hasattr(original_email, 'references') and original_email.references:
                references = f"{original_email.references} {in_reply_to_message_id}"
            else:
                references = in_reply_to_message_id
            
        except Conversation.DoesNotExist:
            full_body = body
    else:
        thread_id = str(uuid.uuid4())
        full_body = body
        references = None
        
    headers = {
        'Message-ID': message_id,
        'In-Reply-To': in_reply_to_message_id,
        'References': references
    }
    
    print(f"Message-ID: {message_id}")
    print(f"In-Reply-To: {in_reply_to_message_id}")
    print(f"References: {references}")
    print(f"Thread-ID: {thread_id}")

    email = SentEmail.objects.create(
        user=user,
        recipient=recipient,
        cc=','.join(cc) if cc else '',
        bcc=','.join(bcc) if bcc else '',
        subject=subject,
        body=body,
        full_body=full_body,
        sent_at=timezone.now(),
        sender=settings.DEFAULT_FROM_EMAIL,
        message_id=message_id,
        thread_id=thread_id,
        in_reply_to=in_reply_to_message_id,
        references=references
    )
    logger.info(f"sending_utils.py: Email db entry created for {recipient} at {timezone.now()}")
    
    def replace_link(match):
        original_url = match.group(0)
        tracked_url = generate_tracking_url(email, 'LINK', original_url)
        return f'<a href="{tracked_url}" style="color: #007bff; text-decoration: none;">{original_url}</a>'
    
    tracked_full_body = re.sub(r'http[s]?:\/\/[^\s]*', replace_link, full_body)
    tracked_body = re.sub(r'http[s]?:\/\/[^\s]*', replace_link, body)
    
    html_body = tracked_body.replace('\n', '<br>')
    
    if in_reply_to_message_id:
        full_body_html = f"{html_body}\n\n\n\n{quoted_history_html}"
    else:
        # full_body_html = html_body
        quoted_history_html = ''

    # 
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
        <div class="gmail_quote">{quoted_history_html}</div>
    </body>
    </html>
    """
    
    msg = EmailMultiAlternatives(
        subject=subject,
        body=tracked_full_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[recipient],
        cc=cc,
        bcc=bcc,
        headers=headers
    )
    msg.attach_alternative(email_body, "text/html")
    msg.send()
    logger.info(f"sending_utils.py: Email sent successfully to {recipient}")
    
    process_email(email, 'sent', user_id, in_reply_sendOrRec)
    
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