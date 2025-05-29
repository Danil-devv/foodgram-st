import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

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
            file_path = Path(
                options.get("file")
                or Path(settings.BASE_DIR).resolve().parent
                / "data"
                / "ingredients.json"
            ).resolve()

            with file_path.open(encoding="utf-8") as fh:
                created = Ingredient.objects.bulk_create(
                    [Ingredient(**item) for item in json.load(fh)],
                    ignore_conflicts=True,
                )
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Added new ingredients: {len(created)}."
                    )
                )
        except Exception as exc:
            self.stderr.write(
                self.style.ERROR(
                    f"Unexpected error in file {file_path}: {exc}"
                )
            )
