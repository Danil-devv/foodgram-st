import datetime
import io

from django.db.models import F, Sum
from django.http import FileResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from .filters import RecipeFilter
from .minified_serializer import RecipeMinifiedSerializer
from .models import Favorite, IngredientInRecipe, Recipe, ShoppingCart
from .permissions import IsAuthorOrReadOnly
from .serializers import RecipeCreateSerializer, RecipeListSerializer


def recipe_short_link_redirect(request, recipe_id):
    return redirect(f"/recipes/{recipe_id}/") \
        if (Recipe.objects.filter(id=recipe_id).exists())\
        else redirect("/")


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        return RecipeListSerializer if self.action in ["list", "retrieve"] else RecipeCreateSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @staticmethod
    def _toggle_entry(model, user, recipe, already_msg):
        entry, created = model.objects.get_or_create(user=user, recipe=recipe)
        if not created:
            raise serializers.ValidationError(already_msg)
        return entry

    @action(methods=["get"], detail=True, url_path="get-link")
    def get_link(self, request, pk=None):
        if not Recipe.objects.filter(pk=pk).exists():
            return Response(status=status.HTTP_404_NOT_FOUND)
        short_link = request.build_absolute_uri(reverse("recipes:recipe-short-link", args=[pk]))
        return Response({"short-link": short_link})

    @action(methods=["post", "delete"], detail=True, permission_classes=[IsAuthenticated], url_path="shopping_cart")
    def shopping_cart(self, request, pk=None):
        recipe = self.get_object()
        user = request.user

        if request.method == "POST":
            self._toggle_entry(ShoppingCart, user, recipe, "Рецепт уже в списке покупок")
            data = RecipeMinifiedSerializer(recipe, context={"request": request}).data
            return Response(data, status=status.HTTP_201_CREATED)

        get_object_or_404(ShoppingCart, user=user, recipe=recipe).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=["get"], detail=False, permission_classes=[IsAuthenticated], url_path="download_shopping_cart")
    def download_shopping_cart(self, request):
        user = request.user
        recipe_ids = user.shopping_carts.values_list("recipe_id", flat=True)
        ingredients = (
            IngredientInRecipe.objects.filter(recipe_id__in=recipe_ids)
            .values(name=F("ingredient__name"), measurement_unit=F("ingredient__measurement_unit"))
            .annotate(total=Sum("amount"))
            .order_by("name")
        )

        today = datetime.date.today().strftime("%d.%m.%Y")
        lines = [
            f"Список покупок — {today}",
            "",
            "Ингредиенты:",
            *[
                f"{idx}. {ing['name'].capitalize()} ({ing['measurement_unit']}) — {ing['total']}"
                for idx, ing in enumerate(ingredients, 1)
            ],
            "",
            "Рецепты:",
            *[
                f"{idx}. {rec.name} — {rec.author}"
                for idx, rec in enumerate(Recipe.objects.filter(id__in=recipe_ids), 1)
            ],
        ]

        buffer = io.BytesIO("\n".join(lines).encode("utf-8"))
        buffer.seek(0)
        return FileResponse(buffer, as_attachment=True, filename="shopping_cart.txt")

    @action(methods=["post", "delete"], detail=True, permission_classes=[IsAuthenticated], url_path="favorite")
    def favorite(self, request, pk=None):
        recipe = self.get_object()
        user = request.user

        if request.method == "POST":
            self._toggle_entry(Favorite, user, recipe, "Рецепт уже в избранном")
            data = RecipeMinifiedSerializer(recipe, context={"request": request}).data
            return Response(data, status=status.HTTP_201_CREATED)

        get_object_or_404(Favorite, user=user, recipe=recipe).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
