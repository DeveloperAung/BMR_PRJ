from rest_framework import serializers
from association.models import Association, AssociationPosts


class AssociationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Association
        fields = [
            'id', 'name', 'short_description', 'description',
            'is_published', 'published_at', 'published_by',
            'created_at', 'created_by', 'modified_at', 'modified_by'
        ]
        read_only_fields = ['id', 'created_at', 'created_by', 'modified_at', 'modified_by']


class AssociationPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssociationPosts
        fields = [
            'id', 'title', 'content', 'is_published', 'published_at', 'published_by',
            'created_at', 'created_by', 'modified_at', 'modified_by'
        ]
        read_only_fields = ['id', 'created_at', 'created_by', 'modified_at', 'modified_by']
