from rest_framework.routers import DefaultRouter
from .views import PublicUsersViewSet, MeViewSet, ManagementUsersViewSet, RoleViewSet

router = DefaultRouter()
router.register(r"public", PublicUsersViewSet, basename="public-users")
router.register(r"", MeViewSet, basename="me")
router.register(r"", ManagementUsersViewSet, basename="mgmt-users")
router.register(r"roles", RoleViewSet, basename="roles")
urlpatterns = router.urls
