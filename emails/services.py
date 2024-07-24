import imaplib
import email
from email.header import decode_header
from django.conf import settings
from .models import Email
from django.utils import timezone

def clean_text(text):
    if isinstance(text, bytes):
        try:
            text = text.decode('utf-8')
        except UnicodeDecodeError:
            text = text.decode('utf-8', errors='replace')
    return text.replace('\x00', '') if text else ''

def fetch_emails():
    imap_server = imaplib.IMAP4_SSL(settings.EMAIL_IMAP_SERVER, settings.EMAIL_IMAP_PORT)
    imap_server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
    imap_server.select('INBOX')

    _, message_numbers = imap_server.search(None, 'ALL')

    for num in message_numbers[0].split():
        try:
            _, msg_data = imap_server.fetch(num, '(RFC822)')
            email_body = msg_data[0][1]
            email_message = email.message_from_bytes(email_body)

            message_id = email_message.get('Message-ID', '')
            if message_id and Email.objects.filter(message_id=message_id).exists():
                continue  # Skip if email already exists and has a message_id

            subject, encoding = decode_header(email_message["Subject"])[0]
            subject = clean_text(subject)

            sender = email.utils.parseaddr(email_message["From"])[1]
            date_tuple = email.utils.parsedate_tz(email_message['Date'])
            if date_tuple:
                received_at = timezone.datetime(*date_tuple[:6])
            else:
                received_at = timezone.now()

            body_html = ""
            body_text = ""
            for part in email_message.walk():
                if part.get_content_type() == "text/plain":
                    body_text = clean_text(part.get_payload(decode=True))
                elif part.get_content_type() == "text/html":
                    body_html = clean_text(part.get_payload(decode=True))

            Email.objects.create(
                sender=sender,
                subject=subject,
                body_text=body_text or None,
                body_html=body_html or None,
                received_at=received_at,
                message_id=message_id or None
            )
        except Exception as e:
            print(f"Error processing email: {str(e)}")

    imap_server.close()
    imap_server.logout()