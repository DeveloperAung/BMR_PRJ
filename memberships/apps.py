from django.apps import AppConfig


class MembershipsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'memberships'
    verbose_name = "Memberships"

    def ready(self):
        from . import signals
        from . import payment_signals