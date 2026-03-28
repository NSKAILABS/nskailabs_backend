from django.db.models import Count, Q
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination

from .models import (
    ResearchPaper, Comment, Like, NewsletterSubscriber, 
    Tool, Announcement, ContactLead
)
from .serializers import (
    ContactLeadSerializer, ResearchPaperListSerializer, ResearchPaperDetailSerializer,
    ResearchPaperCreateSerializer, CommentSerializer, CommentCreateSerializer,
    NewsletterSubscriberSerializer, ToolSerializer, ToolCreateSerializer,
    AnnouncementSerializer, CategorySerializer, TagSerializer
)


class StandardPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 50


# =============================================================================
# Health & Utility
# =============================================================================

@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """Health check endpoint."""
    return Response({
        'status': 'healthy',
        'service': 'NSKAILabs API',
        'version': '2.0.0'
    })


# =============================================================================
# Research Papers
# =============================================================================

@api_view(['GET'])
@permission_classes([AllowAny])
def research_list(request):
    """
    List research papers with filtering and pagination.
    Query params: category, tag, search, featured, author, status
    """
    papers = ResearchPaper.objects.filter(status='published')
    
    # Apply filters
    category = request.query_params.get('category')
    if category:
        papers = papers.filter(category=category)
    
    tag = request.query_params.get('tag')
    if tag:
        papers = papers.filter(tags__contains=[tag])
    
    search = request.query_params.get('search')
    if search:
        papers = papers.filter(
            Q(title__icontains=search) |
            Q(abstract__icontains=search) |
            Q(content__icontains=search) |
            Q(tags__contains=[search])
        )
    
    featured = request.query_params.get('featured')
    if featured and featured.lower() == 'true':
        papers = papers.filter(is_featured=True)
    
    author_id = request.query_params.get('author')
    if author_id:
        papers = papers.filter(author_id=author_id)
    
    # Ordering
    ordering = request.query_params.get('ordering', '-published_at')
    valid_orderings = ['published_at', '-published_at', 'views', '-views', 'title', '-title']
    if ordering in valid_orderings:
        papers = papers.order_by(ordering)
    
    # Annotate with counts
    papers = papers.annotate(
        like_count=Count('likes'),
        comment_count=Count('comments', filter=Q(comments__is_approved=True))
    )
    
    # Paginate
    paginator = StandardPagination()
    page = paginator.paginate_queryset(papers, request)
    serializer = ResearchPaperListSerializer(page, many=True)
    return paginator.get_paginated_response(serializer.data)


@api_view(['GET'])
@permission_classes([AllowAny])
def research_detail(request, slug):
    """Get paper detail by slug and increment views."""
    try:
        paper = ResearchPaper.objects.annotate(
            like_count=Count('likes'),
            comment_count=Count('comments', filter=Q(comments__is_approved=True))
        ).get(slug=slug, status='published')
    except ResearchPaper.DoesNotExist:
        return Response(
            {'error': 'Paper not found.'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Increment views
    paper.increment_views()
    
    serializer = ResearchPaperDetailSerializer(paper, context={'request': request})
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([AllowAny])
def research_comments(request, paper_id):
    """Get comments for a paper."""
    try:
        paper = ResearchPaper.objects.get(id=paper_id, status='published')
    except ResearchPaper.DoesNotExist:
        return Response(
            {'error': 'Paper not found.'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    comments = Comment.objects.filter(
        paper=paper,
        is_approved=True,
        parent__isnull=True
    ).order_by('-created_at')
    
    serializer = CommentSerializer(comments, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_comment(request, paper_id):
    """Add a comment to a paper."""
    try:
        paper = ResearchPaper.objects.get(id=paper_id, status='published')
    except ResearchPaper.DoesNotExist:
        return Response(
            {'error': 'Paper not found.'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    serializer = CommentCreateSerializer(data=request.data)
    if serializer.is_valid():
        comment = serializer.save(paper=paper, author=request.user)
        return Response(
            CommentSerializer(comment).data,
            status=status.HTTP_201_CREATED
        )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def toggle_like(request, paper_id):
    """Toggle like on a paper."""
    try:
        paper = ResearchPaper.objects.get(id=paper_id, status='published')
    except ResearchPaper.DoesNotExist:
        return Response(
            {'error': 'Paper not found.'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    like, created = Like.objects.get_or_create(paper=paper, user=request.user)
    
    if not created:
        # Already liked, so unlike
        like.delete()
        return Response({
            'liked': False,
            'like_count': paper.likes.count()
        })
    
    return Response({
        'liked': True,
        'like_count': paper.likes.count()
    })


# =============================================================================
# Categories & Tags
# =============================================================================

@api_view(['GET'])
@permission_classes([AllowAny])
def categories_list(request):
    """List categories with paper counts."""
    categories = []
    category_choices = ResearchPaper.CATEGORY_CHOICES
    
    for cat_id, cat_name in category_choices:
        count = ResearchPaper.objects.filter(
            category=cat_id,
            status='published'
        ).count()
        categories.append({
            'id': cat_id,
            'name': cat_name,
            'count': count
        })
    
    return Response(categories)


@api_view(['GET'])
@permission_classes([AllowAny])
def tags_list(request):
    """List all unique tags with counts."""
    papers = ResearchPaper.objects.filter(status='published')
    
    tag_counts = {}
    for paper in papers:
        for tag in paper.tags:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1
    
    tags = [{'name': name, 'count': count} for name, count in tag_counts.items()]
    tags.sort(key=lambda x: x['count'], reverse=True)
    
    return Response(tags)


# =============================================================================
# Featured Content (Homepage)
# =============================================================================

@api_view(['GET'])
@permission_classes([AllowAny])
def featured_content(request):
    """Get featured content for homepage."""
    # Featured papers
    featured_papers = ResearchPaper.objects.filter(
        status='published',
        is_featured=True
    ).annotate(
        like_count=Count('likes'),
        comment_count=Count('comments', filter=Q(comments__is_approved=True))
    ).order_by('-published_at')[:3]
    
    # Recent papers
    recent_papers = ResearchPaper.objects.filter(
        status='published'
    ).annotate(
        like_count=Count('likes'),
        comment_count=Count('comments', filter=Q(comments__is_approved=True))
    ).order_by('-published_at')[:6]
    
    # Announcements
    announcements = Announcement.objects.filter(
        is_active=True
    ).order_by('-is_featured', '-published_at', '-created_at')[:5]
    
    # Featured tools
    featured_tools = Tool.objects.filter(
        is_featured=True
    ).order_by('-stars')[:4]
    
    return Response({
        'featured_papers': ResearchPaperListSerializer(featured_papers, many=True).data,
        'recent_papers': ResearchPaperListSerializer(recent_papers, many=True).data,
        'announcements': AnnouncementSerializer(announcements, many=True).data,
        'featured_tools': ToolSerializer(featured_tools, many=True).data,
    })


# =============================================================================
# Tools
# =============================================================================

@api_view(['GET'])
@permission_classes([AllowAny])
def tools_list(request):
    """List tools with filtering."""
    tools = Tool.objects.all()
    
    # Filter by tag
    tag = request.query_params.get('tag')
    if tag:
        tools = tools.filter(tags__contains=[tag])
    
    # Filter by featured
    featured = request.query_params.get('featured')
    if featured and featured.lower() == 'true':
        tools = tools.filter(is_featured=True)
    
    # Search
    search = request.query_params.get('search')
    if search:
        tools = tools.filter(
            Q(name__icontains=search) |
            Q(description__icontains=search) |
            Q(short_description__icontains=search)
        )
    
    serializer = ToolSerializer(tools, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([AllowAny])
def tool_detail(request, slug):
    """Get tool detail by slug."""
    try:
        tool = Tool.objects.get(slug=slug)
    except Tool.DoesNotExist:
        return Response(
            {'error': 'Tool not found.'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    serializer = ToolSerializer(tool)
    return Response(serializer.data)


# =============================================================================
# Newsletter
# =============================================================================

@api_view(['POST'])
@permission_classes([AllowAny])
def newsletter_subscribe(request):
    """Subscribe to newsletter."""
    serializer = NewsletterSubscriberSerializer(data=request.data)
    
    if serializer.is_valid():
        email = serializer.validated_data['email']
        
        # Check if already subscribed
        subscriber, created = NewsletterSubscriber.objects.get_or_create(
            email=email,
            defaults={
                'name': serializer.validated_data.get('name', ''),
                'interests': serializer.validated_data.get('interests', [])
            }
        )
        
        if not created:
            # Update existing subscriber
            if not subscriber.is_active:
                subscriber.is_active = True
                subscriber.save()
                return Response({
                    'message': 'Welcome back! Your subscription has been reactivated.'
                })
            return Response({
                'message': 'You are already subscribed to our newsletter.'
            })
        
        return Response({
            'message': 'Thank you for subscribing to our newsletter!'
        }, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def newsletter_unsubscribe(request):
    """Unsubscribe from newsletter."""
    email = request.data.get('email', '').lower().strip()
    
    if not email:
        return Response(
            {'error': 'Email is required.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        subscriber = NewsletterSubscriber.objects.get(email=email)
        subscriber.is_active = False
        subscriber.save()
        return Response({'message': 'You have been unsubscribed.'})
    except NewsletterSubscriber.DoesNotExist:
        return Response(
            {'error': 'Email not found in our subscribers list.'},
            status=status.HTTP_404_NOT_FOUND
        )


# =============================================================================
# Contact
# =============================================================================

@api_view(['POST'])
@permission_classes([AllowAny])
def contact_submit(request):
    """Handle contact form submissions."""
    serializer = ContactLeadSerializer(data=request.data)
    
    if serializer.is_valid():
        lead = serializer.save()
        
        # Send notification email
        try:
            send_mail(
                subject=f"New Contact Lead: {lead.name}",
                message=(
                    f"Name: {lead.name}\n"
                    f"Email: {lead.email}\n"
                    f"Phone: {lead.phone or 'N/A'}\n"
                    f"Organization: {lead.organization or 'N/A'}\n"
                    f"Message:\n{lead.message}"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.DEFAULT_FROM_EMAIL],
                fail_silently=True,
            )
        except Exception:
            pass
        
        return Response(
            {'message': 'Thank you for your interest! We will contact you soon.'},
            status=status.HTTP_201_CREATED
        )
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# =============================================================================
# Announcements
# =============================================================================

@api_view(['GET'])
@permission_classes([AllowAny])
def announcements_list(request):
    """Get active announcements."""
    announcements = Announcement.objects.filter(
        is_active=True
    ).order_by('-is_featured', '-published_at', '-created_at')[:10]
    
    serializer = AnnouncementSerializer(announcements, many=True)
    return Response(serializer.data)
