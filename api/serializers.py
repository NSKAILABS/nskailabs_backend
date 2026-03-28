from rest_framework import serializers
from django.contrib.auth.models import User

from .models import (
    ContactLead, ResearchPaper, Comment, Like, 
    NewsletterSubscriber, Tool, Announcement
)
from .auth_serializers import AuthorSerializer


class ContactLeadSerializer(serializers.ModelSerializer):
    """Serializer for contact form submissions."""
    
    class Meta:
        model = ContactLead
        fields = ['id', 'name', 'email', 'phone', 'organization', 'message', 'created_at']
        read_only_fields = ['id', 'created_at']


class CommentSerializer(serializers.ModelSerializer):
    """Serializer for comments."""
    
    author = AuthorSerializer(read_only=True)
    replies = serializers.SerializerMethodField()
    
    class Meta:
        model = Comment
        fields = [
            'id', 'author', 'content', 'parent', 
            'created_at', 'updated_at', 'replies'
        ]
        read_only_fields = ['id', 'author', 'created_at', 'updated_at']
    
    def get_replies(self, obj):
        """Get nested replies."""
        if obj.replies.exists():
            return CommentSerializer(
                obj.replies.filter(is_approved=True), 
                many=True
            ).data
        return []


class CommentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating comments."""
    
    class Meta:
        model = Comment
        fields = ['content', 'parent']


class ResearchPaperListSerializer(serializers.ModelSerializer):
    """Serializer for paper list view."""
    
    author = AuthorSerializer(read_only=True)
    like_count = serializers.IntegerField(read_only=True)
    comment_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = ResearchPaper
        fields = [
            'id', 'title', 'slug', 'subtitle', 'abstract',
            'category', 'tags', 'author',
            'featured_image', 'status', 'is_featured',
            'views', 'reading_time', 'like_count', 'comment_count',
            'published_at', 'created_at'
        ]


class ResearchPaperDetailSerializer(serializers.ModelSerializer):
    """Serializer for paper detail view."""
    
    author = AuthorSerializer(read_only=True)
    co_authors = AuthorSerializer(many=True, read_only=True)
    like_count = serializers.IntegerField(read_only=True)
    comment_count = serializers.IntegerField(read_only=True)
    is_liked = serializers.SerializerMethodField()
    comments = serializers.SerializerMethodField()
    
    class Meta:
        model = ResearchPaper
        fields = [
            'id', 'title', 'slug', 'subtitle', 'abstract', 'content',
            'category', 'tags', 'author', 'co_authors',
            'featured_image', 'pdf_url', 'github_url', 'doi',
            'original_paper_title', 'original_paper_authors',
            'original_paper_journal', 'original_paper_year', 'original_paper_doi',
            'status', 'is_featured', 'views', 'reading_time',
            'like_count', 'comment_count', 'is_liked', 'comments',
            'published_at', 'created_at', 'updated_at'
        ]
    
    def get_is_liked(self, obj):
        """Check if current user has liked this paper."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Like.objects.filter(paper=obj, user=request.user).exists()
        return False
    
    def get_comments(self, obj):
        """Get top-level comments."""
        top_level_comments = obj.comments.filter(
            is_approved=True, 
            parent__isnull=True
        ).order_by('-created_at')
        return CommentSerializer(top_level_comments, many=True).data


class ResearchPaperCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating papers."""
    
    co_authors = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        many=True,
        required=False
    )
    
    class Meta:
        model = ResearchPaper
        fields = [
            'title', 'subtitle', 'abstract', 'content',
            'category', 'tags', 'co_authors',
            'featured_image', 'pdf_url', 'github_url', 'doi',
            'original_paper_title', 'original_paper_authors',
            'original_paper_journal', 'original_paper_year', 'original_paper_doi',
            'status'
        ]
    
    def create(self, validated_data):
        co_authors = validated_data.pop('co_authors', [])
        paper = ResearchPaper.objects.create(**validated_data)
        paper.co_authors.set(co_authors)
        return paper
    
    def update(self, instance, validated_data):
        co_authors = validated_data.pop('co_authors', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if co_authors is not None:
            instance.co_authors.set(co_authors)
        return instance


class NewsletterSubscriberSerializer(serializers.ModelSerializer):
    """Serializer for newsletter subscriptions."""
    
    class Meta:
        model = NewsletterSubscriber
        fields = ['email', 'name', 'interests']
    
    def validate_email(self, value):
        """Normalize email to lowercase."""
        return value.lower().strip()


class ToolSerializer(serializers.ModelSerializer):
    """Serializer for tools."""
    
    author = AuthorSerializer(read_only=True)
    
    class Meta:
        model = Tool
        fields = [
            'id', 'name', 'slug', 'short_description', 'description',
            'github_url', 'demo_url', 'documentation_url',
            'author', 'tags', 'stars', 'is_featured',
            'created_at', 'updated_at'
        ]


class ToolCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating tools."""
    
    class Meta:
        model = Tool
        fields = [
            'name', 'short_description', 'description',
            'github_url', 'demo_url', 'documentation_url',
            'tags'
        ]


class AnnouncementSerializer(serializers.ModelSerializer):
    """Serializer for announcements."""
    
    class Meta:
        model = Announcement
        fields = [
            'id', 'title', 'description', 'category',
            'link', 'is_featured', 'published_at', 'created_at'
        ]


class CategorySerializer(serializers.Serializer):
    """Serializer for category with counts."""
    
    id = serializers.CharField()
    name = serializers.CharField()
    count = serializers.IntegerField()


class TagSerializer(serializers.Serializer):
    """Serializer for tags."""
    
    name = serializers.CharField()
    count = serializers.IntegerField()


class FeaturedContentSerializer(serializers.Serializer):
    """Serializer for homepage featured content."""
    
    featured_papers = ResearchPaperListSerializer(many=True)
    recent_papers = ResearchPaperListSerializer(many=True)
    announcements = AnnouncementSerializer(many=True)
    featured_tools = ToolSerializer(many=True)
