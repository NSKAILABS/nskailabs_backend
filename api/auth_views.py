import os
import secrets
from datetime import timedelta

from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

from .auth_serializers import RegisterSerializer, UserSerializer
from .models import UserProfile, OTPVerification


def get_tokens_for_user(user):
    """Generate JWT tokens for a user."""
    refresh = RefreshToken.for_user(user)
    return {
        'access': str(refresh.access_token),
        'refresh': str(refresh),
    }


@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """Standard registration with email/password."""
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        # Create user profile
        UserProfile.objects.get_or_create(user=user)
        tokens = get_tokens_for_user(user)
        return Response({
            'message': 'Registration successful.',
            'user': UserSerializer(user).data,
            'tokens': tokens
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def google_auth(request):
    """
    Authenticate with Google OAuth2.
    Expects: { "credential": "<Google ID Token>" }
    """
    credential = request.data.get('credential')
    
    if not credential:
        return Response(
            {'error': 'Google credential is required.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    google_client_id = os.environ.get('GOOGLE_CLIENT_ID', '')
    
    if not google_client_id:
        return Response(
            {'error': 'Google authentication is not configured.'},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )
    
    try:
        # Verify the Google ID token
        idinfo = id_token.verify_oauth2_token(
            credential,
            google_requests.Request(),
            google_client_id
        )
        
        google_id = idinfo['sub']
        email = idinfo.get('email', '')
        first_name = idinfo.get('given_name', '')
        last_name = idinfo.get('family_name', '')
        avatar_url = idinfo.get('picture', '')
        
        # Check if user exists with this Google ID
        try:
            profile = UserProfile.objects.get(google_id=google_id)
            user = profile.user
        except UserProfile.DoesNotExist:
            # Check if user exists with this email
            try:
                user = User.objects.get(email=email)
                # Link Google account to existing user
                profile, _ = UserProfile.objects.get_or_create(user=user)
                profile.google_id = google_id
                profile.is_google_user = True
                profile.avatar_url = avatar_url
                profile.save()
            except User.DoesNotExist:
                # Create new user
                username = email.split('@')[0]
                base_username = username
                counter = 1
                while User.objects.filter(username=username).exists():
                    username = f"{base_username}{counter}"
                    counter += 1
                
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                )
                user.set_unusable_password()
                user.save()
                
                UserProfile.objects.create(
                    user=user,
                    google_id=google_id,
                    is_google_user=True,
                    avatar_url=avatar_url,
                )
        
        tokens = get_tokens_for_user(user)
        
        return Response({
            'message': 'Google authentication successful.',
            'user': UserSerializer(user).data,
            'tokens': tokens,
            'is_new_user': False,
        })
        
    except ValueError as e:
        return Response(
            {'error': 'Invalid Google credential.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        return Response(
            {'error': f'Authentication failed: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def send_otp(request):
    """
    Send OTP to email for verification.
    Expects: { "email": "<email>", "otp_type": "registration|login|password_reset" }
    """
    email = request.data.get('email', '').strip().lower()
    otp_type = request.data.get('otp_type', 'registration')
    
    if not email:
        return Response(
            {'error': 'Email is required.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Check rate limiting - max 3 OTPs per email per hour
    recent_otps = OTPVerification.objects.filter(
        email=email,
        created_at__gte=timezone.now() - timedelta(hours=1)
    ).count()
    
    if recent_otps >= 3:
        return Response(
            {'error': 'Too many OTP requests. Please try again later.'},
            status=status.HTTP_429_TOO_MANY_REQUESTS
        )
    
    # For login/password_reset, check if user exists
    user = None
    if otp_type in ['login', 'password_reset']:
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {'error': 'No account found with this email.'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    # For registration, check if email is already taken
    if otp_type == 'registration':
        if User.objects.filter(email=email).exists():
            return Response(
                {'error': 'An account with this email already exists.'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    # Invalidate previous OTPs for this email
    OTPVerification.objects.filter(
        email=email,
        is_verified=False
    ).update(is_verified=True)
    
    # Generate new OTP
    otp_code = OTPVerification.generate_otp()
    
    otp_record = OTPVerification.objects.create(
        user=user,
        email=email,
        otp_code=otp_code,
        otp_type=otp_type,
        expires_at=timezone.now() + timedelta(minutes=10)
    )
    
    # Send OTP via email
    try:
        subject = f"Your NSKAILabs Verification Code: {otp_code}"
        message = f"""
Hello,

Your verification code for NSKAILabs is: {otp_code}

This code will expire in 10 minutes.

If you did not request this code, please ignore this email.

Best regards,
NSKAILabs Team
        """
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )
        
        return Response({
            'message': 'OTP sent successfully.',
            'email': email,
            'expires_in_minutes': 10,
        })
        
    except Exception as e:
        otp_record.delete()
        return Response(
            {'error': 'Failed to send OTP. Please try again.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def verify_otp(request):
    """
    Verify OTP and complete authentication.
    Expects: { "email": "<email>", "otp": "<6-digit-code>", "otp_type": "registration|login", ... }
    For registration, also expects: { "username": "<username>", "first_name": "...", "last_name": "..." }
    """
    email = request.data.get('email', '').strip().lower()
    otp_code = request.data.get('otp', '').strip()
    otp_type = request.data.get('otp_type', 'registration')
    
    if not email or not otp_code:
        return Response(
            {'error': 'Email and OTP are required.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Find the latest unverified OTP for this email
    try:
        otp_record = OTPVerification.objects.filter(
            email=email,
            otp_type=otp_type,
            is_verified=False
        ).latest('created_at')
    except OTPVerification.DoesNotExist:
        return Response(
            {'error': 'No pending OTP found for this email.'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Check if expired
    if otp_record.is_expired():
        return Response(
            {'error': 'OTP has expired. Please request a new one.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Check max attempts
    if otp_record.is_max_attempts_reached():
        return Response(
            {'error': 'Maximum verification attempts reached. Please request a new OTP.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Verify OTP
    if otp_record.otp_code != otp_code:
        otp_record.attempts += 1
        otp_record.save()
        remaining = otp_record.max_attempts - otp_record.attempts
        return Response(
            {'error': f'Invalid OTP. {remaining} attempts remaining.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # OTP is valid - mark as verified
    otp_record.is_verified = True
    otp_record.save()
    
    if otp_type == 'registration':
        # Create new user
        username = request.data.get('username', email.split('@')[0])
        first_name = request.data.get('first_name', '')
        last_name = request.data.get('last_name', '')
        
        # Ensure unique username
        base_username = username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1
        
        user = User.objects.create_user(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
        )
        user.set_unusable_password()
        user.save()
        
        UserProfile.objects.create(user=user)
        
        tokens = get_tokens_for_user(user)
        
        return Response({
            'message': 'Registration successful.',
            'user': UserSerializer(user).data,
            'tokens': tokens,
        }, status=status.HTTP_201_CREATED)
    
    elif otp_type == 'login':
        # Login existing user
        try:
            user = User.objects.get(email=email)
            tokens = get_tokens_for_user(user)
            
            return Response({
                'message': 'Login successful.',
                'user': UserSerializer(user).data,
                'tokens': tokens,
            })
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    return Response({'message': 'OTP verified successfully.'})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def me(request):
    """Get current user profile."""
    user_data = UserSerializer(request.user).data
    
    # Add profile data if exists
    try:
        profile = request.user.profile
        user_data['is_google_user'] = profile.is_google_user
        user_data['avatar_url'] = profile.avatar_url
    except UserProfile.DoesNotExist:
        pass
    
    return Response(user_data)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_profile(request):
    """Update user profile."""
    serializer = UserSerializer(request.user, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)