"""
Django management command to create an admin user.
Usage: python manage.py create_admin
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from authapp.models import Role

User = get_user_model()


class Command(BaseCommand):
    help = 'Creates an admin user with email admin@rslsolution.com and password admin123456'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            default='admin@rslsolution.com',
            help='Email for the admin user (default: admin@rslsolution.com)',
        )
        parser.add_argument(
            '--password',
            type=str,
            default='admin123456',
            help='Password for the admin user (default: admin123456)',
        )
        parser.add_argument(
            '--full-name',
            type=str,
            default='Admin User',
            help='Full name for the admin user (default: Admin User)',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force update existing user password',
        )

    def handle(self, *args, **options):
        email = options['email']
        password = options['password']
        full_name = options['full_name']
        force = options['force']

        try:
            # Check if user already exists
            user = User.objects.filter(email=email).first()
            
            if user:
                if force:
                    # Update existing user
                    user.set_password(password)
                    user.is_superuser = True
                    user.is_staff = True
                    user.role = Role.ADMIN
                    user.full_name = full_name
                    if not user.username:
                        user.username = email  # Set username to email if not set
                    user.is_active = True
                    user.save()
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'✅ Successfully updated admin user: {email}'
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            f'⚠️  User with email {email} already exists. '
                            f'Use --force to update password.'
                        )
                    )
                    return
            else:
                # Create new admin user
                # Use the same approach as RegisterSerializer
                username = email  # Set username to email
                
                # Check if username already exists
                if User.objects.filter(username=username).exists():
                    username = f"{email}_{User.objects.count()}"  # Make unique
                
                user = User.objects.create(
                    username=username,
                    email=email,
                    full_name=full_name,
                    role=Role.ADMIN,
                    is_staff=True,
                    is_superuser=True,
                    is_active=True,
                )
                user.set_password(password)
                user.save()
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✅ Successfully created admin user: {email}'
                    )
                )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n📧 Email: {email}\n'
                    f'🔑 Password: {password}\n'
                    f'👤 Full Name: {full_name}\n'
                    f'🔐 Role: ADMIN\n'
                    f'✨ Superuser: Yes\n'
                    f'👨‍💼 Staff: Yes\n'
                    f'✅ Active: Yes\n'
                )
            )
            
        except Exception as e:
            import traceback
            self.stdout.write(
                self.style.ERROR(f'❌ Error creating admin user: {str(e)}')
            )
            self.stdout.write(
                self.style.ERROR(f'Traceback: {traceback.format_exc()}')
            )
            raise

