import imaplib
import email
from email.header import decode_header
from django.conf import settings


def fetch_emails():
    # Connect to the server
    mail = imaplib.IMAP4_SSL('imap.ionos.com')
    mail.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)

    # Select the mailbox you want to use
    mail.select("inbox")

    # Search for all emails
    status, messages = mail.search(None, "ALL")
    
    # Convert messages to a list of email IDs
    email_ids = messages[0].split()
    
    emails = []
    
    for email_id in email_ids:
        # Fetch the email by ID
        status, msg_data = mail.fetch(email_id, "(RFC822)")
        
        for response_part in msg_data:
            if isinstance(response_part, tuple):
                # Parse the email content
                msg = email.message_from_bytes(response_part[1])
                
                # Decode email subject
                subject, encoding = decode_header(msg["Subject"])[0]
                if isinstance(subject, bytes):
                    subject = subject.decode(encoding if encoding else "utf-8")
                
                # Decode email sender
                from_ = msg.get("From")
                
                # Decode email date
                date = msg.get("Date")
                
                # Get the email body
                if msg.is_multipart():
                    for part in msg.walk():
                        content_type = part.get_content_type()
                        content_disposition = str(part.get("Content-Disposition"))

                        if "attachment" not in content_disposition:
                            body = part.get_payload(decode=True).decode()
                            emails.append({
                                "subject": subject,
                                "from": from_,
                                "date": date,
                                "body": body,
                            })
                else:
                    body = msg.get_payload(decode=True).decode()
                    emails.append({
                        "subject": subject,
                        "from": from_,
                        "date": date,
                        "body": body,
                    })
    
    # Close the connection and logout
    mail.close()
    mail.logout()
    
    return emails
# -*- coding: utf-8 -*-

