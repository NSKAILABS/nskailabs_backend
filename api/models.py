from django.db import models
from django.contrib.auth.models import User
import secrets
from datetime import timedelta
from django.utils import timezone


class UserProfile(models.Model):
    """Extended user profile for Google OAuth and OTP authentication."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    google_id = models.CharField(max_length=100, blank=True, null=True, unique=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    is_phone_verified = models.BooleanField(default=False)
    is_google_user = models.BooleanField(default=False)
    avatar_url = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s profile"


class OTPVerification(models.Model):
    """OTP verification for phone/email authentication."""
    OTP_TYPE_CHOICES = [
        ('registration', 'Registration'),
        ('login', 'Login'),
        ('password_reset', 'Password Reset'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='otp_codes', null=True, blank=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    otp_code = models.CharField(max_length=6)
    otp_type = models.CharField(max_length=20, choices=OTP_TYPE_CHOICES, default='registration')
    is_verified = models.BooleanField(default=False)
    attempts = models.IntegerField(default=0)
    max_attempts = models.IntegerField(default=3)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        identifier = self.email or self.phone
        return f"OTP for {identifier} - {self.otp_type}"

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(minutes=10)
        super().save(*args, **kwargs)

    def is_expired(self):
        return timezone.now() > self.expires_at

    def is_max_attempts_reached(self):
        return self.attempts >= self.max_attempts

    @classmethod
    def generate_otp(cls):
        """Generate a 6-digit OTP code."""
        return ''.join([str(secrets.randbelow(10)) for _ in range(6)])


class ContactLead(models.Model):
    """Contact form submissions."""
    name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True, null=True)
    organization = models.CharField(max_length=200, blank=True, null=True)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.email}"


class LicenseKey(models.Model):
    """License keys for software access (managed externally via MetaOptics)."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='license_keys')
    key = models.CharField(max_length=64, unique=True)
    product = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)
    activated_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    external_reference = models.CharField(max_length=200, blank=True, null=True, help_text="Reference ID from MetaOptics platform")

    class Meta:
        ordering = ['-activated_at']

    def __str__(self):
        return f"{self.key[:12]}... - {self.product} ({self.user.username})"


class Announcement(models.Model):
    """Platform announcements for the home page."""
    CATEGORY_CHOICES = [
        ('general', 'General'),
        ('hail_prediction', 'Hail Prediction'),
        ('quantum_research', 'Quantum Research'),
        ('photonics', 'Photonics'),
        ('product', 'Product Update'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='general')
    link = models.URLField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-published_at', '-created_at']

    def __str__(self):
        return f"{self.title} ({self.category})"