# receiving/views.py

import imaplib
import email
from email.header import decode_header
from django.conf import settings
from django.core.files.base import ContentFile
from ..models import ReceivedEmail, Attachment  # Change this line
import json

def fetch_emails_service():    
    # Connect to the IMAP server
    imap_server = imaplib.IMAP4_SSL(settings.IMAP_SERVER, settings.IMAP_PORT)
    imap_server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
    imap_server.select('INBOX')

    # Search for all emails in the inbox
    _, message_numbers = imap_server.search(None, 'ALL')

    for num in message_numbers[0].split():
        _, msg_data = imap_server.fetch(num, '(RFC822)')
        email_body = msg_data[0][1]
        email_message = email.message_from_bytes(email_body)

        # Parse email details
        subject, encoding = decode_header(email_message["Subject"])[0]
        if isinstance(subject, bytes):
            subject = subject.decode(encoding or "utf-8")
        
        sender = email.utils.parseaddr(email_message["From"])[1]
        recipients = [email.utils.parseaddr(addr)[1] for addr in email_message.get_all("To", [])]
        cc = [email.utils.parseaddr(addr)[1] for addr in email_message.get_all("Cc", [])]
        bcc = [email.utils.parseaddr(addr)[1] for addr in email_message.get_all("Bcc", [])]

        # Get the email body (both plain text and HTML)
        plain_body = ""
        html_body = ""
        for part in email_message.walk():
            if part.get_content_type() == "text/plain":
                plain_body = part.get_payload(decode=True).decode()
            elif part.get_content_type() == "text/html":
                html_body = part.get_payload(decode=True).decode()

        # Create ReceivedEmail instance
        received_email = ReceivedEmail.objects.create(
            sender=sender,
            recipients=json.dumps(recipients),
            cc=json.dumps(cc) if cc else None,
            bcc=json.dumps(bcc) if bcc else None,
            subject=subject,
            body=plain_body,
            html_body=html_body,
            message_id=email_message["Message-ID"],
            headers=json.dumps(dict(email_message.items())),
            in_reply_to=ReceivedEmail.objects.filter(message_id=email_message["In-Reply-To"]).first() if email_message["In-Reply-To"] else None,
        )

        # Handle attachments
        for part in email_message.walk():
            if part.get_content_maintype() == 'multipart':
                continue
            if part.get('Content-Disposition') is None:
                continue

            filename = part.get_filename()
            if filename:
                file_data = part.get_payload(decode=True)
                content_type = part.get_content_type()
                size = len(file_data)
                attachment = Attachment(
                    email=received_email,
                    filename=filename,
                    content_type=content_type,
                    size=size
                )
                attachment.file.save(filename, ContentFile(file_data), save=True)

        # Mark the email as read
        imap_server.store(num, '+FLAGS', '\\Seen')

    imap_server.close()
    imap_server.logout()
    
    return "Emails fetched successfully"