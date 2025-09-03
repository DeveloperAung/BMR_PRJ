from django.contrib.auth import authenticate, password_validation, get_user_model
from django.utils import timezone
from rest_framework import serializers
from users.models import Profile
from core.utils.otp import generate_otp, expiry

User = get_user_model()

class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField()
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)
    profile = serializers.DictField()

    def validate(self, attrs):
        if attrs["password"] != attrs["confirm_password"]:
            raise serializers.ValidationError("Passwords do not match.")
        password_validation.validate_password(attrs["password"])
        if not attrs["profile"].get("mobile"):
            raise serializers.ValidationError({"profile": {"mobile": ["This field is required."]}})
        return attrs

    def create(self, validated):
        user = User.objects.create_user(
            username=validated["username"], email=validated["email"], password=validated["password"]
        )
        print('user', user)
        prof_data = validated["profile"]
        profile = getattr(user, "profile", None) or Profile.objects.get_or_create(user=user)[0]

        for field in ["full_name", "mobile", "secondary_mobile"]:
            if field in prof_data:
                setattr(profile, field, prof_data[field])
            # avatar might be a file in multipart—leave to your view; if JSON URL, you can assign string
        if "avatar" in prof_data:
            profile.avatar = prof_data["avatar"]
        profile.save()

        # Profile.objects.create(user=user, **validated["profile"])
        code = generate_otp()
        user.otp_code = code
        user.otp_expired_at = expiry(10)
        user.is_verified = False
        user.is_locked = True
        user.save()
        self.context["otp_code"] = code
        return user

class SendOtpSerializer(serializers.Serializer):
    email = serializers.EmailField()

class VerifyOtpSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(min_length=4, max_length=4)
    def validate(self, attrs):
        try:
            user = User.objects.get(email=attrs["email"])
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found.")
        if not user.otp_code or not user.otp_expired_at:
            raise serializers.ValidationError("No OTP requested.")
        if timezone.now() > user.otp_expired_at:
            raise serializers.ValidationError("OTP expired.")
        if user.otp_code != attrs["code"]:
            raise serializers.ValidationError("Invalid OTP.")
        attrs["user"] = user
        return attrs

class LoginSerializer(serializers.Serializer):
    identifier = serializers.CharField()
    password = serializers.CharField(write_only=True)
    def validate(self, attrs):
        ident = attrs["identifier"]
        pwd = attrs["password"]
        user = authenticate(username=ident, password=pwd)
        if not user:
            try:
                u = User.objects.get(email=ident)
            except User.DoesNotExist:
                raise serializers.ValidationError("Invalid credentials.")
            user = authenticate(username=u.username, password=pwd)
        if not user:
            raise serializers.ValidationError("Invalid credentials.")
        if not user.is_verified:
            raise serializers.ValidationError("Please verify your email to access your account.")
        if user.is_locked:
            raise serializers.ValidationError("Your account is locked. Please verify OTP to unlock your account.")
        attrs["user"] = user
        return attrs

class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(min_length=4, max_length=4)
    new_password = serializers.CharField(write_only=True)
    def validate(self, attrs):
        password_validation.validate_password(attrs["new_password"])
        return attrs

class ForgotUsernameSerializer(serializers.Serializer):
    email = serializers.EmailField()

class GoogleLoginSerializer(serializers.Serializer):
    id_token = serializers.CharField()

class SetPasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(write_only=True)
    def validate(self, attrs):
        password_validation.validate_password(attrs["new_password"])
        return attrs
