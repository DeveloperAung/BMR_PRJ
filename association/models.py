from django.db import models
from core.models import AuditModel
from django.conf import settings


class Association(AuditModel):
    name = models.CharField(max_length=250)
    short_description = models.CharField(max_length=250, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    is_published = models.BooleanField(default=False)
    published_at = models.DateTimeField(blank=True, null=True)
    published_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="%(class)s_published_by",
        null=True,
        blank=True,
    )

    def __str__(self):
            return self.name


class AssociationPosts(AuditModel):
    title = models.CharField(max_length=250, help_text="Title of the post (About Us, Our Objects, etc.)")
    content = models.TextField(help_text="Content of the post")
    is_published = models.BooleanField(default=False)
    published_at = models.DateTimeField(blank=True, null=True)
    published_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="%(class)s_published_by",
        null=True,
    )

    def __str__(self):
        return self.title