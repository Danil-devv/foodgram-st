import json
import os

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files import File
from django.core.management.base import BaseCommand

User = get_user_model()


class Command(BaseCommand):
    help = "Load users from a JSON file with avatars"

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            type=str,
            default=os.path.join(
                settings.BASE_DIR, "..", "data", "users.json"
            ),
            help="Path to the JSON file with user data",
        )
        parser.add_argument(
            "--media-dir",
            type=str,
            default=os.path.join(settings.BASE_DIR, "..", "data"),
            help="Base dir for avatar files"
                 " (relative to json file, by default ../data)",
        )

    def handle(self, *args, **options):
        file_path = os.path.abspath(options["file"])
        media_dir = os.path.abspath(options["media_dir"])
        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f"File not found: {file_path}"))
            return

        with open(file_path, "r", encoding="utf-8") as f:
            users_data = json.load(f)

        created, skipped = 0, 0
        for user_data in users_data:
            email = user_data["email"]
            if User.objects.filter(email=email).exists():
                self.stdout.write(
                    self.style.WARNING(
                        f"User {email} already exists, skipping."
                    )
                )
                skipped += 1
                continue

            password = user_data.pop("password")
            avatar_path = user_data.pop("avatar", None)

            user = User(**user_data)
            user.set_password(password)
            user.save()

            if avatar_path:
                avatar_full_path = os.path.join(media_dir, avatar_path)
                if os.path.exists(avatar_full_path):
                    with open(avatar_full_path, "rb") as avatar_file:
                        user.avatar.save(
                            os.path.basename(avatar_full_path),
                            File(avatar_file),
                            save=True,
                        )
                    self.stdout.write(
                        self.style.SUCCESS(f"Avatar loaded for user {email}.")
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            f"Avatar file not found"
                            f" for user {email}: {avatar_full_path}"
                        )
                    )

            created += 1
            self.stdout.write(self.style.SUCCESS(f"User {email} created."))

        self.stdout.write(
            self.style.SUCCESS(f"Done! Created: {created}, Skipped: {skipped}")
        )
