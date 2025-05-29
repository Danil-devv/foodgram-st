from django.contrib import admin
from django.db.models import Count
from django.utils.safestring import mark_safe

from .models import (
    Favorite,
    Ingredient,
    IngredientInRecipe,
    Recipe,
    ShoppingCart,
)


class InRecipesFilter(admin.SimpleListFilter):
    LOOKUPS = (("yes", "да"), ("no", "нет"))
    title = "Есть в рецептах"
    parameter_name = "has_recipe"

    def lookups(self, request, model_admin):
        return self.LOOKUPS

    def queryset(self, request, queryset):
        if self.value() == "yes":
            return queryset.filter(recipe_count__gt=0)
        if self.value() == "no":
            return queryset.filter(recipe_count=0)
        return queryset


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    search_fields = ("name", "measurement_unit")
    list_display = ("id", "name", "measurement_unit", "recipe_count")
    readonly_fields = ("recipe_count",)
    list_filter = ("measurement_unit", InRecipesFilter)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(recipe_count=Count("recipes"))

    @admin.display(description="В рецептах", ordering="recipe_count")
    def recipe_count(self, ingredient):
        return ingredient.recipe_count


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    search_fields = [
        "name",
        "author__email",
        "author__username",
        "author__first_name",
        "author__last_name",
    ]
    list_display = (
        "id",
        "name",
        "cooking_time",
        "author",
        "favorites_count",
        "ingredients_html",
        "image_tag",
    )
    readonly_fields = ("image_tag",)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(fav_cnt=Count("favorites"))

    @admin.display(description="В избранном", ordering="fav_cnt")
    def favorites_count(self, recipe):
        return recipe.fav_cnt

    @admin.display(description="Ингредиенты")
    @mark_safe
    def ingredients_html(self, recipe):
        items = [
            (f"{ia.ingredient.name} — {ia.amount}"
             f" {ia.ingredient.measurement_unit}")
            for ia in recipe.ingredient_amounts.select_related("ingredient")
        ]
        return "<br>".join(items)

    @admin.display(description="Картинка")
    @mark_safe
    def image_tag(self, recipe):
        if recipe.image:
            return (
                f'<img src="{recipe.image.url}" '
                f'style="height:80px;object-fit:cover;border-radius:4px;" />'
            )
        return "—"


admin.site.register(IngredientInRecipe)
admin.site.register(ShoppingCart)
admin.site.register(Favorite)
