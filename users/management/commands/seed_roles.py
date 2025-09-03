from django.core.management.base import BaseCommand
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from users.models import Role

ROLE_DEFINITIONS = {
    # super admin role for completeness (in practice, rely on is_superuser)
    "Admin": {
        "permissions": "__all__",  # attach all permissions in DB
    },
    "Manager": {
        # broad CRUD over users & profiles + view permissions elsewhere
        "permissions": [
            # users app permissions (Django auto-generates add/change/delete/view)
            "users.add_user", "users.change_user", "users.view_user",
            "users.add_profile", "users.change_profile", "users.view_profile",
            "users.add_role", "users.change_role", "users.view_role",
        ]
    },
    "Support": {
        "permissions": [
            "users.view_user", "users.view_profile", "users.view_role",
            "users.change_profile",
        ]
    },
    "Viewer": {
        "permissions": [
            "users.view_user", "users.view_profile", "users.view_role",
        ]
    },
}

def all_permissions():
    return Permission.objects.all()

def permissions_from_codenames(codenames):
    perms = Permission.objects.filter(
        codename__in=[cn.split(".")[-1] for cn in codenames]
    )
    # if labels like "app_label.codename" were supplied, filter by both
    by_label = [cn for cn in codenames if "." in cn]
    if by_label:
        # union: keep those already matched; add explicit pairs
        extra = Permission.objects.none()
        for entry in by_label:
            app_label, codename = entry.split(".", 1)
            ct = ContentType.objects.filter(app_label=app_label).values_list("id", flat=True)
            extra = extra | Permission.objects.filter(content_type_id__in=ct, codename=codename)
        perms = (perms | extra).distinct()
    return perms

class Command(BaseCommand):
    help = "Seed default Roles and attach permissions"

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true", help="Delete existing roles before seeding")

    @transaction.atomic
    def handle(self, *args, **options):
        if options["reset"]:
            Role.objects.all().delete()
            self.stdout.write(self.style.WARNING("Deleted existing roles."))

        for role_name, cfg in ROLE_DEFINITIONS.items():
            role, created = Role.objects.get_or_create(name=role_name)
            if cfg["permissions"] == "__all__":
                perms = all_permissions()
            else:
                perms = permissions_from_codenames(cfg["permissions"])
            role.permissions.set(perms)
            role.save()
            self.stdout.write(self.style.SUCCESS(
                f"{'Created' if created else 'Updated'} role '{role_name}' with {perms.count()} permissions"
            ))

        self.stdout.write(self.style.SUCCESS("Seeding complete."))
