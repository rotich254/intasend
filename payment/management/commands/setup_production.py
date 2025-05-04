import os
from django.core.management.base import BaseCommand
from django.core.management import call_command


class Command(BaseCommand):
    help = 'Sets up the application for production'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting production setup...'))
        
        # Collect static files
        self.stdout.write('Collecting static files...')
        call_command('collectstatic', '--noinput')
        
        # Apply migrations
        self.stdout.write('Applying database migrations...')
        call_command('migrate', '--noinput')
        
        # Check for deployment issues
        self.stdout.write('Checking for deployment issues...')
        call_command('check', '--deploy')
        
        self.stdout.write(self.style.SUCCESS('Production setup complete!'))
        self.stdout.write(self.style.WARNING(
            'Important: Make sure to update the ALLOWED_HOSTS setting with your domain name.'
        )) 