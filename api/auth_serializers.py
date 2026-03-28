from django.contrib.auth.models import User
from rest_framework import serializers

from .models import UserProfile


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for UserProfile model."""
    
    class Meta:
        model = UserProfile
        fields = [
            'bio', 'institution', 'department', 'research_interests',
            'website', 'google_scholar', 'orcid', 'avatar_url',
            'twitter', 'linkedin', 'is_contributor',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model with profile data."""
    
    profile = UserProfileSerializer(read_only=True)
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name', 
            'full_name', 'date_joined', 'last_login', 'profile'
        ]
        read_only_fields = ['id', 'email', 'date_joined', 'last_login']
    
    def get_full_name(self, obj):
        """Return full name or email if name not set."""
        full_name = f"{obj.first_name} {obj.last_name}".strip()
        return full_name if full_name else obj.email.split('@')[0]


class ProfileUpdateSerializer(serializers.ModelSerializer):
    """Serializer for profile updates."""
    
    # User fields
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)
    
    # Profile fields
    bio = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    institution = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    department = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    research_interests = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=list
    )
    website = serializers.URLField(required=False, allow_blank=True, allow_null=True)
    google_scholar = serializers.URLField(required=False, allow_blank=True, allow_null=True)
    orcid = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    avatar_url = serializers.URLField(required=False, allow_blank=True, allow_null=True)
    twitter = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    linkedin = serializers.URLField(required=False, allow_blank=True, allow_null=True)
    
    class Meta:
        model = UserProfile
        fields = [
            'first_name', 'last_name',
            'bio', 'institution', 'department', 'research_interests',
            'website', 'google_scholar', 'orcid', 'avatar_url',
            'twitter', 'linkedin'
        ]
    
    def update(self, instance, validated_data):
        """Update user and profile data."""
        # Extract user fields
        first_name = validated_data.pop('first_name', None)
        last_name = validated_data.pop('last_name', None)
        
        # Update User fields
        user = instance.user
        if first_name is not None:
            user.first_name = first_name
        if last_name is not None:
            user.last_name = last_name
        user.save()
        
        # Update Profile fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        return instance


class MagicLinkRequestSerializer(serializers.Serializer):
    """Serializer for magic link request."""
    
    email = serializers.EmailField(required=True)
    
    def validate_email(self, value):
        """Normalize email to lowercase."""
        return value.lower().strip()


class MagicLinkVerifySerializer(serializers.Serializer):
    """Serializer for magic link verification."""
    
    token = serializers.UUIDField(required=True)


class AuthorSerializer(serializers.ModelSerializer):
    """Minimal serializer for author info in papers/comments."""
    
    full_name = serializers.SerializerMethodField()
    avatar_url = serializers.SerializerMethodField()
    institution = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'full_name', 'avatar_url', 'institution']
    
    def get_full_name(self, obj):
        full_name = f"{obj.first_name} {obj.last_name}".strip()
        return full_name if full_name else obj.email.split('@')[0]
    
    def get_avatar_url(self, obj):
        try:
            return obj.profile.avatar_url
        except UserProfile.DoesNotExist:
            return None
    
    def get_institution(self, obj):
        try:
            return obj.profile.institution
        except UserProfile.DoesNotExist:
            return None
