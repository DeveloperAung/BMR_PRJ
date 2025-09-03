# core/management/commands/generate_fernet_key.py
from django.core.management.base import BaseCommand
from cryptography.fernet import Fernet
import base64


class Command(BaseCommand):
    help = 'Generate a new Fernet key for encryption'

    def handle(self, *args, **options):
        key = Fernet.generate_key()
        key_string = key.decode()

        self.stdout.write(self.style.SUCCESS(f'Generated Fernet Key: {key_string}'))
        self.stdout.write(self.style.WARNING('Add this to your .env file as:'))
        self.stdout.write(f'FERNET_KEY={key_string}')
        self.stdout.write(self.style.WARNING('Keep this key secret and secure!'))