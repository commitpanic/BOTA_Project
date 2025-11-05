"""
Custom management command to create a superuser with random password and email notification.
Usage: python manage.py create_superuser_with_notification
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
import secrets
import string


class Command(BaseCommand):
    help = 'Creates a superuser with a random password and sends it via email'

    def add_arguments(self, parser):
        parser.add_argument(
            '--callsign',
            type=str,
            default='SP3JFB',
            help='Callsign for the superuser (default: SP3JFB)'
        )
        parser.add_argument(
            '--email',
            type=str,
            default='j.f.blaszyk@gmail.com',
            help='Email address for the superuser (default: j.f.blaszyk@gmail.com)'
        )

    def generate_secure_password(self, length=16):
        """Generate a secure random password."""
        alphabet = string.ascii_letters + string.digits + string.punctuation
        # Ensure password has at least one of each type
        password = [
            secrets.choice(string.ascii_lowercase),
            secrets.choice(string.ascii_uppercase),
            secrets.choice(string.digits),
            secrets.choice(string.punctuation),
        ]
        # Fill the rest
        password += [secrets.choice(alphabet) for _ in range(length - 4)]
        # Shuffle
        secrets.SystemRandom().shuffle(password)
        return ''.join(password)

    def handle(self, *args, **options):
        User = get_user_model()
        callsign = options['callsign']
        email = options['email']

        # Check if superuser already exists
        if User.objects.filter(callsign=callsign).exists():
            self.stdout.write(
                self.style.WARNING(f'Superuser with callsign {callsign} already exists!')
            )
            return

        # Generate random password
        password = self.generate_secure_password()

        try:
            # Create superuser
            user = User.objects.create_superuser(
                callsign=callsign,
                email=email,
                password=password
            )
            
            # Mark that password must be changed on first login
            user.force_password_change = True
            user.save()

            self.stdout.write(
                self.style.SUCCESS(f'Successfully created superuser: {callsign}')
            )

            # Send email with credentials
            subject = 'SP_BOTA - Admin Account Created'
            message = f"""Hello {callsign},

Your SP_BOTA administrator account has been created successfully!

Login Details:
--------------
Callsign: {callsign}
Email: {email}
Temporary Password: {password}

IMPORTANT SECURITY NOTICE:
- This is a temporary password
- You MUST change it immediately after your first login
- The system will force you to change your password when you log in
- Do not share this password with anyone
- This email will not be sent again - save your new password securely

Login URL: {settings.ALLOWED_HOSTS[0] if settings.ALLOWED_HOSTS else 'http://localhost:8000'}/login/

After logging in, you will be prompted to change your password.

73!
SP_BOTA Team
"""

            try:
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [email],
                    fail_silently=False,
                )
                self.stdout.write(
                    self.style.SUCCESS(f'Credentials sent to {email}')
                )
                self.stdout.write(
                    self.style.WARNING('Check your email backend (console or SMTP) for the message')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Failed to send email: {e}')
                )
                self.stdout.write(
                    self.style.WARNING(f'TEMPORARY PASSWORD: {password}')
                )
                self.stdout.write(
                    self.style.WARNING('SAVE THIS PASSWORD - IT WILL NOT BE SHOWN AGAIN!')
                )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error creating superuser: {e}')
            )
