import base64
import uuid
from io import BytesIO

from django.core.files.base import ContentFile
from django.core.validators import MinValueValidator
from djoser.serializers import (
    SetPasswordSerializer as DjoserSetPasswordSerializer,
)
from djoser.serializers import (
    UserCreateSerializer as DjoserUserCreateSerializer,
)
from djoser.serializers import UserSerializer as DjoserUserSerializer
from PIL import Image
from rest_framework import serializers

from recipes.models import Ingredient, IngredientInRecipe, Recipe
from users.models import Subscription, User

from .minified_serializer import RecipeMinifiedSerializer

SetPasswordSerializer = DjoserSetPasswordSerializer
UserCreateSerializer = DjoserUserCreateSerializer


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ("id", "name", "measurement_unit")


class UserSerializer(DjoserUserSerializer):
    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.ImageField(read_only=True)

    class Meta(DjoserUserSerializer.Meta):
        model = User
        fields = (
            "id",
            "email",
            "username",
            "first_name",
            "last_name",
            "is_subscribed",
            "avatar",
        )

    def get_is_subscribed(self, user: User) -> bool:
        request = self.context.get("request")
        if request is None or request.user.is_anonymous:
            return False
        return Subscription.objects.filter(
            user=request.user, author=user
        ).exists()


class AvatarSerializer(serializers.Serializer):
    avatar = serializers.CharField()

    def validate_avatar(self, value):
        if not value.startswith("data:image/"):
            raise serializers.ValidationError("Некорректный формат картинки")
        try:
            format, imgstr = value.split(";base64,")
            decoded_file = base64.b64decode(imgstr)

            image = Image.open(BytesIO(decoded_file))
            image.verify()
        except Exception:
            raise serializers.ValidationError(
                "Не удалось декодировать изображение"
            )
        return value

    def save(self, **kwargs):
        user: User = self.context["request"].user
        value: str = self.validated_data["avatar"]

        header, imgstr = value.split(";base64,", 1)
        extension = header.split("/")[-1]
        decoded = base64.b64decode(imgstr)

        filename = f"{uuid.uuid4()}.{extension}"
        user.avatar.save(filename, ContentFile(decoded), save=True)
        return user


class UserWithRecipesSerializer(UserSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(
        source="recipes.count", read_only=True
    )

    class Meta(UserSerializer.Meta):
        model = User
        fields = UserSerializer.Meta.fields + ("recipes", "recipes_count")

    def get_recipes(self, user):
        request = self.context.get("request")
        limit = request.query_params.get("recipes_limit")
        qs = user.recipes.all()
        if limit is not None and limit.isdigit():
            qs = qs[: int(limit)]
        return RecipeMinifiedSerializer(
            qs, many=True, context=self.context
        ).data


class IngredientInRecipeReadSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source="ingredient.id")
    name = serializers.ReadOnlyField(source="ingredient.name")
    measurement_unit = serializers.ReadOnlyField(
        source="ingredient.measurement_unit"
    )

    class Meta:
        model = IngredientInRecipe
        fields = ("id", "name", "measurement_unit", "amount")
        read_only_fields = fields


class IngredientInRecipeWriteSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(), source="ingredient"
    )
    amount = serializers.IntegerField(validators=[MinValueValidator(1)])

    class Meta:
        model = IngredientInRecipe
        fields = ("id", "amount")


class RecipeListSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    ingredients = IngredientInRecipeReadSerializer(
        source="ingredient_amounts", many=True, read_only=True
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = serializers.ImageField(read_only=True)

    class Meta:
        model = Recipe
        fields = (
            "id",
            "author",
            "ingredients",
            "is_favorited",
            "is_in_shopping_cart",
            "name",
            "image",
            "text",
            "cooking_time",
        )
        read_only_fields = fields

    def get_is_favorited(self, recipe):
        user = self.context["request"].user
        return (
            user.is_authenticated
            and recipe.favorites.filter(user=user).exists()
        )

    def get_is_in_shopping_cart(self, recipe):
        user = self.context["request"].user
        return (
            user.is_authenticated
            and recipe.shopping_carts.filter(user=user).exists()
        )


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith("data:image"):
            header, imgstr = data.split(";base64,", 1)
            ext = header.split("/")[-1]
            decoded = base64.b64decode(imgstr)
            data = ContentFile(decoded, name=f"{uuid.uuid4()}.{ext}")
        return super().to_internal_value(data)


class RecipeCreateSerializer(serializers.ModelSerializer):
    ingredients = IngredientInRecipeWriteSerializer(
        many=True, required=True, allow_empty=False
    )
    image = Base64ImageField()
    cooking_time = serializers.IntegerField(validators=[MinValueValidator(1)])

    class Meta:
        model = Recipe
        fields = ("id", "ingredients", "image", "name", "text", "cooking_time")

    def validate_ingredients(self, ingredients_list):
        if not ingredients_list:
            raise serializers.ValidationError(
                "Нужно указать хотя бы один ингредиент"
            )
        ids = [item["ingredient"].id for item in ingredients_list]
        if len(ids) != len(set(ids)):
            raise serializers.ValidationError(
                "Ингредиенты не должны повторяться"
            )
        return ingredients_list

    def _save_ingredients(self, recipe, ingredients_data):
        IngredientInRecipe.objects.bulk_create(
            [
                IngredientInRecipe(
                    recipe=recipe,
                    ingredient=item["ingredient"],
                    amount=item["amount"],
                )
                for item in ingredients_data
            ]
        )

    def create(self, validated_data):
        ingredients_data = validated_data.pop("ingredients")
        recipe = super().create(validated_data)
        self._save_ingredients(recipe, ingredients_data)
        return recipe

    def update(self, instance, validated_data):
        # при PATCH запросе DRF не требует обязательных полей
        # поэтому проверяем здесь
        if "ingredients" not in self.initial_data:
            raise serializers.ValidationError(
                {"ingredients": ["Это поле обязательно."]}
            )
        ingredients_data = validated_data.pop("ingredients", None)
        recipe = super().update(instance, validated_data)
        if ingredients_data is not None:
            recipe.ingredient_amounts.all().delete()
            self._save_ingredients(recipe, ingredients_data)
        return recipe

    def to_representation(self, instance):
        return RecipeListSerializer(instance, context=self.context).data
