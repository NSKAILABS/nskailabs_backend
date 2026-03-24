from rest_framework import serializers
from .models import ContactLead


class ContactLeadSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactLead
        fields = ['id', 'name', 'email', 'phone', 'organization', 'message', 'created_at']
        read_only_fields = ['id', 'created_at']
