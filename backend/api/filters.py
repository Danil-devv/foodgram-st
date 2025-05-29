import django_filters
from django_filters.rest_framework import CharFilter, FilterSet

from recipes.models import Ingredient, Recipe


class IngredientFilter(FilterSet):
    name = CharFilter(field_name="name", lookup_expr="istartswith")

    class Meta:
        model = Ingredient
        fields = ["name"]


class RecipeFilter(django_filters.FilterSet):
    is_in_shopping_cart = django_filters.NumberFilter(
        method="filter_is_in_shopping_cart"
    )
    is_favorited = django_filters.NumberFilter(method="filter_is_favorited")
    author = django_filters.NumberFilter(field_name="author__id")

    def filter_is_in_shopping_cart(self, recipes, name, value):
        user = getattr(self.request, "user", None)
        if value == 1 and user and user.is_authenticated:
            return recipes.filter(shopping_carts__user=user)
        return recipes

    def filter_is_favorited(self, recipes, name, value):
        user = getattr(self.request, "user", None)
        if value == 1 and user and user.is_authenticated:
            return recipes.filter(favorites__user=user)
        return recipes

    class Meta:
        model = Recipe
        fields = ("author", "is_favorited", "is_in_shopping_cart")
