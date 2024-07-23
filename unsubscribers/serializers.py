# -*- coding: utf-8 -*-

from rest_framework import serializers
from .models import UnsubscribedUser

class UnsubscribedUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = UnsubscribedUser
        fields = '__all__'

