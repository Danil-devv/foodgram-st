from rest_framework import serializers

from recipes.models import Ingredient
from users.serializers import UserSerializer

from .models import IngredientInRecipe, Recipe


class IngredientInRecipeReadSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source="ingredient.id")
    name = serializers.ReadOnlyField(source="ingredient.name")
    measurement_unit = serializers.ReadOnlyField(
        source="ingredient.measurement_unit"
    )

    class Meta:
        model = IngredientInRecipe
        fields = ("id", "name", "measurement_unit", "amount")


class RecipeListSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    ingredients = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()

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

    def get_ingredients(self, obj):
        qs = obj.ingredient_amounts.select_related("ingredient")
        return IngredientInRecipeReadSerializer(qs, many=True).data

    def get_is_favorited(self, obj):
        user = self.context.get("request").user
        if user.is_anonymous:
            return False
        return obj.in_favorites.filter(user=user).exists()

    def get_is_in_shopping_cart(self, obj):
        user = self.context.get("request").user
        if user.is_anonymous:
            return False
        return obj.in_shopping_carts.filter(user=user).exists()

    def get_image(self, obj):
        request = self.context.get("request")
        if obj.image and hasattr(obj.image, "url"):
            url = obj.image.url
            if request:
                return request.build_absolute_uri(url)
            return url
        return None


class IngredientInRecipeWriteSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(), source="ingredient"
    )
    amount = serializers.IntegerField()

    class Meta:
        model = IngredientInRecipe
        fields = ("id", "amount")


class RecipeCreateSerializer(serializers.ModelSerializer):
    ingredients = IngredientInRecipeWriteSerializer(many=True)
    image = serializers.CharField()

    class Meta:
        model = Recipe
        fields = ("id", "ingredients", "image", "name", "text", "cooking_time")

    def validate(self, data):
        return data

    def validate_ingredients(self, value):
        if not value or len(value) == 0:
            raise serializers.ValidationError(
                "Нужно указать хотя бы один ингредиент"
            )
        ids = [item["ingredient"].id for item in value]
        if len(ids) != len(set(ids)):
            raise serializers.ValidationError(
                "Ингредиенты не должны повторяться"
            )
        for item in value:
            if item["amount"] < 1:
                raise serializers.ValidationError(
                    "Количество ингредиента должно быть не меньше 1"
                )
        return value

    def validate_cooking_time(self, value):
        if value < 1:
            raise serializers.ValidationError(
                "Время приготовления должно быть не меньше 1 минуты"
            )
        return value

    def create(self, validated_data):
        ingredients_data = validated_data.pop("ingredients")
        image_data = validated_data.pop("image")
        recipe = Recipe.objects.create(**validated_data)

        import base64
        import uuid

        from django.core.files.base import ContentFile

        if image_data.startswith("data:image"):
            format, imgstr = image_data.split(";base64,")
            ext = format.split("/")[-1]
            decoded_file = base64.b64decode(imgstr)
            file_name = f"{uuid.uuid4()}.{ext}"
            recipe.image.save(file_name, ContentFile(decoded_file), save=True)

        for ing in ingredients_data:
            IngredientInRecipe.objects.create(
                recipe=recipe,
                ingredient=ing["ingredient"],
                amount=ing["amount"],
            )
        return recipe

    def update(self, instance, validated_data):
        if "ingredients" not in self.initial_data:
            raise serializers.ValidationError(
                {"ingredients": ["Это поле обязательно."]}
            )

        ingredients_data = validated_data.pop("ingredients", None)
        image_data = validated_data.pop("image", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if image_data:
            import base64
            import uuid

            from django.core.files.base import ContentFile

            if image_data.startswith("data:image"):
                format, imgstr = image_data.split(";base64,")
                ext = format.split("/")[-1]
                decoded_file = base64.b64decode(imgstr)
                file_name = f"{uuid.uuid4()}.{ext}"
                instance.image.save(
                    file_name, ContentFile(decoded_file), save=True
                )

        instance.save()

        if ingredients_data is not None:
            instance.ingredient_amounts.all().delete()
            for ing in ingredients_data:
                IngredientInRecipe.objects.create(
                    recipe=instance,
                    ingredient=ing["ingredient"],
                    amount=ing["amount"],
                )

        return instance

    def to_representation(self, instance):
        return RecipeListSerializer(instance, context=self.context).data
