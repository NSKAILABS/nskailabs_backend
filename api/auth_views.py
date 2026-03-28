import os
from datetime import timedelta

from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.html import strip_tags
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken

from .models import MagicLink, UserProfile
from .auth_serializers import UserSerializer, ProfileUpdateSerializer


def get_tokens_for_user(user):
    """Generate JWT tokens for a user."""
    refresh = RefreshToken.for_user(user)
    return {
        'access': str(refresh.access_token),
        'refresh': str(refresh),
    }


def get_frontend_url():
    """Get the frontend URL from environment or default."""
    return os.environ.get('FRONTEND_URL', 'https://nskailabs.com')


@api_view(['POST'])
@permission_classes([AllowAny])
def request_magic_link(request):
    """
    Request a magic link for authentication.
    Expects: { "email": "user@example.com" }
    """
    email = request.data.get('email', '').strip().lower()
    
    if not email:
        return Response(
            {'error': 'Email is required.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Basic email validation
    if '@' not in email or '.' not in email:
        return Response(
            {'error': 'Please enter a valid email address.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Rate limiting - max 5 magic links per email per hour
    recent_links = MagicLink.objects.filter(
        email=email,
        created_at__gte=timezone.now() - timedelta(hours=1)
    ).count()
    
    if recent_links >= 5:
        return Response(
            {'error': 'Too many requests. Please try again later.'},
            status=status.HTTP_429_TOO_MANY_REQUESTS
        )
    
    # Create magic link
    magic_link = MagicLink.create_for_email(email)
    
    # Build verification URL
    frontend_url = get_frontend_url()
    verification_url = f"{frontend_url}/auth/verify?token={magic_link.token}"
    
    # Send email
    try:
        subject = "Sign in to NSKAILabs"
        
        # Plain text version
        message = f"""
Hello,

Click the link below to sign in to NSKAILabs:

{verification_url}

This link will expire in 15 minutes.

If you didn't request this link, you can safely ignore this email.

Best regards,
The NSKAILabs Team

---
NSKAILabs - Open Research in Nanophotonics & Metasurfaces
https://nskailabs.com
        """
        
        # HTML version
        html_message = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="text-align: center; margin-bottom: 30px;">
        <h1 style="color: #2563eb; margin: 0; font-size: 24px;">NSKAILabs</h1>
        <p style="color: #6b7280; margin: 5px 0 0 0; font-size: 14px;">Open Research in Nanophotonics & Metasurfaces</p>
    </div>
    
    <div style="background: #f8fafc; border-radius: 12px; padding: 30px; margin-bottom: 20px;">
        <h2 style="margin: 0 0 15px 0; font-size: 20px; color: #1f2937;">Sign in to your account</h2>
        <p style="margin: 0 0 25px 0; color: #4b5563;">Click the button below to sign in. This link will expire in 15 minutes.</p>
        
        <a href="{verification_url}" style="display: inline-block; background: #2563eb; color: white; padding: 14px 32px; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 16px;">
            Sign in to NSKAILabs
        </a>
    </div>
    
    <p style="color: #6b7280; font-size: 13px; margin-bottom: 10px;">
        Or copy and paste this link into your browser:
    </p>
    <p style="background: #f1f5f9; padding: 12px; border-radius: 6px; font-size: 12px; word-break: break-all; color: #475569;">
        {verification_url}
    </p>
    
    <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 30px 0;">
    
    <p style="color: #9ca3af; font-size: 12px; text-align: center;">
        If you didn't request this link, you can safely ignore this email.
    </p>
</body>
</html>
        """
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            html_message=html_message,
            fail_silently=False,
        )
        
        return Response({
            'message': 'Magic link sent to your email.',
            'email': email,
            'expires_in_minutes': 15,
        })
        
    except Exception as e:
        # Delete the magic link if email failed
        magic_link.delete()
        return Response(
            {'error': 'Failed to send email. Please try again.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def verify_magic_link(request):
    """
    Verify magic link token and authenticate user.
    Expects: { "token": "uuid-token" }
    """
    token = request.data.get('token', '').strip()
    
    if not token:
        return Response(
            {'error': 'Token is required.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Find the magic link
    try:
        magic_link = MagicLink.objects.get(token=token)
    except MagicLink.DoesNotExist:
        return Response(
            {'error': 'Invalid or expired link. Please request a new one.'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Check if already used
    if magic_link.is_used:
        return Response(
            {'error': 'This link has already been used. Please request a new one.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Check if expired
    if magic_link.is_expired():
        return Response(
            {'error': 'This link has expired. Please request a new one.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Mark as used
    magic_link.is_used = True
    magic_link.save()
    
    email = magic_link.email
    is_new_user = False
    
    # Get or create user
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        # Create new user
        is_new_user = True
        
        # Generate username from email
        username = email.split('@')[0]
        base_username = username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1
        
        user = User.objects.create_user(
            username=username,
            email=email,
        )
        user.set_unusable_password()
        user.save()
        
        # Create profile
        UserProfile.objects.create(user=user)
    
    # Ensure profile exists for existing users
    UserProfile.objects.get_or_create(user=user)
    
    # Update last login
    user.last_login = timezone.now()
    user.save(update_fields=['last_login'])
    
    # Generate tokens
    tokens = get_tokens_for_user(user)
    
    return Response({
        'message': 'Authentication successful.',
        'user': UserSerializer(user).data,
        'tokens': tokens,
        'is_new_user': is_new_user,
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    """
    Logout user by blacklisting their refresh token.
    Expects: { "refresh": "refresh-token" }
    """
    refresh_token = request.data.get('refresh')
    
    if not refresh_token:
        return Response(
            {'error': 'Refresh token is required.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        token = RefreshToken(refresh_token)
        token.blacklist()
        return Response({'message': 'Successfully logged out.'})
    except Exception:
        return Response(
            {'error': 'Invalid token.'},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user(request):
    """Get current authenticated user."""
    return Response(UserSerializer(request.user).data)


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_profile(request):
    """Update user profile."""
    try:
        profile = request.user.profile
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=request.user)
    
    serializer = ProfileUpdateSerializer(
        profile, 
        data=request.data, 
        partial=True,
        context={'request': request}
    )
    
    if serializer.is_valid():
        serializer.save()
        return Response(UserSerializer(request.user).data)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
