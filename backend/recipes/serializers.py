from django.core.validators import MinValueValidator

from .models import Ingredient
from users.serializers import UserSerializer
from .models import IngredientInRecipe, Recipe

import base64
import uuid

from django.core.files.base import ContentFile
from rest_framework import serializers


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith("data:image"):
            header, imgstr = data.split(";base64,", 1)
            ext = header.split("/")[-1]
            decoded = base64.b64decode(imgstr)
            data = ContentFile(decoded, name=f"{uuid.uuid4()}.{ext}")
        return super().to_internal_value(data)



class IngredientInRecipeReadSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source="ingredient.id")
    name = serializers.ReadOnlyField(source="ingredient.name")
    measurement_unit = serializers.ReadOnlyField(source="ingredient.measurement_unit")

    class Meta:
        model = IngredientInRecipe
        fields = ("id", "name", "measurement_unit", "amount")
        read_only_fields = fields


class IngredientInRecipeWriteSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all(), source="ingredient")
    amount = serializers.IntegerField(validators=[MinValueValidator(1)])

    class Meta:
        model = IngredientInRecipe
        fields = ("id", "amount")


class RecipeListSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    ingredients = IngredientInRecipeReadSerializer(source="ingredient_amounts", many=True, read_only=True)
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
        return user.is_authenticated and recipe.favorites.filter(user=user).exists()

    def get_is_in_shopping_cart(self, recipe):
        user = self.context["request"].user
        return user.is_authenticated and recipe.shopping_carts.filter(user=user).exists()


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
            raise serializers.ValidationError("Нужно указать хотя бы один ингредиент")
        ids = [item["ingredient"].id for item in ingredients_list]
        if len(ids) != len(set(ids)):
            raise serializers.ValidationError("Ингредиенты не должны повторяться")
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
            raise serializers.ValidationError({"ingredients": ["Это поле обязательно."]})
        ingredients_data = validated_data.pop("ingredients", None)
        recipe = super().update(instance, validated_data)
        if ingredients_data is not None:
            recipe.ingredient_amounts.all().delete()
            self._save_ingredients(recipe, ingredients_data)
        return recipe

    def to_representation(self, instance):
        return RecipeListSerializer(instance, context=self.context).data
