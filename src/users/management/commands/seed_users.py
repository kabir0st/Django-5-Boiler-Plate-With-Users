import contextlib
from django.core.management.base import BaseCommand
from faker import Faker
from f_seeder import User
from users.models.users import UserBase

fake = Faker()


class Command(BaseCommand):
    help = 'Populate dummy data for Students'

    def handle(self, *args, **kwargs):
        print('here triggered')
        with contextlib.suppress(Exception):
            User.objects.create_superuser('admin@admin.com', 'pass')
        for _ in range(50):
            with contextlib.suppress(Exception):
                UserBase.objects.create(
                    family_name=fake.first_name(),
                    given_name=fake.first_name(),
                    last_name=fake.last_name(),
                    email=fake.email(),
                    phone_number=fake.phone_number(),
                )

        self.stdout.write(self.style.SUCCESS('Users populated successfully.'))
