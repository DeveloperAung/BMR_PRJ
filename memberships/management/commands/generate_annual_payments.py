from django.core.management.base import BaseCommand
from django.utils import timezone
from memberships.models import Membership, MembershipPayment

class Command(BaseCommand):
    help = "Generate yearly pending payments for all memberships"

    def add_arguments(self, parser):
        parser.add_argument("--year", type=int, default=timezone.now().year)

    def handle(self, *args, **opts):
        year = opts["year"]
        created = 0
        qs = Membership.objects.filter(is_active=True)
        for m in qs:
            amount = (m.membership_type.amount if m.membership_type and m.membership_type.amount is not None else None)
            if amount is None:
                continue  # or choose a default / log
            # avoid duplicates for year
            exists = MembershipPayment.objects.filter(membership=m, period_year=year).exists()
            if exists:
                continue
            MembershipPayment.objects.create(
                membership=m,
                method="bank_transfer",    # generic pending invoice; user can switch to online later
                status="pending",
                amount=amount,
                currency="SGD",
                period_year=year,
                description=f"Membership fee {year}",
            )
            created += 1
        self.stdout.write(self.style.SUCCESS(f"Created {created} payments for {year}"))
