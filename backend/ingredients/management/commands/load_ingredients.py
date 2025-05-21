import json
import os

from django.conf import settings
from django.core.management.base import BaseCommand

from ingredients.models import Ingredient


class Command(BaseCommand):
    help = "Downloads ingredients from data/ingredients.json"

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            type=str,
            help="Path to ingredients.json (by default ../data/ingredients.json)",
        )

    def handle(self, *args, **options):
        file_path = options.get("file")
        if not file_path:
            file_path = os.path.join(
                settings.BASE_DIR, "..", "data", "ingredients.json"
            )
            file_path = os.path.abspath(file_path)
        else:
            file_path = os.path.abspath(file_path)

        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f"File {file_path} not found"))
            return

        with open(file_path, encoding="utf-8") as f:
            data = json.load(f)
            added = 0
            for item in data:
                obj, created = Ingredient.objects.get_or_create(
                    name=item["name"],
                    measurement_unit=item["measurement_unit"],
                )
                if created:
                    added += 1
            self.stdout.write(
                self.style.SUCCESS(f"Added new ingredients: {added}")
            )
