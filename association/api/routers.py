from rest_framework.routers import DefaultRouter
from association.api.views import AssociationViewSet, AssociationPostViewSet

router = DefaultRouter()
router.register(r"associations", AssociationViewSet, basename="associations")
router.register(r"association-posts", AssociationPostViewSet, basename="association-posts")

urlpatterns = router.urls
