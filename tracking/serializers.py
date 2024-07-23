# -*- coding: utf-8 -*-

from rest_framework import serializers
from .models import TrackingLog, LinkClick
from sending.models import Email, Link

class TrackingLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrackingLog
        fields = '__all__'

class LinkClickSerializer(serializers.ModelSerializer):
    class Meta:
        model = LinkClick
        fields = '__all__'

class LinkSerializer(serializers.ModelSerializer):
    linkclick_set = LinkClickSerializer(many=True, read_only=True)

    class Meta:
        model = Link
        fields = '__all__'

class EmailSerializer(serializers.ModelSerializer):
    trackinglog_set = TrackingLogSerializer(many=True, read_only=True)
    link_set = LinkSerializer(many=True, read_only=True)

    class Meta:
        model = Email
        fields = '__all__'