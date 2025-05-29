import datetime
import io

from django.db.models import F, Sum
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import (
    generics,
    pagination,
    permissions,
    serializers,
    status,
    viewsets,
)
from rest_framework.decorators import action
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
)
from rest_framework.response import Response

from recipes.models import (
    Favorite,
    Ingredient,
    IngredientInRecipe,
    Recipe,
    ShoppingCart,
)
from users.models import Subscription, User

from .filters import IngredientFilter, RecipeFilter
from .minified_serializer import RecipeMinifiedSerializer
from .permissions import IsAuthorOrReadOnly
from .serializers import (
    AvatarSerializer,
    IngredientSerializer,
    RecipeCreateSerializer,
    RecipeListSerializer,
    UserWithRecipesSerializer,
)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = IngredientFilter
    pagination_class = None


class UserViewSet(DjoserUserViewSet):
    queryset = User.objects.all()

    @action(
        detail=False,
        methods=["get"],
        permission_classes=[IsAuthenticated],
        url_path="me",
        url_name="me",
    )
    def me(self, request, *args, **kwargs):
        return super().me(request, *args, **kwargs)

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [AllowAny()]
        return super().get_permissions()

    @action(
        methods=["put", "delete"],
        detail=False,
        permission_classes=[IsAuthenticated],
        url_path="me/avatar",
    )
    def avatar(self, request):
        user = request.user
        if request.method == "PUT":
            serializer = AvatarSerializer(
                data=request.data, context={"request": request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            avatar_url = (
                request.build_absolute_uri(user.avatar.url)
                if user.avatar
                else None
            )
            return Response({"avatar": avatar_url})
        user.avatar.delete(save=True)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=["post", "delete"],
        detail=True,
        permission_classes=[IsAuthenticated],
        url_path="subscribe",
    )
    def subscribe(self, request, id=None):
        user = request.user
        author = get_object_or_404(User, id=id)
        if request.method == "POST":
            if user == author:
                raise serializers.ValidationError(
                    "Нельзя подписаться на самого себя"
                )
            subscription, created = Subscription.objects.get_or_create(
                user=user,
                author=author,
            )
            if not created:
                raise serializers.ValidationError(
                    "Вы уже подписаны на данного автора"
                )
            data = UserWithRecipesSerializer(
                author, context={"request": request}
            ).data
            return Response(data, status=status.HTTP_201_CREATED)
        get_object_or_404(Subscription, user=user, author=author).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class SubscriptionPagination(pagination.PageNumberPagination):
    page_size = 6
    page_size_query_param = "limit"


class SubscriptionListView(generics.ListAPIView):
    serializer_class = UserWithRecipesSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = SubscriptionPagination

    def get_queryset(self):
        return User.objects.filter(
            subscriptions_to_me__user=self.request.user
        ).distinct()


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        return (
            RecipeListSerializer
            if self.action in ["list", "retrieve"]
            else RecipeCreateSerializer
        )

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
        short_link = request.build_absolute_uri(
            reverse("recipes:recipe-short-link-redirect", args=[pk])
        )
        return Response({"short-link": short_link})

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
            self._toggle_entry(
                ShoppingCart, user, recipe, "Рецепт уже в списке покупок"
            )
            data = RecipeMinifiedSerializer(
                recipe, context={"request": request}
            ).data
            return Response(data, status=status.HTTP_201_CREATED)

        get_object_or_404(ShoppingCart, user=user, recipe=recipe).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=["get"],
        detail=False,
        permission_classes=[IsAuthenticated],
        url_path="download_shopping_cart",
    )
    def download_shopping_cart(self, request):
        user = request.user
        recipe_ids = user.shopping_carts.values_list("recipe_id", flat=True)
        ingredients = (
            IngredientInRecipe.objects.filter(recipe_id__in=recipe_ids)
            .values(
                name=F("ingredient__name"),
                measurement_unit=F("ingredient__measurement_unit"),
            )
            .annotate(total=Sum("amount"))
            .order_by("name")
        )

        today = datetime.date.today().strftime("%d.%m.%Y")
        lines = [
            f"Список покупок — {today}",
            "",
            "Ингредиенты:",
            *[
                f"{idx}. {ing['name'].capitalize()} "
                f"({ing['measurement_unit']}) — {ing['total']}"
                for idx, ing in enumerate(ingredients, 1)
            ],
            "",
            "Рецепты:",
            *[
                f"{idx}. {rec.name} — {rec.author}"
                for idx, rec in enumerate(
                    Recipe.objects.filter(id__in=recipe_ids), 1
                )
            ],
        ]

        buffer = io.BytesIO("\n".join(lines).encode("utf-8"))
        buffer.seek(0)
        return FileResponse(
            buffer, as_attachment=True, filename="shopping_cart.txt"
        )

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
            self._toggle_entry(
                Favorite, user, recipe, "Рецепт уже в избранном"
            )
            data = RecipeMinifiedSerializer(
                recipe, context={"request": request}
            ).data
            return Response(data, status=status.HTTP_201_CREATED)

        get_object_or_404(Favorite, user=user, recipe=recipe).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
