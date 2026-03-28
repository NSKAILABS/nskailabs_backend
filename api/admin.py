from django.contrib import admin
from .models import (
    UserProfile, MagicLink, ResearchPaper, Comment, Like,
    NewsletterSubscriber, Tool, ContactLead, LicenseKey, Announcement
)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'institution', 'is_contributor', 'created_at']
    list_filter = ['is_contributor', 'created_at']
    search_fields = ['user__username', 'user__email', 'institution']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(MagicLink)
class MagicLinkAdmin(admin.ModelAdmin):
    list_display = ['email', 'token', 'is_used', 'created_at', 'expires_at']
    list_filter = ['is_used', 'created_at']
    search_fields = ['email']
    readonly_fields = ['token', 'created_at']
    ordering = ['-created_at']


@admin.register(ResearchPaper)
class ResearchPaperAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'category', 'status', 'is_featured', 'views', 'published_at']
    list_filter = ['category', 'status', 'is_featured', 'created_at']
    search_fields = ['title', 'abstract', 'content', 'author__email']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ['views', 'reading_time', 'created_at', 'updated_at']
    list_editable = ['status', 'is_featured']
    filter_horizontal = ['co_authors']
    date_hierarchy = 'published_at'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'subtitle', 'abstract', 'content')
        }),
        ('Classification', {
            'fields': ('category', 'tags', 'author', 'co_authors')
        }),
        ('Media & Links', {
            'fields': ('featured_image', 'pdf_url', 'github_url', 'doi')
        }),
        ('Original Paper Reference', {
            'fields': (
                'original_paper_title', 'original_paper_authors',
                'original_paper_journal', 'original_paper_year', 'original_paper_doi'
            ),
            'classes': ('collapse',)
        }),
        ('Status & Metrics', {
            'fields': ('status', 'is_featured', 'views', 'reading_time', 'published_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['author', 'paper', 'is_approved', 'created_at']
    list_filter = ['is_approved', 'created_at']
    search_fields = ['content', 'author__email', 'paper__title']
    readonly_fields = ['created_at', 'updated_at']
    list_editable = ['is_approved']
    raw_id_fields = ['paper', 'author', 'parent']


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ['user', 'paper', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__email', 'paper__title']
    raw_id_fields = ['paper', 'user']


@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
    list_display = ['email', 'name', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['email', 'name']
    list_editable = ['is_active']


@admin.register(Tool)
class ToolAdmin(admin.ModelAdmin):
    list_display = ['name', 'author', 'stars', 'is_featured', 'created_at']
    list_filter = ['is_featured', 'created_at']
    search_fields = ['name', 'description', 'author__email']
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['is_featured']


@admin.register(ContactLead)
class ContactLeadAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'organization', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name', 'email', 'organization']
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
