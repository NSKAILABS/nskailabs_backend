from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import UserProfile


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for UserProfile model."""
    
    class Meta:
        model = UserProfile
        fields = ['phone_number', 'avatar_url', 'is_google_user']
        read_only_fields = ['is_google_user']


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model with profile data."""
    
    profile = UserProfileSerializer(source='userprofile', read_only=True)
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'first_name', 'last_name', 'full_name', 
                  'date_joined', 'last_login', 'profile']
        read_only_fields = ['id', 'email', 'date_joined', 'last_login']
    
    def get_full_name(self, obj):
        """Return full name or email if name not set."""
        full_name = f"{obj.first_name} {obj.last_name}".strip()
        return full_name if full_name else obj.email


class RegisterSerializer(serializers.ModelSerializer):
    """Serializer for user registration."""
    
    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        write_only=True, 
        required=True, 
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(
        write_only=True, 
        required=True,
        style={'input_type': 'password'}
    )
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)
    
    class Meta:
        model = User
        fields = ['email', 'password', 'password_confirm', 'first_name', 'last_name']
    
    def validate_email(self, value):
        """Ensure email is unique."""
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value.lower()
    
    def validate(self, attrs):
        """Validate that passwords match."""
        if attrs.get('password') != attrs.get('password_confirm'):
            raise serializers.ValidationError({
                "password_confirm": "Password fields didn't match."
            })
        return attrs
    
    def create(self, validated_data):
        """Create new user with profile."""
        validated_data.pop('password_confirm')
        
        user = User.objects.create_user(
            username=validated_data['email'],  # Use email as username
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
        )
        
        # Create associated profile
        UserProfile.objects.create(user=user)
        
        return user


class OTPSendSerializer(serializers.Serializer):
    """Serializer for OTP send requests."""
    
    email = serializers.EmailField(required=True)
    otp_type = serializers.ChoiceField(
        choices=['login', 'registration'],
        default='login'
    )
    
    def validate_email(self, value):
        """Normalize email to lowercase."""
        return value.lower()


class OTPVerifySerializer(serializers.Serializer):
    """Serializer for OTP verification requests."""
    
    email = serializers.EmailField(required=True)
    otp = serializers.CharField(min_length=6, max_length=6, required=True)
    otp_type = serializers.ChoiceField(
        choices=['login', 'registration'],
        default='login'
    )
    # Optional fields for registration
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)
    
    def validate_email(self, value):
        """Normalize email to lowercase."""
        return value.lower()
    
    def validate_otp(self, value):
        """Ensure OTP contains only digits."""
        if not value.isdigit():
            raise serializers.ValidationError("OTP must contain only digits.")
        return value


class GoogleAuthSerializer(serializers.Serializer):
    """Serializer for Google OAuth token."""
    
    credential = serializers.CharField(required=True)


class ProfileUpdateSerializer(serializers.ModelSerializer):
    """Serializer for profile updates."""
    
    first_name = serializers.CharField(source='user.first_name', required=False)
    last_name = serializers.CharField(source='user.last_name', required=False)
    
    class Meta:
        model = UserProfile
        fields = ['first_name', 'last_name', 'phone_number', 'avatar_url']
    
    def update(self, instance, validated_data):
        """Update user and profile data."""
        user_data = validated_data.pop('user', {})
        
        # Update User fields
        if user_data:
            user = instance.user
            for attr, value in user_data.items():
                setattr(user, attr, value)
            user.save()
        
        # Update Profile fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        return instance