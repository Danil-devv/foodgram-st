import base64
import uuid
from io import BytesIO

from django.conf import settings
from django.core.files.base import ContentFile
from PIL import Image
from rest_framework import serializers

from djoser.serializers import (
    UserSerializer as DjoserUserSerializer,
    UserCreateSerializer as DjoserUserCreateSerializer,
    SetPasswordSerializer as DjoserSetPasswordSerializer,
)

from recipes.minified_serializer import RecipeMinifiedSerializer
from .models import Subscription, User


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
        return Subscription.objects.filter(user=request.user, author=user).exists()


SetPasswordSerializer = DjoserSetPasswordSerializer
UserCreateSerializer = DjoserUserCreateSerializer

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
    recipes_count = serializers.IntegerField(source="recipes.count", read_only=True)

    class Meta(UserSerializer.Meta):
        model = User
        fields = UserSerializer.Meta.fields + ("recipes", "recipes_count")

    def get_recipes(self, user):
        request = self.context.get("request")
        limit = request.query_params.get("recipes_limit")
        qs = user.recipes.all()
        if limit is not None and limit.isdigit():
            qs = qs[: int(limit)]
        return RecipeMinifiedSerializer(qs, many=True, context=self.context).data
