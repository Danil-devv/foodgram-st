import json
import os

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files import File
from django.core.management.base import BaseCommand

from ingredients.models import Ingredient
from recipes.models import Favorite, IngredientInRecipe, Recipe, ShoppingCart

User = get_user_model()


class Command(BaseCommand):
    help = "Import recipes, shopping_cart and favorite from JSON file"

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            type=str,
            default=os.path.join(
                settings.BASE_DIR, "..", "data", "recipes_full.json"
            ),
            help="Path to recipes.json file",
        )
        parser.add_argument(
            "--media-dir",
            type=str,
            default=os.path.join(settings.BASE_DIR, "..", "data"),
            help="Base media directory",
        )

    def handle(self, *args, **options):
        file_path = os.path.abspath(options["file"])
        media_dir = os.path.abspath(options["media_dir"])

        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f"File not found: {file_path}"))
            return

        with open(file_path, "r", encoding="utf-8") as f:
            recipes_data = json.load(f)

        created, skipped = 0, 0
        for recipe_data in recipes_data:
            author_email = recipe_data.get("author_email")
            author = User.objects.filter(email=author_email).first()
            if not author:
                self.stdout.write(
                    self.style.WARNING(
                        f"Author {author_email} not found, skipping"
                    )
                )
                skipped += 1
                continue

            name = recipe_data["name"]
            text = recipe_data["text"]
            cooking_time = recipe_data["cooking_time"]

            if Recipe.objects.filter(author=author, name=name).exists():
                self.stdout.write(
                    self.style.WARNING(
                        f"Recipe '{name}' from"
                        f" {author_email} already exists, skipping"
                    )
                )
                skipped += 1
                continue

            recipe = Recipe(
                author=author, name=name, text=text, cooking_time=cooking_time
            )
            recipe.save()

            image_path = recipe_data.get("image")
            if image_path:
                image_full_path = os.path.join(media_dir, image_path)
                if os.path.exists(image_full_path):
                    with open(image_full_path, "rb") as img_file:
                        recipe.image.save(
                            os.path.basename(image_full_path),
                            File(img_file),
                            save=True,
                        )
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            f"Image not found: {image_full_path}"
                        )
                    )

            ingredients_data = recipe_data.get("ingredients", [])
            for ing in ingredients_data:
                ingredient_id = ing["id"]
                amount = ing["amount"]
                ingredient = Ingredient.objects.filter(
                    id=ingredient_id
                ).first()
                if not ingredient:
                    self.stdout.write(
                        self.style.WARNING(
                            f"Ingredient with id={ingredient_id}"
                            f" not found, skipping"
                        )
                    )
                    continue
                IngredientInRecipe.objects.create(
                    recipe=recipe, ingredient=ingredient, amount=amount
                )

            cart_emails = recipe_data.get("shopping_cart", [])
            for cart_email in cart_emails:
                user = User.objects.filter(email=cart_email).first()
                if user:
                    ShoppingCart.objects.get_or_create(
                        user=user, recipe=recipe
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            f"User for cart with"
                            f" cart_email {cart_email} not found"
                        )
                    )

            fav_emails = recipe_data.get("favorited_by", [])
            for fav_email in fav_emails:
                user = User.objects.filter(email=fav_email).first()
                if user:
                    Favorite.objects.get_or_create(user=user, recipe=recipe)
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            f"User for favorite {fav_email} not found"
                        )
                    )

            created += 1
            self.stdout.write(
                self.style.SUCCESS(f"Recipe '{name}' successfully created")
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Import done! Created: {created}, skipped: {skipped}"
            )
        )
