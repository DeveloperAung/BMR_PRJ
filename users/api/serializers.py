from django.contrib.auth import authenticate, password_validation
from django.utils import timezone
from rest_framework import serializers
from users.models import User, Profile, Role

class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ("uuid","name")

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ("full_name","avatar","mobile","secondary_mobile")

class UserPublicSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer()
    class Meta:
        model = User
        fields = ("uuid","username","is_verified","profile")

class UserPrivateSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer()
    roles = RoleSerializer(many=True, read_only=True)
    class Meta:
        model = User
        fields = ("uuid","username","email","is_staff","is_verified","is_locked","roles","profile")

class PromoteToStaffSerializer(serializers.Serializer):
    is_staff = serializers.BooleanField()
    roles = serializers.ListField(child=serializers.CharField(), required=False)

class AssignRolesSerializer(serializers.Serializer):
    roles = serializers.ListField(child=serializers.CharField())


class SelfProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ["mobile", "secondary_mobile"]
