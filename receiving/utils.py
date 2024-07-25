import imaplib
import email
from django.conf import settings
from .models import ReceivedEmail, Attachment
from sending.models import Email as SentEmail
from django.core.files.base import ContentFile
from email.utils import parseaddr

def fetch_and_process_emails():
    new_emails_count = 0
    with imaplib.IMAP4_SSL(settings.EMAIL_IMAP_SERVER, settings.EMAIL_IMAP_PORT) as mail:
        mail.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
        mail.select('inbox')

        _, search_data = mail.search(None, 'UNSEEN')
        for num in search_data[0].split():
            _, data = mail.fetch(num, '(RFC822)')
            raw_email = data[0][1]
            if process_incoming_email(raw_email):
                new_emails_count += 1

    return new_emails_count

def process_incoming_email(raw_email):
    email_message = email.message_from_bytes(raw_email)
    
    # Extract email details
    sender = parseaddr(email_message['From'])[1]
    recipient = parseaddr(email_message['To'])[1]
    subject = email_message['Subject']
    message_id = email_message['Message-ID']
    in_reply_to = email_message.get('In-Reply-To')
    
    # Check if this email has already been processed
    if ReceivedEmail.objects.filter(message_id=message_id).exists():
        return False

    # Get the email body
    if email_message.is_multipart():
        for part in email_message.walk():
            if part.get_content_type() == "text/plain":
                body = part.get_payload(decode=True).decode()
                break
    else:
        body = email_message.get_payload(decode=True).decode()

    # Create ReceivedEmail instance
    received_email = ReceivedEmail.objects.create(
        sender=sender,
        recipient=recipient,
        subject=subject,
        body=body,
        message_id=message_id
    )

    # Link to the original email if it's a reply
    if in_reply_to:
        try:
            original_email = SentEmail.objects.get(message_id=in_reply_to)
            received_email.in_reply_to = original_email
            received_email.thread_id = original_email.thread_id
            received_email.save()
        except SentEmail.DoesNotExist:
            pass

    # Process attachments
    for part in email_message.walk():
        if part.get_content_maintype() == 'multipart':
            continue
        if part.get('Content-Disposition') is None:
            continue

        filename = part.get_filename()
        if filename:
            content_type = part.get_content_type()
            file_data = part.get_payload(decode=True)
            
            attachment = Attachment(email=received_email, filename=filename, content_type=content_type)
            attachment.file.save(filename, ContentFile(file_data), save=True)

    return True

