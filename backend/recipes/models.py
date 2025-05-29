from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class Ingredient(models.Model):
    name = models.CharField("Название", max_length=128)
    measurement_unit = models.CharField("Единица измерения", max_length=64)

    class Meta:
        ordering = ("name",)
        verbose_name = "Ингредиент"
        verbose_name_plural = "Ингредиенты"
        constraints = [
            models.UniqueConstraint(
                fields=["name", "measurement_unit"],
                name="unique_ingredient_measurement_unit"
            )
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.measurement_unit})"


class Recipe(models.Model):
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    name = models.CharField("Название", max_length=256)
    image = models.ImageField("Изображение", upload_to="recipes/images/")
    text = models.TextField("Описание")
    cooking_time = models.PositiveIntegerField(
        "Время приготовления", validators=[MinValueValidator(1)]
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through="IngredientInRecipe",
        verbose_name="Ингредиенты"
    )
    created = models.DateTimeField("Дата создания", auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ("-created",)
        verbose_name = "Рецепт"
        verbose_name_plural = "Рецепты"
        default_related_name = "recipes"


class IngredientInRecipe(models.Model):
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, related_name="ingredient_amounts"
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name="recipe_ingredients"
    )
    amount = models.PositiveIntegerField(validators=[MinValueValidator(1)])

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("recipe", "ingredient"),
                name="unique_recipe_ingredient",
            )
        ]


class UserRecipeBase(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
    )

    def __str__(self):
        return f"{self.user} – {self.recipe}"

    class Meta:
        abstract = True
        constraints = [
            models.UniqueConstraint(
                fields=("user", "recipe"), name="unique_%(class)s"
            )
        ]


class ShoppingCart(UserRecipeBase):
    class Meta(UserRecipeBase.Meta):
        verbose_name = "Корзина"
        verbose_name_plural = "Корзина"
        default_related_name = "shopping_carts"


class Favorite(UserRecipeBase):
    class Meta(UserRecipeBase.Meta):
        verbose_name = "Избранное"
        verbose_name_plural = "Избранные"
        default_related_name = "favorites"
