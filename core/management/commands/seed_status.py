# core/management/commands/seed_status.py
from django.core.management.base import BaseCommand
from core.models import Status


class Command(BaseCommand):
    help = 'Seed workflow status data'

    def handle(self, *args, **options):
        status_data = [
            {
                'status_code': '10',
                'internal_status': 'Draft',
                'external_status': 'Draft',
                'description': 'Member workflow in draft state',
                'parent_code': '1',
            },
            {
                'status_code': '11',
                'internal_status': 'Pending Payment',
                'external_status': 'Pending Payment',
                'description': 'Member has submitted application, payment pending',
                'parent_code': '1',
            },
            {
                'status_code': '12',
                'internal_status': 'Pending Approval',
                'external_status': 'Pending Approval',
                'description': 'After payment, awaiting admin approval',
                'parent_code': '1',
            },
            {
                'status_code': '13',
                'internal_status': 'Approved',
                'external_status': 'Approved',
                'description': 'Membership application approved',
                'parent_code': '1',
            },
            {
                'status_code': '14',
                'internal_status': 'Revise for review',
                'external_status': 'Revise for review',
                'description': 'Member needs to revise application',
                'parent_code': '1',
            },
            {
                'status_code': '15',
                'internal_status': 'Reject',
                'external_status': 'Reject',
                'description': 'Membership application rejected',
                'parent_code': '1',
            },
            {
                'status_code': '16',
                'internal_status': 'Terminated',
                'external_status': 'Terminated',
                'description': 'Membership terminated',
                'parent_code': '1',
            },
        ]

        parent_status = Status.objects.get_or_create(
            status_code='1',
            defaults={
                'internal_status': 'Member Workflow',
                'external_status': 'Member Workflow',
                'description': 'Main workflow for membership applications',
                'parent_code': '',
            }
        )[0]

        created_count = 0
        updated_count = 0

        for status_info in status_data:
            status, created = Status.objects.get_or_create(
                status_code=status_info['status_code'],
                defaults={
                    'internal_status': status_info['internal_status'],
                    'external_status': status_info['external_status'],
                    'description': status_info['description'],
                    'parent': parent_status,
                    'parent_code': status_info['parent_code'],
                }
            )

            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Created status: {status.status_code} - {status.internal_status}'
                    )
                )
            else:
                # Update existing status
                status.internal_status = status_info['internal_status']
                status.external_status = status_info['external_status']
                status.description = status_info['description']
                status.parent = parent_status
                status.parent_code = status_info['parent_code']
                status.save()
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(
                        f'Updated status: {status.status_code} - {status.internal_status}'
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'Seeding complete. Created: {created_count}, Updated: {updated_count}'
            )
        )