# authentication/urls.py - Django Template URLs
from django.urls import path
from . import views

urlpatterns = [
    # Django Template Views
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('verify-otp/', views.verify_otp_view, name='verify_otp'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('membership/', views.membership_view, name='membership'),

    # API Endpoints for React
    path('api/login/', views.api_login, name='api_login'),
    path('api/register/', views.api_register, name='api_register'),
]