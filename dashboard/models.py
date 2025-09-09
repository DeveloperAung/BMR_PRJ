from django.db import models

from django.db import models
from django.contrib.auth import get_user_model
from core.models import AuditModel

User = get_user_model()


class DashboardWidget(AuditModel):
    """Dashboard widgets configuration"""
    WIDGET_TYPES = [
        ('stats', 'Statistics Card'),
        ('chart', 'Chart'),
        ('table', 'Data Table'),
        ('activity', 'Activity Feed'),
        ('quick_actions', 'Quick Actions'),
    ]

    name = models.CharField(max_length=100)
    widget_type = models.CharField(max_length=20, choices=WIDGET_TYPES)
    title = models.CharField(max_length=200)
    config = models.JSONField(default=dict, help_text="Widget configuration in JSON format")
    order = models.IntegerField(default=0)
    is_staff_only = models.BooleanField(default=False)

    class Meta:
        ordering = ['order', 'name']

    def __str__(self):
        return f"{self.name} ({'Staff' if self.is_staff_only else 'Public'})"


class UserActivity(AuditModel):
    """Track user activities for dashboard feed"""
    ACTION_TYPES = [
        ('login', 'User Login'),
        ('profile_update', 'Profile Updated'),
        ('membership_application', 'Membership Application'),
        ('payment', 'Payment Made'),
        ('document_upload', 'Document Uploaded'),
        ('status_change', 'Status Changed'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    action_type = models.CharField(max_length=30, choices=ACTION_TYPES)
    description = models.CharField(max_length=500)
    metadata = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "User Activities"

    def __str__(self):
        return f"{self.user.username} - {self.get_action_type_display()}"


class Notification(AuditModel):
    """User notifications"""
    NOTIFICATION_TYPES = [
        ('info', 'Information'),
        ('success', 'Success'),
        ('warning', 'Warning'),
        ('error', 'Error'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, default='info')
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    action_url = models.URLField(blank=True, help_text="Optional URL for action button")
    action_text = models.CharField(max_length=50, blank=True, help_text="Text for action button")

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.title}"

    def mark_as_read(self):
        from django.utils import timezone
        self.is_read = True
        self.read_at = timezone.now()
        self.save(update_fields=['is_read', 'read_at'])