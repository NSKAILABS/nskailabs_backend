import uuid
from datetime import timedelta

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.text import slugify


class UserProfile(models.Model):
    """Extended user profile for researchers."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    # Professional info
    bio = models.TextField(blank=True, null=True)
    institution = models.CharField(max_length=200, blank=True, null=True)
    department = models.CharField(max_length=200, blank=True, null=True)
    research_interests = models.JSONField(default=list, blank=True)
    
    # Links
    website = models.URLField(blank=True, null=True)
    google_scholar = models.URLField(blank=True, null=True)
    orcid = models.CharField(max_length=50, blank=True, null=True)
    avatar_url = models.URLField(blank=True, null=True)
    
    # Social
    twitter = models.CharField(max_length=100, blank=True, null=True)
    linkedin = models.URLField(blank=True, null=True)
    
    # Status
    is_contributor = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.email}'s profile"


class MagicLink(models.Model):
    """Magic link tokens for passwordless authentication."""
    email = models.EmailField()
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"MagicLink for {self.email}"

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(minutes=15)
        super().save(*args, **kwargs)

    def is_expired(self):
        return timezone.now() > self.expires_at

    def is_valid(self):
        return not self.is_used and not self.is_expired()

    @classmethod
    def create_for_email(cls, email):
        """Create a new magic link for the given email."""
        # Invalidate any existing unused links for this email
        cls.objects.filter(email=email.lower(), is_used=False).update(is_used=True)
        
        return cls.objects.create(
            email=email.lower(),
            expires_at=timezone.now() + timedelta(minutes=15)
        )


class ResearchPaper(models.Model):
    """Research papers and articles."""
    CATEGORY_CHOICES = [
        ('fundamentals', 'Fundamentals'),
        ('tutorial', 'Tutorial'),
        ('research', 'Research'),
        ('news', 'News'),
        ('review', 'Review'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('review', 'Under Review'),
        ('published', 'Published'),
    ]

    # Basic info
    title = models.CharField(max_length=300)
    slug = models.SlugField(max_length=350, unique=True, blank=True)
    subtitle = models.CharField(max_length=500, blank=True, null=True)
    abstract = models.TextField()
    content = models.TextField(help_text="Markdown content")
    
    # Classification
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='research')
    tags = models.JSONField(default=list, blank=True)
    
    # Authors
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='papers')
    co_authors = models.ManyToManyField(User, related_name='co_authored_papers', blank=True)
    
    # Media & links
    featured_image = models.URLField(blank=True, null=True)
    pdf_url = models.URLField(blank=True, null=True)
    github_url = models.URLField(blank=True, null=True)
    doi = models.CharField(max_length=100, blank=True, null=True)
    
    # Original paper reference
    original_paper_title = models.CharField(max_length=500, blank=True, null=True)
    original_paper_authors = models.TextField(blank=True, null=True)
    original_paper_journal = models.CharField(max_length=300, blank=True, null=True)
    original_paper_year = models.IntegerField(blank=True, null=True)
    original_paper_doi = models.CharField(max_length=100, blank=True, null=True)
    
    # Status & metrics
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    is_featured = models.BooleanField(default=False)
    views = models.PositiveIntegerField(default=0)
    reading_time = models.PositiveIntegerField(default=5, help_text="Estimated reading time in minutes")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ['-published_at', '-created_at']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            while ResearchPaper.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        
        # Calculate reading time (avg 200 words per minute)
        if self.content:
            word_count = len(self.content.split())
            self.reading_time = max(1, word_count // 200)
        
        super().save(*args, **kwargs)

    def increment_views(self):
        self.views += 1
        self.save(update_fields=['views'])

    @property
    def like_count(self):
        return self.likes.count()

    @property
    def comment_count(self):
        return self.comments.filter(is_approved=True).count()


class Comment(models.Model):
    """Comments on research papers."""
    paper = models.ForeignKey(ResearchPaper, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField()
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    
    is_approved = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Comment by {self.author.email} on {self.paper.title[:30]}"


class Like(models.Model):
    """Likes on research papers."""
    paper = models.ForeignKey(ResearchPaper, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['paper', 'user']

    def __str__(self):
        return f"{self.user.email} likes {self.paper.title[:30]}"


class NewsletterSubscriber(models.Model):
    """Newsletter subscribers."""
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=200, blank=True, null=True)
    interests = models.JSONField(default=list, blank=True)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.email


class Tool(models.Model):
    """Open-source tools directory."""
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=250, unique=True, blank=True)
    short_description = models.CharField(max_length=300)
    description = models.TextField()
    
    # Links
    github_url = models.URLField()
    demo_url = models.URLField(blank=True, null=True)
    documentation_url = models.URLField(blank=True, null=True)
    
    # Metadata
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='tools')
    tags = models.JSONField(default=list, blank=True)
    stars = models.PositiveIntegerField(default=0)
    is_featured = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_featured', '-stars', '-created_at']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Tool.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)


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
    """License keys for software access."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='license_keys')
    key = models.CharField(max_length=64, unique=True)
    product = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)
    activated_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    external_reference = models.CharField(max_length=200, blank=True, null=True)

    class Meta:
        ordering = ['-activated_at']

    def __str__(self):
        return f"{self.key[:12]}... - {self.product}"


class Announcement(models.Model):
    """Platform announcements."""
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
