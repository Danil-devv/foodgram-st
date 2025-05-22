from django.db.models import F, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
)
from rest_framework.response import Response

from .filters import RecipeFilter
from .minified_serializer import RecipeMinifiedSerializer
from .models import Favorite, IngredientInRecipe, Recipe, ShoppingCart
from .permissions import IsAuthorOrReadOnly
from .serializers import RecipeCreateSerializer, RecipeListSerializer


def recipe_short_link_redirect(request, short_id):
    try:
        recipe_id = int(short_id, 16)
    except ValueError:
        return redirect("/")

    recipe = get_object_or_404(Recipe, id=recipe_id)
    return redirect(f"/recipes/{recipe.id}/")


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return RecipeListSerializer
        return RecipeCreateSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(methods=["get"], detail=True, url_path="get-link")
    def get_link(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)

        short_id = format(recipe.id, "x")
        short_link = request.build_absolute_uri(
            reverse("recipes:recipe-short-link", args=[short_id])
        )

        return Response({"short-link": short_link}, status=status.HTTP_200_OK)

    @action(
        methods=["post", "delete"],
        detail=True,
        permission_classes=[IsAuthenticated],
        url_path="shopping_cart",
    )
    def shopping_cart(self, request, pk=None):
        recipe = self.get_object()
        user = request.user

        if request.method == "POST":
            if ShoppingCart.objects.filter(user=user, recipe=recipe).exists():
                return Response(
                    {"errors": "Рецепт уже в списке покупок"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            ShoppingCart.objects.create(user=user, recipe=recipe)
            serializer = RecipeMinifiedSerializer(
                recipe, context={"request": request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == "DELETE":
            obj = ShoppingCart.objects.filter(user=user, recipe=recipe).first()
            if obj is None:
                return Response(
                    {"errors": "Этого рецепта нет в списке покупок"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            obj.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=["get"],
        detail=False,
        permission_classes=[IsAuthenticated],
        url_path="download_shopping_cart",
    )
    def download_shopping_cart(self, request):
        user = request.user
        recipe_ids = user.shopping_cart.values_list("recipe_id", flat=True)
        ingredients = (
            IngredientInRecipe.objects.filter(recipe_id__in=recipe_ids)
            .values(
                name=F("ingredient__name"),
                measurement_unit=F("ingredient__measurement_unit"),
            )
            .annotate(total=Sum("amount"))
            .order_by("name")
        )

        lines = []
        for ing in ingredients:
            lines.append(
                f"{ing['name']} ({ing['measurement_unit']}) — {ing['total']}"
            )

        content = "\n".join(lines)
        response = HttpResponse(content, content_type="text/plain")
        response["Content-Disposition"] = (
            "attachment; filename=shopping_cart.txt"
        )
        return response

    @action(
        methods=["post", "delete"],
        detail=True,
        permission_classes=[IsAuthenticated],
        url_path="favorite",
    )
    def favorite(self, request, pk=None):
        recipe = self.get_object()
        user = request.user

        if request.method == "POST":
            if Favorite.objects.filter(user=user, recipe=recipe).exists():
                return Response(
                    {"errors": "Рецепт уже в избранном"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            Favorite.objects.create(user=user, recipe=recipe)
            serializer = RecipeMinifiedSerializer(
                recipe, context={"request": request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == "DELETE":
            obj = Favorite.objects.filter(user=user, recipe=recipe).first()
            if obj is None:
                return Response(
                    {"errors": "Этого рецепта нет в избранном"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            obj.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
