from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from django.http import JsonResponse
from django.contrib.admin.views.decorators import staff_member_required

from memberships.models import Membership, MembershipPayment
from .models import DashboardWidget, UserActivity, Notification
from core.models import Status

User = get_user_model()


@login_required
def dashboard_router(request):
    """Route users to appropriate dashboard based on staff status"""
    if request.user.is_staff:
        return redirect('admin_dashboard')
    else:
        return redirect('public_dashboard')


@login_required
def public_dashboard(request):
    """Public user dashboard"""
    user = request.user

    # Get user's membership if exists
    try:
        membership = Membership.objects.select_related(
            'membership_type', 'workflow_status', 'profile_info', 'contact_info'
        ).get(user=user)
    except Membership.DoesNotExist:
        membership = None

    # Get recent activities
    recent_activities = UserActivity.objects.filter(
        user=user
    ).order_by('-created_at')[:10]

    # Get unread notifications
    unread_notifications = Notification.objects.filter(
        user=user,
        is_read=False
    ).order_by('-created_at')[:5]

    # Get public dashboard widgets
    widgets = DashboardWidget.objects.filter(
        is_active=True,
        is_staff_only=False
    ).order_by('order')

    # Membership statistics for user
    membership_stats = {
        'has_membership': membership is not None,
        'status': membership.workflow_status.external_status if membership and membership.workflow_status else 'No Application',
        'reference_no': membership.reference_no if membership else None,
        'applied_date': membership.applied_date if membership else None,
        'can_edit': membership.can_edit() if membership else False,
    }

    # Payment information
    payment_info = None
    if membership:
        latest_payment = MembershipPayment.objects.filter(
            membership=membership
        ).order_by('-created_at').first()

        if latest_payment:
            payment_info = {
                'status': latest_payment.status,
                'amount': latest_payment.amount,
                'currency': latest_payment.currency,
                'method': latest_payment.method,
                'created_at': latest_payment.created_at,
            }

    context = {
        'user': user,
        'membership': membership,
        'membership_stats': membership_stats,
        'payment_info': payment_info,
        'recent_activities': recent_activities,
        'unread_notifications': unread_notifications,
        'widgets': widgets,
        'page_title': 'Dashboard',
    }
    return render(request, 'public/dashboard/index.html', context)


@staff_member_required
def admin_dashboard(request):
    """Admin/Staff dashboard with management features"""
    user = request.user

    # Date ranges for analytics
    today = timezone.now().date()
    last_30_days = today - timedelta(days=30)
    last_7_days = today - timedelta(days=7)

    # User statistics
    user_stats = {
        'total_users': User.objects.filter(is_active=True).count(),
        'verified_users': User.objects.filter(is_active=True, is_verified=True).count(),
        'new_users_30d': User.objects.filter(
            is_active=True,
            created_at__date__gte=last_30_days
        ).count(),
        'new_users_7d': User.objects.filter(
            is_active=True,
            created_at__date__gte=last_7_days
        ).count(),
    }

    # Membership statistics
    membership_stats = {
        'total_applications': Membership.objects.count(),
        'pending_approval': Membership.objects.filter(
            workflow_status__status_code__in=['10', '11', '12']  # Draft, Pending Payment, Pending Approval
        ).count(),
        'approved': Membership.objects.filter(
            workflow_status__status_code='13'  # Approved
        ).count(),
        'new_applications_30d': Membership.objects.filter(
            created_at__date__gte=last_30_days
        ).count(),
    }

    # Payment statistics
    payment_stats = {
        'total_payments': MembershipPayment.objects.count(),
        'paid_payments': MembershipPayment.objects.filter(status='paid').count(),
        'pending_payments': MembershipPayment.objects.filter(status__in=['created', 'pending']).count(),
        'total_revenue': MembershipPayment.objects.filter(
            status='paid'
        ).aggregate(total=Count('amount'))['total'] or 0,
    }

    # Recent activities (system-wide for admins)
    recent_activities = UserActivity.objects.select_related('user').order_by('-created_at')[:15]

    # Recent applications requiring attention
    pending_memberships = Membership.objects.select_related(
        'user', 'membership_type', 'workflow_status'
    ).filter(
        workflow_status__status_code__in=['11', '12']  # Pending Payment, Pending Approval
    ).order_by('-created_at')[:10]

    # Get admin dashboard widgets
    widgets = DashboardWidget.objects.filter(
        is_active=True,
        is_staff_only=True
    ).order_by('order')

    # Quick actions data
    quick_actions = [
        {
            'title': 'User Management',
            'url': '/admin/auth/user/',
            'icon': 'fas fa-users',
            'description': 'Manage user accounts'
        },
        {
            'title': 'Membership Applications',
            'url': '/admin/memberships/membership/',
            'icon': 'fas fa-id-card',
            'description': 'Review applications'
        },
        {
            'title': 'Payment Management',
            'url': '/admin/memberships/membershippayment/',
            'icon': 'fas fa-credit-card',
            'description': 'Manage payments'
        },
        {
            'title': 'Generate Reports',
            'url': '#',
            'icon': 'fas fa-chart-bar',
            'description': 'View analytics'
        },
    ]

    context = {
        'user': user,
        'user_stats': user_stats,
        'membership_stats': membership_stats,
        'payment_stats': payment_stats,
        'recent_activities': recent_activities,
        'pending_memberships': pending_memberships,
        'widgets': widgets,
        'quick_actions': quick_actions,
        'page_title': 'Admin Dashboard',
    }

    return render(request, 'dashboards/admin/index.html', context)


@login_required
def dashboard_analytics_api(request):
    """API endpoint for dashboard analytics data"""
    if not request.user.is_staff:
        return JsonResponse({'error': 'Permission denied'}, status=403)

    # Get analytics data based on request parameters
    days = int(request.GET.get('days', 30))
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=days)

    # Daily user registrations
    daily_registrations = []
    for i in range(days):
        date = start_date + timedelta(days=i)
        count = User.objects.filter(
            created_at__date=date,
            is_active=True
        ).count()
        daily_registrations.append({
            'date': date.strftime('%Y-%m-%d'),
            'count': count
        })

    # Daily membership applications
    daily_applications = []
    for i in range(days):
        date = start_date + timedelta(days=i)
        count = Membership.objects.filter(
            created_at__date=date
        ).count()
        daily_applications.append({
            'date': date.strftime('%Y-%m-%d'),
            'count': count
        })

    # Membership status distribution
    status_distribution = []
    statuses = Status.objects.filter(status_code__in=['10', '11', '12', '13', '14', '15', '16'])
    for status in statuses:
        count = Membership.objects.filter(workflow_status=status).count()
        status_distribution.append({
            'status': status.external_status,
            'count': count
        })

    return JsonResponse({
        'daily_registrations': daily_registrations,
        'daily_applications': daily_applications,
        'status_distribution': status_distribution,
    })


@login_required
def mark_notification_read(request, notification_id):
    """Mark a notification as read"""
    try:
        notification = Notification.objects.get(
            id=notification_id,
            user=request.user
        )
        notification.mark_as_read()
        return JsonResponse({'success': True})
    except Notification.DoesNotExist:
        return JsonResponse({'error': 'Notification not found'}, status=404)


@login_required
def log_user_activity(request):
    """Log user activity - called via AJAX"""
    if request.method == 'POST':
        import json
        data = json.loads(request.body)

        activity = UserActivity.objects.create(
            user=request.user,
            action_type=data.get('action_type', 'unknown'),
            description=data.get('description', ''),
            metadata=data.get('metadata', {}),
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
        )

        return JsonResponse({
            'success': True,
            'activity_id': activity.id
        })

    return JsonResponse({'error': 'Invalid method'}, status=405)