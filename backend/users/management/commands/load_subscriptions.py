import json
import os

from django.conf import settings
from django.core.management.base import BaseCommand

from users.models import Subscription, User


class Command(BaseCommand):
    help = "Load subscriptions from a JSON file"

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            type=str,
            default=os.path.join(
                settings.BASE_DIR, "..", "data", "subscriptions.json"
            ),
            help="Path to the subscriptions.json file",
        )

    def handle(self, *args, **options):
        path = os.path.abspath(options["file"])
        if not os.path.exists(path):
            self.stdout.write(self.style.ERROR(f"File {path} not found"))
            return
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        added = 0
        for sub in data:
            user = User.objects.filter(email=sub["user_email"]).first()
            author = User.objects.filter(email=sub["author_email"]).first()
            if user and author and user != author:
                obj, created = Subscription.objects.get_or_create(
                    user=user, author=author
                )
                if created:
                    added += 1
        self.stdout.write(
            self.style.SUCCESS(f"Added new subscriptions: {added}")
        )
