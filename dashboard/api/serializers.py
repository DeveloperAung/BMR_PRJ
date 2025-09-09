from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta

from dashboards.models import DashboardWidget, UserActivity, Notification
from memberships.models import Membership, MembershipPayment
from memberships.api.serializers import MembershipReadSerializer

User = get_user_model()


class DashboardWidgetSerializer(serializers.ModelSerializer):
    class Meta:
        model = DashboardWidget
        fields = ['uuid', 'name', 'widget_type', 'title', 'config', 'order']


class UserActivitySerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.username', read_only=True)
    action_display = serializers.CharField(source='get_action_type_display', read_only=True)

    class Meta:
        model = UserActivity
        fields = ['uuid', 'user_name', 'action_type', 'action_display',
                  'description', 'metadata', 'created_at']


class NotificationSerializer(serializers.ModelSerializer):
    type_display = serializers.CharField(source='get_notification_type_display', read_only=True)

    class Meta:
        model = Notification
        fields = ['uuid', 'title', 'message', 'notification_type', 'type_display',
                  'is_read', 'read_at', 'action_url', 'action_text', 'created_at']


class PublicDashboardSerializer(serializers.Serializer):
    """Serializer for public user dashboard data"""
    user = serializers.SerializerMethodField()
    membership = serializers.SerializerMethodField()
    membership_stats = serializers.SerializerMethodField()
    payment_info = serializers.SerializerMethodField()
    recent_activities = UserActivitySerializer(many=True, read_only=True)
    unread_notifications = NotificationSerializer(many=True, read_only=True)
    widgets = DashboardWidgetSerializer(many=True, read_only=True)

    def get_user(self, obj):
        from users.api.serializers import UserPrivateSerializer
        return UserPrivateSerializer(obj['user']).data

    def get_membership(self, obj):
        membership = obj.get('membership')
        if membership:
            return MembershipReadSerializer(membership, context=self.context).data
        return None

    def get_membership_stats(self, obj):
        return obj.get('membership_stats', {})

    def get_payment_info(self, obj):
        return obj.get('payment_info')


class AdminStatsSerializer(serializers.Serializer):
    """Admin dashboard statistics"""
    total_users = serializers.IntegerField()
    verified_users = serializers.IntegerField()
    new_users_30d = serializers.IntegerField()
    new_users_7d = serializers.IntegerField()


class MembershipStatsSerializer(serializers.Serializer):
    """Membership statistics"""
    total_applications = serializers.IntegerField()
    pending_approval = serializers.IntegerField()
    approved = serializers.IntegerField()
    new_applications_30d = serializers.IntegerField()


class PaymentStatsSerializer(serializers.Serializer):
    """Payment statistics"""
    total_payments = serializers.IntegerField()
    paid_payments = serializers.IntegerField()
    pending_payments = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=10, decimal_places=2)


class QuickActionSerializer(serializers.Serializer):
    """Quick action items"""
    title = serializers.CharField()
    url = serializers.URLField()
    icon = serializers.CharField()
    description = serializers.CharField()


class AdminDashboardSerializer(serializers.Serializer):
    """Serializer for admin dashboard data"""
    user = serializers.SerializerMethodField()
    user_stats = AdminStatsSerializer()
    membership_stats = MembershipStatsSerializer()
    payment_stats = PaymentStatsSerializer()
    recent_activities = UserActivitySerializer(many=True, read_only=True)
    pending_memberships = MembershipReadSerializer(many=True, read_only=True)
    widgets = DashboardWidgetSerializer(many=True, read_only=True)
    quick_actions = QuickActionSerializer(many=True, read_only=True)

    def get_user(self, obj):
        from users.api.serializers import UserPrivateSerializer
        return UserPrivateSerializer(obj['user']).data


class AnalyticsDataSerializer(serializers.Serializer):
    """Analytics data for charts"""
    daily_registrations = serializers.ListSerializer(
        child=serializers.DictField()
    )
    daily_applications = serializers.ListSerializer(
        child=serializers.DictField()
    )
    status_distribution = serializers.ListSerializer(
        child=serializers.DictField()
    )


class LogActivitySerializer(serializers.Serializer):
    """Log user activity"""
    action_type = serializers.ChoiceField(choices=UserActivity.ACTION_TYPES)
    description = serializers.CharField(max_length=500)
    metadata = serializers.JSONField(required=False, default=dict)

    def create(self, validated_data):
        request = self.context['request']
        return UserActivity.objects.create(
            user=request.user,
            action_type=validated_data['action_type'],
            description=validated_data['description'],
            metadata=validated_data.get('metadata', {}),
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
        )