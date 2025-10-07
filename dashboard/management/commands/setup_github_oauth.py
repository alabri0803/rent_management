from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp


class Command(BaseCommand):
    help = 'Setup GitHub OAuth application for django-allauth'

    def add_arguments(self, parser):
        parser.add_argument('--client-id', type=str, help='GitHub OAuth Client ID')
        parser.add_argument('--client-secret', type=str, help='GitHub OAuth Client Secret')

    def handle(self, *args, **options):
        client_id = options.get('client_id')
        client_secret = options.get('client_secret')

        if not client_id or not client_secret:
            self.stdout.write(self.style.ERROR('Please provide both --client-id and --client-secret'))
            self.stdout.write(self.style.WARNING('\nTo get GitHub OAuth credentials:'))
            self.stdout.write('1. Go to https://github.com/settings/developers')
            self.stdout.write('2. Click "New OAuth App"')
            self.stdout.write('3. Fill in:')
            self.stdout.write('   - Application name: Rent Management System')
            self.stdout.write('   - Homepage URL: https://adminalabrialabri.pythonanywhere.com')
            self.stdout.write('   - Authorization callback URL: https://adminalabrialabri.pythonanywhere.com/accounts/github/login/callback/')
            self.stdout.write('4. Copy the Client ID and Client Secret')
            self.stdout.write('\nThen run:')
            self.stdout.write('python manage.py setup_github_oauth --client-id YOUR_CLIENT_ID --client-secret YOUR_CLIENT_SECRET')
            return

        # Get or create the site
        site = Site.objects.get_current()

        # Create or update the GitHub social app
        github_app, created = SocialApp.objects.get_or_create(
            provider='github',
            defaults={
                'name': 'GitHub',
                'client_id': client_id,
                'secret': client_secret,
            }
        )

        if not created:
            github_app.client_id = client_id
            github_app.secret = client_secret
            github_app.save()

        # Add the site to the app
        if site not in github_app.sites.all():
            github_app.sites.add(site)

        action = 'Created' if created else 'Updated'
        self.stdout.write(self.style.SUCCESS(f'{action} GitHub OAuth app successfully!'))
        self.stdout.write(f'Provider: {github_app.provider}')
        self.stdout.write(f'Client ID: {github_app.client_id}')
        self.stdout.write(f'Sites: {", ".join([s.domain for s in github_app.sites.all()])}')
