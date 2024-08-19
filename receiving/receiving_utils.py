import imaplib
import email
import re
from django.conf import settings
from .models import ReceivedEmail, Attachment
from sending.models import SentEmail
from django.core.files.base import ContentFile
from email.utils import parseaddr
from conversations.email_processor import process_email
from django.contrib.auth import get_user_model

from django.core.exceptions import ObjectDoesNotExist

def parse_email_body(body):
    # Patterns for different email clients
    patterns = [
        # Gmail and many others
        r'\n\s*On .+?wrote:\s*\n',
        # Outlook
        r'\n\s*-----Original Message-----\s*\n',
        # Another Outlook format
        r'\n\s*From:.*\n\s*Sent:.*\n\s*To:.*\n\s*Subject:.*\n',
        # Apple Mail
        r'\n\s*On .+?, .+ wrote:\s*\n',
        # Yahoo Mail
        r'\n\s*-{3,}\s*\n.*\n.*wrote:\s*\n'
    ]

    # Combine all patterns
    combined_pattern = '|'.join(patterns)

    # Split the body using the combined pattern
    parts = re.split(combined_pattern, body, maxsplit=1, flags=re.IGNORECASE | re.DOTALL)

    if len(parts) > 1:
        new_content = parts[0].strip()
        history = parts[1].strip()

        # Check if the split point is actually in the middle of the new content
        # This can happen if the new content contains something that looks like a header
        if len(new_content.splitlines()) < 3 and len(history.splitlines()) > 10:
            # If the new_content is very short and history is long, assume the split was incorrect
            new_content = body.strip()
            history = ''
    else:
        new_content = body.strip()
        history = ''

    return new_content, history

def clean_parsed_content(content):
    # Remove any leading '>' characters and extra whitespace
    lines = content.splitlines()
    cleaned_lines = []
    for line in lines:
        line = line.lstrip('>').strip()
        # Remove Outlook's separator if it's alone on a line
        if not line.strip('_') and len(line) > 20:
            continue
        cleaned_lines.append(line)
    
    # Join lines and remove any trailing Outlook separators
    cleaned_content = '\n'.join(cleaned_lines).strip()
    cleaned_content = re.sub(r'\n_{20,}\s*$', '', cleaned_content)
    
    return cleaned_content

def extract_message_id(header_value):
    if not header_value:
        return None
    # This regex looks for anything enclosed in < >, including the brackets
    match = re.search(r'(<[^>]+>)', header_value)
    if match:
        return match.group(1)
    return None

def find_email_model(user, message_id):
    try:
        sent_email = SentEmail.objects.get(user=user, message_id=message_id)
        return 'send', sent_email
    except ObjectDoesNotExist:
        pass
    
    try:
        received_email = ReceivedEmail.objects.get(user=user, message_id=message_id)
        return 'received', received_email
    except ObjectDoesNotExist:
        pass
    
    return None, None  # If message_id is not found in either model

def fetch_and_process_emails(user_id):
    new_emails_count = 0
    with imaplib.IMAP4_SSL(settings.EMAIL_IMAP_SERVER, settings.EMAIL_IMAP_PORT) as mail:
        mail.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
        mail.select('inbox')

        _, search_data = mail.search(None, 'UNSEEN')
        for num in search_data[0].split():
            _, data = mail.fetch(num, '(RFC822)')
            raw_email = data[0][1]
            if process_incoming_email(raw_email, user_id):
                new_emails_count += 1

    return new_emails_count

def process_incoming_email(raw_email, user_id):
    
    User = get_user_model()
    user = User.objects.get(id=user_id)
    
    email_message = email.message_from_bytes(raw_email)
    
    # Extract email details
    sender = parseaddr(email_message['From'])[1]
    recipient = parseaddr(email_message['To'])[1]
    subject = email_message['Subject']
    message_id = email_message['Message-ID']
    message_id = extract_message_id(message_id)
    in_reply_to = email_message.get('In-Reply-To')
    if in_reply_to:
        in_reply_to = extract_message_id(in_reply_to)
        references = email_message.get('References')
        
        if references:
            references = [extract_message_id(ref) for ref in references.split()]
            references = [ref for ref in references if ref]  # Remove any None values
            references = ' '.join(references)
        else:
            references = ''
    else:
        references = ''
    
    print(f'***********FROM INSIDE RECEIVING. sender of the received message: \n {sender}')
    print(f'***********FROM INSIDE RECEIVING. recipient of the received message: \n {recipient}')
    print(f'***********FROM INSIDE RECEIVING. subject of the received message: \n {subject}')
    print(f'***********FROM INSIDE RECEIVING. message_id of the received message: \n {message_id}')
    print(f'***********FROM INSIDE RECEIVING. in_reply_to of the received message: \n {in_reply_to}')
    print(f'***********FROM INSIDE RECEIVING. references of the received message: \n {references}')
    
    # Check if this email has already been processed
    if ReceivedEmail.objects.filter(user=user, message_id=message_id).exists():
        print(f'Email with message id {message_id} has already been received. Abandoning to prevent duplicate!')
        return False

    # Get the email body
    if email_message.is_multipart():
        for part in email_message.walk():
            if part.get_content_type() == "text/plain":
                body = part.get_payload(decode=True).decode()
                break
    else:
        body = email_message.get_payload(decode=True).decode()

    new_content, history = parse_email_body(body)

    # Create ReceivedEmail instance
    received_email = ReceivedEmail.objects.create(
        user=user,
        sender=sender,
        recipient=recipient,
        subject=subject,
        body=new_content,
        full_body=body,
        message_id=message_id,
        references=references
    )

    # Link to the original email if it's a reply
    if in_reply_to:
       
        result_msg, original_email = find_email_model(user, in_reply_to) 
        received_email.in_reply_to = in_reply_to
        if original_email:
            received_email.thread_id = original_email.thread_id
        else:
            received_email.thread_id = ''
        received_email.save()
        
        process_email(received_email, 'received', user_id, result_msg)
        
    else:
        received_email.in_reply_to = in_reply_to
        received_email.thread_id = ''
        received_email.save()
        process_email(received_email, 'received', user_id)

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

