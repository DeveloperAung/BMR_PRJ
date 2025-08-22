from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model

from core.middleware import get_current_user
from memberships.models import Membership, WorkflowLog

User = get_user_model()

@receiver(pre_save, sender=Membership)
def _capture_previous_status(sender, instance: Membership, **kwargs):
    """
    Before saving, capture the previous workflow_status_id so post_save can detect changes.
    """
    if instance.pk:
        try:
            prev = Membership.objects.only("workflow_status").get(pk=instance.pk)
            instance._prev_workflow_status_id = prev.workflow_status_id
        except Membership.DoesNotExist:
            instance._prev_workflow_status_id = None
    else:
        instance._prev_workflow_status_id = None


@receiver(post_save, sender=Membership)
def _log_status_change(sender, instance: Membership, created: bool, **kwargs):
    """
    If workflow_status changed, insert a WorkflowLog entry.
    Uses CurrentUserMiddleware to attribute action_by when possible.
    """
    prev_id = getattr(instance, "_prev_workflow_status_id", None)
    curr_id = instance.workflow_status_id

    # Only log when status actually changed (and not just created with no status)
    changed = (prev_id != curr_id) and (curr_id is not None)
    if not changed:
        return

    actor = get_current_user()
    if actor and not getattr(actor, "is_authenticated", False):
        actor = None

    WorkflowLog.objects.create(
        membership=instance,
        workflow_status=instance.workflow_status,
        action_by=actor,
        reason=instance.reason,  # optional: copy membership.reason if you use it
    )
