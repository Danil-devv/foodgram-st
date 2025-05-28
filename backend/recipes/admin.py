from .models import Favorite, IngredientInRecipe, Recipe, ShoppingCart

from django.contrib import admin
from django.db.models import Count

from .models import Ingredient


class InRecipesFilter(admin.SimpleListFilter):
    title = "Есть в рецептах"
    parameter_name = "has_recipe"

    def lookups(self, request, model_admin):
        return ("yes", "да"), ("no", "нет")

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

    def recipe_count(self, ingredient):
        return ingredient.recipe_count

    recipe_count.short_description = "Находится в рецептах"
    recipe_count.admin_order_field = "recipe_count"


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    search_fields = [
        "name",
        "author__email",
        "author__username",
        "author__first_name",
        "author__last_name",
    ]
    list_display = ("id", "name", "author", "favorites_count")

    def favorites_count(self, obj):
        return obj.in_favorites.count()

    favorites_count.short_description = "In Favorites"


admin.site.register(IngredientInRecipe)
admin.site.register(ShoppingCart)
admin.site.register(Favorite)
