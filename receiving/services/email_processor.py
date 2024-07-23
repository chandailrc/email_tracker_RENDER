# receiving/services/email_processor.py

import email
from email.utils import parseaddr
from ..models import ReceivedEmail, Attachment
from sending.models import Email as SentEmail
from django.utils import timezone

def process_incoming_email(raw_email, is_webhook=True):
    if is_webhook:
        msg = email.message_from_bytes(raw_email)
    else:
        msg = raw_email  # For IMAP-fetched emails, raw_email is already an email.message object

    # Extract email details
    sender = parseaddr(msg['From'])[1]
    recipients = [parseaddr(addr)[1] for addr in msg.get_all('To', [])]
    cc = [parseaddr(addr)[1] for addr in msg.get_all('Cc', [])]
    bcc = [parseaddr(addr)[1] for addr in msg.get_all('Bcc', [])]
    subject = msg['Subject']
    message_id = msg['Message-ID']
    in_reply_to = msg['In-Reply-To']

    # Extract body
    body = ""
    html_body = ""
    for part in msg.walk():
        if part.get_content_type() == "text/plain":
            body = part.get_payload(decode=True).decode()
        elif part.get_content_type() == "text/html":
            html_body = part.get_payload(decode=True).decode()

    # Create ReceivedEmail instance
    received_email = ReceivedEmail.objects.create(
        sender=sender,
        recipients=recipients,
        cc=cc,
        bcc=bcc,
        subject=subject,
        body=body,
        html_body=html_body,
        message_id=message_id,
        headers=dict(msg.items()),
        received_at=timezone.now()
    )

    # Link to original sent email if it's a reply
    if in_reply_to:
        try:
            original_sent_email = SentEmail.objects.get(message_id=in_reply_to)
            received_email.original_sent_email = original_sent_email
            received_email.save()
        except SentEmail.DoesNotExist:
            pass

    # Process attachments
    for part in msg.walk():
        if part.get_content_maintype() == 'multipart':
            continue
        if part.get('Content-Disposition') is None:
            continue

        filename = part.get_filename()
        if filename:
            content_type = part.get_content_type()
            size = len(part.get_payload(decode=True))
            
            attachment = Attachment.objects.create(
                email=received_email,
                filename=filename,
                content_type=content_type,
                size=size
            )
            attachment.file.save(filename, part.get_payload(decode=True))

    return received_email

def process_imap_email(email_message):
    # This function is called by the email_fetcher when processing IMAP emails
    return process_incoming_email(email_message, is_webhook=False)