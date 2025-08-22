from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver

from core.models import Status
from memberships.models import MembershipPayment, PaymentLog

@receiver(pre_save, sender=MembershipPayment)
def _capture_payment_status(sender, instance: MembershipPayment, **kwargs):
    if instance.pk:
        try:
            prev = MembershipPayment.objects.only("status").get(pk=instance.pk)
            instance._prev_status = prev.status
        except MembershipPayment.DoesNotExist:
            instance._prev_status = None
    else:
        instance._prev_status = None

@receiver(post_save, sender=MembershipPayment)
def _log_payment_status(sender, instance: MembershipPayment, created: bool, **kwargs):
    prev = getattr(instance, "_prev_status", None)
    if created:
        PaymentLog.objects.create(payment=instance, old_status=None, new_status=instance.status, note="created")
    elif prev != instance.status:
        PaymentLog.objects.create(payment=instance, old_status=prev, new_status=instance.status)


@receiver(post_save, sender=MembershipPayment)
def _maybe_advance_membership(sender, instance: MembershipPayment, created: bool, **kwargs):
    # when a payment turns paid, move membership to next status (e.g., "pending_approval": code "12")
    if instance.status == "paid":
        m = instance.membership
        try:
            next_status = Status.objects.get(status_code="12")  # adjust to your next step
        except Status.DoesNotExist:
            return
        if not m.workflow_status or m.workflow_status.status_code != "12":
            m.workflow_status = next_status
            m.save()