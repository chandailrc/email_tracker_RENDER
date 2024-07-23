import time
import random

from . import email_utils

from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from utils.permissions import IsAuthenticatedOrDevMode

from .serializers import SendEmailSerializer


@api_view(['POST'])
@permission_classes([IsAuthenticatedOrDevMode])
def send_tracked_email(request):
    serializer = SendEmailSerializer(data=request.data)
    if serializer.is_valid():
        data = serializer.validated_data
        sent_count = 0
        failed_recipients = []

        for recipient in data['recipients']:
            success = email_utils.tracked_email_sender(recipient, data['subject'], data['body'])
            if success:
                sent_count += 1
            else:
                failed_recipients.append(recipient)
            
            if data.get('delay_type') == 'fixed':
                time.sleep(data.get('delay_value', 0))
            elif data.get('delay_type') == 'random':
                time.sleep(random.uniform(data.get('min_delay', 0), data.get('max_delay', 0)))

        confirmation_message = f"{sent_count} email(s) sent successfully!"
        return Response({
            'success': True,
            'message': confirmation_message,
            'sent_count': sent_count,
            'failed_recipients': failed_recipients
        })
    return Response(serializer.errors, status=400)