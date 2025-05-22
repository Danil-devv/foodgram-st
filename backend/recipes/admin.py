from django.contrib import admin

from .models import Favorite, IngredientInRecipe, Recipe, ShoppingCart


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
