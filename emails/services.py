# -*- coding: utf-8 -*-

import imaplib
import email
from email.header import decode_header
from django.conf import settings
from .models import Email

def fetch_emails():
    # Connect to the IMAP server
    imap_server = imaplib.IMAP4_SSL(settings.EMAIL_IMAP_SERVER, settings.EMAIL_IMAP_PORT)
    imap_server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
    imap_server.select('INBOX')

    # Search for all emails in the inbox
    _, message_numbers = imap_server.search(None, 'ALL')

    for num in message_numbers[0].split():
        _, msg_data = imap_server.fetch(num, '(RFC822)')
        email_body = msg_data[0][1]
        email_message = email.message_from_bytes(email_body)

        # Decode subject
        subject, encoding = decode_header(email_message["Subject"])[0]
        if isinstance(subject, bytes):
            subject = subject.decode(encoding or "utf-8", errors="replace")

        # Get sender
        sender = email.utils.parseaddr(email_message["From"])[1]

        # Get body
        if email_message.is_multipart():
            for part in email_message.walk():
                if part.get_content_type() == "text/plain":
                    body = part.get_payload(decode=True)
                    break
        else:
            body = email_message.get_payload(decode=True)

        # Decode body
        if isinstance(body, bytes):
            try:
                body = body.decode('utf-8')
            except UnicodeDecodeError:
                body = body.decode('utf-8', errors='replace')

        # Save to database
        Email.objects.create(sender=sender, subject=subject, body=body)

    imap_server.close()
    imap_server.logout()
    imap_server.logout()