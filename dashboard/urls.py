from django.urls import path, include
from . import views

urlpatterns = [
    # Main dashboard router
    path('', views.dashboard_router, name='dashboard'),

    # Specific dashboards
    path('public/', views.public_dashboard, name='public_dashboard'),
    path('admin/', views.admin_dashboard, name='admin_dashboard'),

    # AJAX endpoints
    path('api/analytics/', views.dashboard_analytics_api, name='dashboard_analytics_api'),
    path('api/notifications/<int:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'),
    path('api/log-activity/', views.log_user_activity, name='log_user_activity'),

    # API routes for mobile/SPA
    # path('api/', include('dashboards.api.routers')),
]