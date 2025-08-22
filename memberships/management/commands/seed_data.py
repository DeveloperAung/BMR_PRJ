from django.core.management.base import BaseCommand
from memberships.models import Status, EducationLevel, Institution
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = 'Seed initial data (Education Levels, Institutions)'

    def handle(self, *args, **options):
        self.stdout.write('Seeding Education Levels...')
        education_levels = [
            "Primary",
            "Secondary",
            "Post Secondary",
            "Diploma",
            "Bachelor's Degree",
            "Master's Degree",
            "Doctorate (PhD)",
            "Other",
            "Not Applicable",
        ]
        for level_name in education_levels:
            level, created = EducationLevel.objects.get_or_create(name=level_name)
            if created:
                self.stdout.write(self.style.SUCCESS(f'Successfully created EducationLevel: {level_name}'))
            else:
                self.stdout.write(self.style.WARNING(f'EducationLevel "{level_name}" already exists.'))

        self.stdout.write('\nSeeding Institutions...')
        institutions = [
            "Institute of Technical Education (ITE)",
            "Polytechnic",
            "University",
            "Foreign System School",
            "International School",
            "Private Education Institution",
            "Other",
            "Not Applicable",
        ]
        for inst_name in institutions:
            institution, created = Institution.objects.get_or_create(name=inst_name)
            if created:
                self.stdout.write(self.style.SUCCESS(f'Successfully created Institution: {inst_name}'))
            else:
                self.stdout.write(self.style.WARNING(f'Institution "{inst_name}" already exists.'))

        
        
