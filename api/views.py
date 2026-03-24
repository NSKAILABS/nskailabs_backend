from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.core.mail import send_mail
from django.conf import settings
from .serializers import ContactLeadSerializer
from .models import Announcement


@api_view(['GET'])
def health_check(request):
    """Health check endpoint."""
    return Response({
        'status': 'healthy',
        'service': 'NSKAILabs API',
        'version': '2.0.0'
    })


@api_view(['POST'])
def contact_submit(request):
    """Handle contact form submissions."""
    serializer = ContactLeadSerializer(data=request.data)
    if serializer.is_valid():
        lead = serializer.save()
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


@api_view(['GET'])
@permission_classes([AllowAny])
def announcements_list(request):
    """Get active announcements for the homepage."""
    announcements = Announcement.objects.filter(is_active=True).order_by('-is_featured', '-published_at', '-created_at')[:5]
    
    data = [
        {
            'id': a.id,
            'title': a.title,
            'description': a.description,
            'category': a.category,
            'link': a.link,
            'is_featured': a.is_featured,
            'published_at': a.published_at or a.created_at,
        }
        for a in announcements
    ]
    
    return Response(data)