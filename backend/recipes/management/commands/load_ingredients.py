import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from recipes.models import Ingredient


class Command(BaseCommand):
    help = "Load ingredients from JSON file"

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            type=str,
            help="Path to ingredients.json "
                 "(by default ../data/ingredients.json)",
        )

    def handle(self, *args, **options):
        """
        Загружает ингредиенты из JSON одним bulk-запросом.
        Создаются только отсутствующие записи.
        """
        file_path = Path()
        try:
            file_path = Path(options.get("file") or
                             Path(settings.BASE_DIR).resolve().parent
                             / "data" / "ingredients.json").resolve()

            with file_path.open(encoding="utf-8") as fh:
                items = json.load(fh)

            if not isinstance(items, list):
                self.stderr.write(self.style.ERROR("JSON root must be a list"))
                return

            names_in_db = set(
                Ingredient.objects.filter(name__in=[item["name"] for item in items])
                .values_list("name", flat=True)
            )

            to_create = [
                Ingredient(**item)
                for item in items
                if item["name"] not in names_in_db
            ]

            with transaction.atomic():
                Ingredient.objects.bulk_create(to_create, ignore_conflicts=True)

            self.stdout.write(
                self.style.SUCCESS(f"Added new ingredients: {len(to_create)}")
            )

        except FileNotFoundError:
            self.stderr.write(self.style.ERROR(f"File not found: {file_path}"))
        except json.JSONDecodeError as exc:
            self.stderr.write(self.style.ERROR(f"Invalid JSON: {exc}"))
        except KeyError as exc:
            self.stderr.write(self.style.ERROR(f"Missing key in JSON items: {exc}"))
        except Exception as exc:
            self.stderr.write(self.style.ERROR(f"Unexpected error: {exc}"))
