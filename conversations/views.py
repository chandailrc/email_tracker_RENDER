from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import Conversation, ConversationMessage, ConversationParticipant
from sending.models import Email as SentEmail
from receiving.models import ReceivedEmail
import json

@require_http_methods(["GET"])
def list_conversations(request):
    conversations = Conversation.objects.all().order_by('-last_updated')
    data = [{
        'id': conv.id,
        'subject': conv.subject,
        'last_updated': conv.last_updated.isoformat(),
        'participants': [p.email for p in conv.participants.all()]
    } for conv in conversations]
    return JsonResponse({'conversations': data})

@require_http_methods(["GET"])
def get_conversation(request, conversation_id):
    try:
        conversation = Conversation.objects.get(id=conversation_id)
        messages = conversation.messages.all().order_by('timestamp')
        data = {
            'id': conversation.id,
            'subject': conversation.subject,
            'participants': [p.email for p in conversation.participants.all()],
            'messages': [{
                'id': msg.id,
                'sender': msg.sent_email.sender if msg.sent_email else msg.received_email.sender,
                'content': msg.sent_email.body if msg.sent_email else msg.received_email.body,
                'timestamp': msg.timestamp.isoformat()
            } for msg in messages]
        }
        return JsonResponse(data)
    except Conversation.DoesNotExist:
        return JsonResponse({'error': 'Conversation not found'}, status=404)

@require_http_methods(["POST"])
def create_conversation(request):
    data = json.loads(request.body)
    subject = data.get('subject')
    participants = data.get('participants', [])
    
    conversation = Conversation.objects.create(subject=subject)
    for email in participants:
        ConversationParticipant.objects.create(conversation=conversation, email=email)
    
    return JsonResponse({'id': conversation.id, 'subject': conversation.subject}, status=201)

@require_http_methods(["POST"])
def add_message_to_conversation(request, conversation_id):
    data = json.loads(request.body)
    email_id = data.get('email_id')
    email_type = data.get('email_type')  # 'sent' or 'received'
    
    try:
        conversation = Conversation.objects.get(id=conversation_id)
        if email_type == 'sent':
            email = SentEmail.objects.get(id=email_id)
            ConversationMessage.objects.create(conversation=conversation, sent_email=email)
        elif email_type == 'received':
            email = ReceivedEmail.objects.get(id=email_id)
            ConversationMessage.objects.create(conversation=conversation, received_email=email)
        else:
            return JsonResponse({'error': 'Invalid email type'}, status=400)
        
        return JsonResponse({'success': True}, status=201)
    except (Conversation.DoesNotExist, SentEmail.DoesNotExist, ReceivedEmail.DoesNotExist):
        return JsonResponse({'error': 'Conversation or Email not found'}, status=404)