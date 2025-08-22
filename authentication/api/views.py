from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import transaction
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample, inline_serializer

from core.api_schemas import UserPrivateEnvelopeSerializer, OkEnvelopeSerializer, TokensEnvelopeSerializer
from core.responses import ok, fail
from core.utils.emailer import send_otp_email, send_username_email
from core.utils.otp import generate_otp, expiry
from core.utils.google_auth import verify_google_id_token
from users.models import Profile
from .serializers import (
    RegisterSerializer, SendOtpSerializer, VerifyOtpSerializer, LoginSerializer,
    ForgotPasswordSerializer, ResetPasswordSerializer, ForgotUsernameSerializer,
    GoogleLoginSerializer, SetPasswordSerializer
)
from rest_framework import serializers

User = get_user_model()

@extend_schema(
    tags=["Auth"],
    request=RegisterSerializer,
    responses={201: OpenApiResponse(UserPrivateEnvelopeSerializer(), description="Registered. OTP sent.")},
    examples=[
        OpenApiExample(
            "RegisterRequest",
            value={
                "username": "jdoe",
                "email": "jdoe@example.com",
                "password": "StrongPass123!",
                "confirm_password": "StrongPass123!",
                "profile": {"full_name": "John Doe", "mobile": "+12025550123"}
            },
            request_only=True,
        )
    ],
)
@api_view(["POST"])
def register(request):
    ser = RegisterSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    with transaction.atomic():
        user = ser.save()
        send_otp_email(user.email, ser.context["otp_code"])
    return ok({"user": {"username": user.username, "email": user.email}}, "Registered. OTP sent.", 201)

@extend_schema(
    tags=["Auth"],
    request=SendOtpSerializer,
    responses={200: OkEnvelopeSerializer},
    examples=[OpenApiExample("SendOtp", value={"email": "jdoe@example.com"}, request_only=True)],
)
@api_view(["POST"])
def send_otp(request):
    ser = SendOtpSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    try:
        user = User.objects.get(email=ser.validated_data["email"])
    except User.DoesNotExist:
        return fail({"email": ["User not found."]}, status=404)
    code = generate_otp()
    user.otp_code = code
    user.otp_expired_at = expiry(10)
    user.is_locked = True
    user.save()
    send_otp_email(user.email, code)
    return ok(message="OTP sent.")

@extend_schema(
    tags=["Auth"],
    request=VerifyOtpSerializer,
    responses={200: UserPrivateEnvelopeSerializer()},
    examples=[OpenApiExample("VerifyOtp", value={"email": "jdoe@example.com", "code": "0421"}, request_only=True)],
)
@api_view(["POST"])
def verify_otp(request):
    ser = VerifyOtpSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    user = ser.validated_data["user"]
    user.is_verified = True
    user.is_locked = False
    user.otp_code = None
    user.otp_expired_at = None
    user.save()
    return ok(message="Email verified.")

@extend_schema(
    tags=["Auth"],
    request=LoginSerializer,
    responses={200: TokensEnvelopeSerializer},
    examples=[OpenApiExample("Login", value={"identifier": "jdoe", "password": "StrongPass123!"}, request_only=True)],
)
@api_view(["POST"])
def login(request):
    ser = LoginSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    user = ser.validated_data["user"]
    refresh = RefreshToken.for_user(user)
    return ok({"access": str(refresh.access_token), "refresh": str(refresh)},"Logged in.")


@extend_schema(
    tags=["Auth"],
    request=inline_serializer(
        name="LogoutRequest",
        fields={"refresh": serializers.CharField()}
    ),
    responses={200: OkEnvelopeSerializer},
    examples=[OpenApiExample("Logout", value={"refresh": "REFRESH_TOKEN_HERE"}, request_only=True)],
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout(request):
    token = request.data.get("refresh")
    if not token:
        return fail({"refresh": ["This field is required."]})
    try:
        RefreshToken(token).blacklist()
    except Exception:
        return fail("Invalid refresh token.", status=400)
    return ok(message="Logged out.")


@extend_schema(
    tags=["Auth"],
    request=ForgotPasswordSerializer,
    responses={200: OkEnvelopeSerializer},
    examples=[OpenApiExample("ForgotPassword", value={"email": "jdoe@example.com"}, request_only=True)],
)
@api_view(["POST"])
def forgot_password(request):
    ser = ForgotPasswordSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    try:
        user = User.objects.get(email=ser.validated_data["email"])
    except User.DoesNotExist:
        return ok(message="If the email exists, an OTP has been sent.")
    code = generate_otp()
    user.otp_code = code
    user.otp_expired_at = expiry(10)
    user.is_locked = True
    user.save()
    send_otp_email(user.email, code)
    return ok(message="OTP sent to email.")


@extend_schema(
    tags=["Auth"],
    request=ResetPasswordSerializer,
    responses={200: OkEnvelopeSerializer},
    examples=[OpenApiExample("ResetPassword", value={"email": "jdoe@example.com", "code": "0421", "new_password": "NewStrongPass!1"}, request_only=True)],
)
@api_view(["POST"])
def reset_password(request):
    ser = ResetPasswordSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    try:
        user = User.objects.get(email=ser.validated_data["email"])
    except User.DoesNotExist:
        return fail("Invalid code or email.")
    if user.otp_code != ser.validated_data["code"] or not user.otp_expired_at or timezone.now() > user.otp_expired_at:
        return fail("Invalid or expired OTP.")
    user.set_password(ser.validated_data["new_password"])
    user.is_locked = False
    user.otp_code = None
    user.otp_expired_at = None
    user.save()
    return ok(message="Password reset successful.")


@extend_schema(
    tags=["Auth"],
    request=ForgotUsernameSerializer,
    responses={200: OkEnvelopeSerializer},
    examples=[OpenApiExample("ForgotUsername", value={"email": "jdoe@example.com"}, request_only=True)],
)
@api_view(["POST"])
def forgot_username(request):
    ser = ForgotUsernameSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    try:
        user = User.objects.get(email=ser.validated_data["email"])
    except User.DoesNotExist:
        return ok(message="If the email exists, the username has been sent.")
    send_username_email(user.email, user.username)
    return ok(message="Username sent to email.")


@extend_schema(
    tags=["Auth"],
    request=GoogleLoginSerializer,
    responses={200: TokensEnvelopeSerializer},
    examples=[OpenApiExample("GoogleLogin", value={"id_token": "GOOGLE_ID_TOKEN"}, request_only=True)],
)
@api_view(["POST"])
def google_login(request):
    ser = GoogleLoginSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    info = verify_google_id_token(ser.validated_data["id_token"])
    email = info.get("email")
    if not email:
        return fail("Google token missing email.", status=400)
    user, created = User.objects.get_or_create(email=email, defaults={
        "username": email.split("@")[0],
        "is_verified": info.get("email_verified", False),
        "is_google_login": True,
        "is_locked": False,
    })

    # Update the (auto-created) profile
    profile = getattr(user, "profile", None) or Profile.objects.get_or_create(user=user)[0]
    if info.get("name"):
        profile.full_name = info["name"]
    # picture is a URL; only set if you handle remote fetch elsewhere
    profile.save()
    #
    # if created and not hasattr(user, "profile"):
    #     Profile.objects.create(user=user, full_name=info.get("name") or user.username, mobile="")
    refresh = RefreshToken.for_user(user)
    return ok({"access": str(refresh.access_token), "refresh": str(refresh)}, "Google login successful.")


@extend_schema(
    tags=["Auth"],
    request=SetPasswordSerializer,
    responses={200: OkEnvelopeSerializer},
    examples=[OpenApiExample("SetPassword", value={"new_password": "StrongPass!234"}, request_only=True)],
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def set_password(request):
    if not request.user.is_google_login:
        return fail("Only Google users can set password with this endpoint.", status=400)
    ser = SetPasswordSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    request.user.set_password(ser.validated_data["new_password"])
    request.user.save()
    return ok(message="Password set.")
