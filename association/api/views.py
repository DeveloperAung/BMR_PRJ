from rest_framework import viewsets, permissions
from association.models import Association, AssociationPosts
from association.api.serializers import AssociationSerializer, AssociationPostSerializer


class AssociationViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows associations to be viewed or edited.
    """
    queryset = Association.objects.all()
    serializer_class = AssociationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(modified_by=self.request.user)


class AssociationPostViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows association posts to be viewed or edited.
    """
    queryset = AssociationPosts.objects.all()
    serializer_class = AssociationPostSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(modified_by=self.request.user)
