from django.db import models
from django.contrib.auth.models import AbstractUser, Permission
from django.conf import settings
from core.models import AuditModel


class User(AbstractUser, AuditModel):
    email = models.EmailField(unique=True)
    is_locked = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    otp_code = models.CharField(max_length=4, blank=True, null=True)
    otp_expired_at = models.DateTimeField(blank=True, null=True)
    is_google_login = models.BooleanField(default=False)

    REQUIRED_FIELDS = ["email"]

    def __str__(self):
        return self.username or self.email

class Role(AuditModel):
    name = models.CharField(max_length=100, unique=True)
    permissions = models.ManyToManyField(Permission, blank=True, related_name="roles")
    def __str__(self): return self.name

# user <-> roles
User.add_to_class("roles", models.ManyToManyField(Role, blank=True, related_name="users"))

class Profile(AuditModel):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    full_name = models.CharField(max_length=255)
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)
    mobile = models.CharField(max_length=32)
    secondary_mobile = models.CharField(max_length=32, blank=True, null=True)

    def __str__(self):
        return f"{self.full_name} ({self.user.username})"


