from django.contrib import admin
from .models import ContactLead, LicenseKey, UserProfile, OTPVerification, Announcement


@admin.register(ContactLead)
class ContactLeadAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'organization', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name', 'email', 'organization']
    readonly_fields = ['created_at']


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'is_google_user', 'is_phone_verified', 'created_at']
    list_filter = ['is_google_user', 'is_phone_verified']
    search_fields = ['user__username', 'user__email', 'google_id']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(OTPVerification)
class OTPVerificationAdmin(admin.ModelAdmin):
    list_display = ['email', 'phone', 'otp_type', 'is_verified', 'attempts', 'created_at', 'expires_at']
    list_filter = ['otp_type', 'is_verified']
    search_fields = ['email', 'phone']
    readonly_fields = ['created_at']


@admin.register(LicenseKey)
class LicenseKeyAdmin(admin.ModelAdmin):
    list_display = ['key', 'user', 'product', 'is_active', 'expires_at']
    list_filter = ['is_active', 'product']
    search_fields = ['key', 'user__username', 'external_reference']


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'is_active', 'is_featured', 'published_at']
    list_filter = ['category', 'is_active', 'is_featured']
    search_fields = ['title', 'description']
    readonly_fields = ['created_at']
    list_editable = ['is_active', 'is_featured']