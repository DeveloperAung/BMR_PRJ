from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from .models import User, Profile, Role

@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    fieldsets = DjangoUserAdmin.fieldsets + (
        ("Status", {"fields": ("is_locked","is_verified","is_google_login","otp_code","otp_expired_at","roles")}),
    )
    list_display = ("username","email","is_staff","is_verified","is_locked","is_active")

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user","full_name","mobile")

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    filter_horizontal = ("permissions",)
    list_display = ("name","created_at","is_active")
