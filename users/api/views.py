from rest_framework import viewsets, mixins
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from drf_spectacular.utils import extend_schema, OpenApiExample

from core.api_schemas import PublicUsersListEnvelopeSerializer, PublicUserEnvelopeSerializer, \
    UserPrivateEnvelopeSerializer
from users.models import User, Profile, Role
from .serializers import (
    UserPublicSerializer, UserPrivateSerializer, ProfileSerializer,
    PromoteToStaffSerializer, AssignRolesSerializer, RoleSerializer, SelfProfileUpdateSerializer
)
from core.responses import ok, fail

class MeViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = UserPrivateSerializer

    @extend_schema(
        tags=["Users"],
        responses={200: UserPrivateEnvelopeSerializer()},
        summary="Get current user"
    )
    @action(detail=False, methods=["GET"])
    def me(self, request):
        return ok({"user": UserPrivateSerializer(request.user).data})

    @extend_schema(
        tags=["Users"],
        request=SelfProfileUpdateSerializer,
        responses={200: UserPrivateEnvelopeSerializer()},
        examples=[
            OpenApiExample(
                "UpdateMobileNumbers",
                value={
                    "mobile": "+12025550123",
                    "secondary_mobile": "+12025550177"
                },
                request_only=True
            )
        ],
        summary="Update only mobile numbers"
    )
    @action(detail=False, methods=["PATCH"])
    def update_profile(self, request):
        profile = request.user.profile
        serializer = SelfProfileUpdateSerializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return ok({"user": UserPrivateSerializer(request.user).data}, "Profile updated")


@extend_schema(tags=["Management - User"])
class PublicUsersViewSet(mixins.RetrieveModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = User.objects.filter(is_active=True, is_verified=True).select_related("profile")
    serializer_class = UserPublicSerializer
    lookup_field = "uuid"
    permission_classes = [AllowAny]

    @extend_schema(
        responses={200: PublicUsersListEnvelopeSerializer()},
        operation_id="public_users_list",
        summary="List verified public users"
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        responses={200: PublicUserEnvelopeSerializer()},
        operation_id="public_users_retrieve",
        summary="Retrieve public user by UUID"
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

@extend_schema(tags=["Management - User"])
class ManagementUsersViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().select_related("profile").prefetch_related("roles")
    serializer_class = UserPrivateSerializer
    permission_classes = [IsAdminUser]

    @extend_schema(
        request=PromoteToStaffSerializer,
        responses={200: UserPrivateEnvelopeSerializer()},
        examples=[OpenApiExample("PromoteUser", value={"is_staff": True, "roles": ["Manager", "Support"]},
                                 request_only=True)],
        summary="Promote/demote and optionally assign roles",
    )
    @action(detail=True, methods=["POST"])
    def promote(self, request, pk=None):
        user = self.get_object()
        ser = PromoteToStaffSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        user.is_staff = ser.validated_data["is_staff"]
        user.save()
        # optional roles in same call
        roles = ser.validated_data.get("roles")
        if roles is not None:
            qs = Role.objects.filter(name__in=roles)
            user.roles.set(qs)
        return ok({"user": UserPrivateSerializer(user).data}, message="User updated.")

    @extend_schema(tags=["Management - User"])
    @action(detail=True, methods=["POST"])
    def roles(self, request, pk=None):
        user = self.get_object()
        ser = AssignRolesSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        qs = Role.objects.filter(name__in=ser.validated_data["roles"])
        user.roles.set(qs)
        return ok({"user": UserPrivateSerializer(user).data}, message="Roles assigned.")

@extend_schema(tags=["Management - Role"])
class RoleViewSet(viewsets.ModelViewSet):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [IsAdminUser]
