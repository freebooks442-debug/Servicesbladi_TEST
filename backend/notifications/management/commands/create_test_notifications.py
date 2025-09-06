from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from custom_requests.models import Notification

User = get_user_model()

class Command(BaseCommand):
    help = 'Create test notifications for all users'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user-id',
            type=int,
            help='Create notifications for specific user ID',
        )

    def handle(self, *args, **options):
        user_id = options.get('user_id')
        
        if user_id:
            users = User.objects.filter(id=user_id)
            if not users.exists():
                self.stdout.write(
                    self.style.ERROR(f'User with ID {user_id} not found')
                )
                return
        else:
            users = User.objects.filter(is_active=True)[:5]  # Limit to first 5 users

        notification_types = [
            ('info', 'Welcome to ServicesBladi!', 'Your account has been successfully created.'),
            ('success', 'Profile Updated', 'Your profile information has been successfully updated.'),
            ('warning', 'Document Required', 'Please upload your identity document to complete verification.'),
            ('error', 'Payment Failed', 'Your last payment attempt was unsuccessful. Please try again.'),
            ('appointment', 'Appointment Confirmed', 'Your appointment with Dr. Smith is confirmed for tomorrow at 3 PM.'),
            ('message', 'New Message', 'You have received a new message from your expert.'),
            ('request', 'Request Update', 'Your service request has been updated by the expert.'),
        ]

        created_count = 0
        for user in users:
            self.stdout.write(f'Creating notifications for user: {user.email}')
            
            for notif_type, title, content in notification_types:
                notification = Notification.objects.create(
                    user=user,
                    type=notif_type,
                    title=title,
                    content=content,
                    is_read=False
                )
                created_count += 1
                self.stdout.write(f'  - Created: {notification.title}')

        # Create some read notifications too
        for user in users:
            read_notification = Notification.objects.create(
                user=user,
                type='info',
                title='System Maintenance',
                content='Scheduled maintenance completed successfully.',
                is_read=True
            )
            created_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {created_count} test notifications'
            )
        )
