# -*- coding: utf-8 -*-

from rest_framework import serializers
from .models import Email

class EmailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Email
        fields = '__all__'#['recipient', 'subject', 'body']

class SendEmailSerializer(serializers.Serializer):
    recipients = serializers.ListField(child=serializers.EmailField())
    subject = serializers.CharField(max_length=255)
    body = serializers.CharField()
    delay_type = serializers.ChoiceField(choices=['fixed', 'random'], required=False)
    delay_value = serializers.IntegerField(required=False)
    min_delay = serializers.IntegerField(required=False)
    max_delay = serializers.IntegerField(required=False)