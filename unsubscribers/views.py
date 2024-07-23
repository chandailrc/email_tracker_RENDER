from .models import UnsubscribedUser
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect

# unsubscribers/views.py

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import UnsubscribedUser
from .serializers import UnsubscribedUserSerializer

from rest_framework.parsers import JSONParser

class UnsubscribedUserViewSet(viewsets.ModelViewSet):
    queryset = UnsubscribedUser.objects.all()
    serializer_class = UnsubscribedUserSerializer
    parser_classes = [JSONParser]

    @action(detail=False, methods=['post'])
    def unsubscribe(self, request):
        user_email = request.data.get('user_email')
        if user_email:
            unsubscribed, created = UnsubscribedUser.objects.get_or_create(email=user_email)
            return Response({
                'success': True,
                'message': 'You have been unsubscribed.',
                'already_unsubscribed': not created
            })
        else:
            return Response({
                'success': False,
                'message': 'Email address is required.'
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def unsubscribed_users(self, request):
        unsubscribed_users = self.get_queryset().values_list('email', flat=True)
        return Response({
            'unsubscribed_emails': list(unsubscribed_users)
        })

    @action(detail=False, methods=['post'])
    def delete_unsub_user(self, request):
        user_email = request.data.get('user_email')
        if user_email:
            try:
                user = UnsubscribedUser.objects.get(email=user_email)
                user.delete()
                return Response({
                    'success': True,
                    'message': f'User email {user_email} removed from unsubscribed list.'
                })
            except UnsubscribedUser.DoesNotExist:
                return Response({
                    'success': False,
                    'message': f'User email {user_email} not found in unsubscribed list.'
                }, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({
                'success': False,
                'message': 'Email address is required.'
            }, status=status.HTTP_400_BAD_REQUEST)

    # You can keep the destroy method if you want both options
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({
            'success': True,
            'message': f'User email {instance.email} removed from unsubscribed list.'
        })