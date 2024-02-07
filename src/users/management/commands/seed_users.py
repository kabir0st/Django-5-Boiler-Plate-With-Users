import contextlib
from django.core.management.base import BaseCommand
from faker import Faker
from f_seeder import User
from users.models.userbase import UserBase

fake = Faker()


class Command(BaseCommand):
    help = 'Populate dummy data for Students'

    def handle(self, *args, **kwargs):
        print('here triggered')
        with contextlib.suppress(Exception):
            User.objects.create_superuser('admin@admin.com', 'pass')
        for _ in range(10):
            UserBase.objects.create_user(family_name=fake.first_name(),
                                         given_name=fake.first_name(),
                                         email=fake.email(),
                                         password='pass')
        for _ in range(2):
            UserBase.objects.create_agent(family_name=fake.first_name(),
                                          given_name=fake.first_name(),
                                          email=fake.email(),
                                          password='pass',
                                          is_agent=True)

        self.stdout.write(self.style.SUCCESS('Users populated successfully.'))
