from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from . import views
from . import auth_views

urlpatterns = [
    # ==========================================================================
    # Health Check
    # ==========================================================================
    path('health/', views.health_check, name='health'),
    
    # ==========================================================================
    # Authentication (Magic Link)
    # ==========================================================================
    path('auth/request-magic-link/', auth_views.request_magic_link, name='request_magic_link'),
    path('auth/verify-magic-link/', auth_views.verify_magic_link, name='verify_magic_link'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/logout/', auth_views.logout, name='logout'),
    path('auth/user/', auth_views.get_user, name='get_user'),
    path('auth/profile/', auth_views.update_profile, name='update_profile'),
    
    # ==========================================================================
    # Research Papers
    # ==========================================================================
    path('research/', views.research_list, name='research_list'),
    path('research/<slug:slug>/', views.research_detail, name='research_detail'),
    path('research/<int:paper_id>/comments/', views.research_comments, name='research_comments'),
    path('research/<int:paper_id>/add_comment/', views.add_comment, name='add_comment'),
    path('research/<int:paper_id>/like/', views.toggle_like, name='toggle_like'),
    
    # ==========================================================================
    # Categories & Tags
    # ==========================================================================
    path('categories/', views.categories_list, name='categories'),
    path('tags/', views.tags_list, name='tags'),
    
    # ==========================================================================
    # Featured Content (Homepage)
    # ==========================================================================
    path('featured/', views.featured_content, name='featured'),
    
    # ==========================================================================
    # Tools
    # ==========================================================================
    path('tools/', views.tools_list, name='tools_list'),
    path('tools/<slug:slug>/', views.tool_detail, name='tool_detail'),
    
    # ==========================================================================
    # Newsletter
    # ==========================================================================
    path('newsletter/subscribe/', views.newsletter_subscribe, name='newsletter_subscribe'),
    path('newsletter/unsubscribe/', views.newsletter_unsubscribe, name='newsletter_unsubscribe'),
    
    # ==========================================================================
    # Contact
    # ==========================================================================
    path('contact/', views.contact_submit, name='contact'),
    
    # ==========================================================================
    # Announcements
    # ==========================================================================
    path('announcements/', views.announcements_list, name='announcements'),
]
