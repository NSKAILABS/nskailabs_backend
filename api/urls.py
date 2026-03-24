from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from . import views
from . import auth_views

urlpatterns = [
    # Health check
    path('health/', views.health_check, name='health'),
    
    # Contact form
    path('contact/', views.contact_submit, name='contact'),
    
    # Announcements
    path('announcements/', views.announcements_list, name='announcements'),
    
    # Standard JWT Auth
    path('auth/register/', auth_views.register, name='register'),
    path('auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/me/', auth_views.me, name='me'),
    path('auth/profile/', auth_views.update_profile, name='update_profile'),
    
    # Google OAuth
    path('auth/google/', auth_views.google_auth, name='google_auth'),
    
    # OTP Authentication
    path('auth/otp/send/', auth_views.send_otp, name='send_otp'),
    path('auth/otp/verify/', auth_views.verify_otp, name='verify_otp'),
]