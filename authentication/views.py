# authentication/views.py - Django Template Views
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as django_login, logout as django_logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth import get_user_model
from django.utils import timezone
import json

from core.utils.otp import generate_otp, expiry
from core.utils.emailer import send_otp_email
from users.models import Profile

User = get_user_model()


def login_view(request):
    """Django template-based login view"""
    if request.method == 'POST':
        identifier = request.POST.get('username')
        password = request.POST.get('password')

        # Try to authenticate with username first
        user = authenticate(request, username=identifier, password=password)

        # If that fails, try with email
        if not user:
            try:
                user_obj = User.objects.get(email=identifier)
                user = authenticate(request, username=user_obj.username, password=password)
            except User.DoesNotExist:
                pass

        if user:
            if not user.is_verified:
                messages.error(request, 'Please verify your email to access your account.')
                return render(request, 'auth/login.html')

            if user.is_locked:
                messages.error(request, 'Your account is locked. Please verify OTP to unlock.')
                return render(request, 'auth/login.html')

            django_login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')

            # Redirect to dashboard or membership page
            next_url = request.GET.get('next', reverse('dashboard'))
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid credentials.')

    return render(request, 'auth/login.html')


def register_view(request):
    """Django template-based registration view"""
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        # Validation
        errors = {}

        if User.objects.filter(username=username).exists():
            errors['username'] = 'Username already exists.'

        if User.objects.filter(email=email).exists():
            errors['email'] = 'Email already exists.'

        if password1 != password2:
            errors['password2'] = 'Passwords do not match.'

        if len(password1) < 8:
            errors['password1'] = 'Password must be at least 8 characters long.'

        if errors:
            return render(request, 'auth/register.html', {
                'errors': errors,
                'form_data': request.POST
            })

        # Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password1
        )

        # Generate OTP
        code = generate_otp()
        user.otp_code = code
        user.otp_expired_at = expiry(10)
        user.is_verified = False
        user.is_locked = True
        user.save()

        # Create profile
        Profile.objects.get_or_create(
            user=user,
            defaults={
                'full_name': username,
                'mobile': ''
            }
        )

        # Send OTP email
        send_otp_email(user.email, code)

        messages.success(request, 'Registration successful! Please check your email for verification code.')
        return redirect('verify_otp')

    return render(request, 'auth/register.html')


def verify_otp_view(request):
    """OTP verification view"""
    if request.method == 'POST':
        email = request.POST.get('email')
        code = request.POST.get('code')

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            messages.error(request, 'User not found.')
            return render(request, 'auth/verify_otp.html')

        if not user.otp_code or not user.otp_expired_at:
            messages.error(request, 'No OTP requested.')
            return render(request, 'auth/verify_otp.html')

        if timezone.now() > user.otp_expired_at:
            messages.error(request, 'OTP expired. Please request a new one.')
            return render(request, 'auth/verify_otp.html')

        if user.otp_code != code:
            messages.error(request, 'Invalid OTP.')
            return render(request, 'auth/verify_otp.html')

        # Verify user
        user.is_verified = True
        user.is_locked = False
        user.otp_code = None
        user.otp_expired_at = None
        user.save()

        messages.success(request, 'Email verified successfully! You can now login.')
        return redirect('login')

    return render(request, 'auth/verify_otp.html')


@login_required
def dashboard_view(request):
    """Dashboard after login"""
    return render(request, 'public/dashboard/index.html', {
        'user': request.user
    })


@login_required
def membership_view(request):
    """Membership application view"""
    return render(request, 'membership/application.html')


def logout_view(request):
    """Logout view"""
    django_logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('login')


# ===========================================
# API Views for React Frontend
# ===========================================

@csrf_exempt
@require_http_methods(["POST"])
def api_login(request):
    """API endpoint for React login"""
    try:
        data = json.loads(request.body)
        identifier = data.get('identifier')
        password = data.get('password')

        # Try authentication
        user = authenticate(request, username=identifier, password=password)

        if not user:
            try:
                user_obj = User.objects.get(email=identifier)
                user = authenticate(request, username=user_obj.username, password=password)
            except User.DoesNotExist:
                pass

        if not user:
            return JsonResponse({
                'success': False,
                'message': 'Invalid credentials'
            }, status=400)

        if not user.is_verified:
            return JsonResponse({
                'success': False,
                'message': 'Please verify your email to access your account.'
            }, status=400)

        if user.is_locked:
            return JsonResponse({
                'success': False,
                'message': 'Your account is locked. Please verify OTP to unlock.'
            }, status=400)

        django_login(request, user)

        return JsonResponse({
            'success': True,
            'message': f'Welcome back, {user.username}!',
            'data': {
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'is_staff': user.is_staff
                }
            }
        })

    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def api_register(request):
    """API endpoint for React registration"""
    try:
        data = json.loads(request.body)
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        confirm_password = data.get('confirm_password')

        # Validation
        if User.objects.filter(username=username).exists():
            return JsonResponse({
                'success': False,
                'message': 'Username already exists'
            }, status=400)

        if User.objects.filter(email=email).exists():
            return JsonResponse({
                'success': False,
                'message': 'Email already exists'
            }, status=400)

        if password != confirm_password:
            return JsonResponse({
                'success': False,
                'message': 'Passwords do not match'
            }, status=400)

        # Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        # Generate OTP
        code = generate_otp()
        user.otp_code = code
        user.otp_expired_at = expiry(10)
        user.is_verified = False
        user.is_locked = True
        user.save()

        # Create profile
        Profile.objects.get_or_create(
            user=user,
            defaults={'full_name': username, 'mobile': ''}
        )

        # Send OTP
        send_otp_email(user.email, code)

        return JsonResponse({
            'success': True,
            'message': 'Registration successful! Please check your email for verification code.',
            'data': {
                'email': user.email
            }
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)