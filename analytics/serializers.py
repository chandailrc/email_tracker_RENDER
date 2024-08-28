from rest_framework import serializers
from tracking.models import EmailInteraction

class EmailInteractionSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailInteraction
        fields = '__all__'

