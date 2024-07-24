import imaplib
import email
from email.header import decode_header
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

def fetch_emails():
    try:
        email_user = settings.EMAIL_HOST_USER.strip()
        email_pass = settings.EMAIL_HOST_PASSWORD.strip()
        
        logger.debug(f"Connecting to IMAP server: {settings.EMAIL_IMAP_SERVER}")
        
        mail = imaplib.IMAP4_SSL(settings.EMAIL_IMAP_SERVER, settings.EMAIL_IMAP_PORT)
        mail.login(email_user, email_pass)
        
        logger.debug("Successfully logged in to the email server.")
        
        mail.select("inbox")
        status, messages = mail.search(None, "ALL")
        email_ids = messages[0].split()
        
        emails = []
        
        for email_id in email_ids:
            status, msg_data = mail.fetch(email_id, "(RFC822)")
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    subject, encoding = decode_header(msg["Subject"])[0]
                    if isinstance(subject, bytes):
                        subject = subject.decode(encoding if encoding else "utf-8")
                    from_ = msg.get("From")
                    date = msg.get("Date")
                    
                    if msg.is_multipart():
                        for part in msg.walk():
                            content_type = part.get_content_type()
                            content_disposition = str(part.get("Content-Disposition"))

                            if "attachment" not in content_disposition:
                                try:
                                    body = part.get_payload(decode=True)
                                    if body:
                                        body = body.decode()
                                    else:
                                        body = ""
                                except Exception as e:
                                    logger.error(f"Error decoding body: {e}")
                                    body = ""
                                
                                emails.append({
                                    "subject": subject,
                                    "from": from_,
                                    "date": date,
                                    "body": body,
                                })
                    else:
                        try:
                            body = msg.get_payload(decode=True)
                            if body:
                                body = body.decode()
                            else:
                                body = ""
                        except Exception as e:
                            logger.error(f"Error decoding body: {e}")
                            body = ""
                        
                        emails.append({
                            "subject": subject,
                            "from": from_,
                            "date": date,
                            "body": body,
                        })
        
        mail.close()
        mail.logout()
        
        return emails
    except Exception as e:
        logger.error(f"Error fetching emails: {e}")
        return []
