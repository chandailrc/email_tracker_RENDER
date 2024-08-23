from django.core.exceptions import ValidationError
from .models import Conversation, ConversationParticipant, ConversationMessage
from sending.models import SentEmail
from receiving.models import ReceivedEmail
from django.contrib.auth import get_user_model

def process_email(email, email_type, user_id, in_reply_sendOrRec=None, imap_datetime=None):
    User = get_user_model()
    user = User.objects.get(id=user_id)
    
    if email_type not in ['sent', 'received']:
        raise ValueError('Invalid email type')
    
    if email_type == 'sent' and not isinstance(email, SentEmail):
        raise ValidationError('Email object must be an instance of SentEmail for sent emails')
    
    if email_type == 'received' and not isinstance(email, ReceivedEmail):
        raise ValidationError('Email object must be an instance of ReceivedEmail for received emails')

    # Check if the email is a reply to an existing conversation
    if email.in_reply_to:
        try:
            if email_type == 'sent':
                if in_reply_sendOrRec == "send":
                    in_reply_to_email = SentEmail.objects.get(user=user, message_id=email.in_reply_to)
                    existing_message = ConversationMessage.objects.get(conversation__user=user, sent_email=in_reply_to_email)
                else:
                    in_reply_to_email = ReceivedEmail.objects.get(user=user, message_id=email.in_reply_to)
                    existing_message = ConversationMessage.objects.get(conversation__user=user, received_email=in_reply_to_email)
            else:  # received
                if in_reply_sendOrRec == "send":
                    in_reply_to_email = SentEmail.objects.get(user=user, message_id=email.in_reply_to)
                    existing_message = ConversationMessage.objects.get(conversation__user=user, sent_email=in_reply_to_email)
                else:
                    in_reply_to_email = ReceivedEmail.objects.get(user=user, message_id=email.in_reply_to)
                    existing_message = ConversationMessage.objects.get(conversation__user=user, received_email=in_reply_to_email)
                existing_message.conversation.increment_unread_count() # Increase the unread counter for ANY received email
            conversation = existing_message.conversation
        except ConversationMessage.DoesNotExist:
            # If not found, create a new conversation
            conversation = Conversation.objects.create(user=user, subject=email.subject)
    else:
        # Create a new conversation
        conversation = Conversation.objects.create(user=user, subject=email.subject, unread=True, is_new=True)
    
    # Add participants
    participants = [email.sender, email.recipient] + email.get_cc_list() + email.get_bcc_list()
    for participant in set(participants):
        ConversationParticipant.objects.get_or_create(conversation=conversation, email=participant)
    
    # Add the message to the conversation
    if email_type == 'sent':
        ConversationMessage.objects.create(conversation=conversation, sent_email=email, content=email.body)
    else:
        ConversationMessage.objects.create(conversation=conversation, received_email=email, content=email.body)
    
    conversation.save(delivered_timestamp=imap_datetime)  # Update the last_updated field. If imap_datetime is Non
    return conversation