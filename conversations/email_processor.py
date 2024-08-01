from django.core.exceptions import ValidationError
from .models import Conversation, ConversationParticipant, ConversationMessage
from sending.models import SentEmail
from receiving.models import ReceivedEmail

def process_email(email, email_type, user):
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
                existing_message = ConversationMessage.objects.get(conversation__user=user, received_email=email.in_reply_to)
            else:  # received
                existing_message = ConversationMessage.objects.get(conversation__user=user, sent_email=email.in_reply_to)
            conversation = existing_message.conversation
        except ConversationMessage.DoesNotExist:
            # If not found, create a new conversation
            conversation = Conversation.objects.create(user=user, subject=email.subject)
    else:
        # Create a new conversation
        conversation = Conversation.objects.create(user=user, subject=email.subject)
    
    # Add participants
    participants = [email.sender, email.recipient] + email.get_cc_list() + email.get_bcc_list()
    for participant in set(participants):
        ConversationParticipant.objects.get_or_create(conversation=conversation, email=participant)
    
    # Add the message to the conversation
    if email_type == 'sent':
        ConversationMessage.objects.create(conversation=conversation, sent_email=email)
    else:
        ConversationMessage.objects.create(conversation=conversation, received_email=email)
    
    conversation.save()  # Update the last_updated field
    return conversation