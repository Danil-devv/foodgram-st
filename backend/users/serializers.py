import base64
import re
import uuid
from io import BytesIO

from django.core.files.base import ContentFile
from PIL import Image
from rest_framework import serializers

from recipes.minified_serializer import RecipeMinifiedSerializer

from .models import Subscription, User


class UserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    class Meta:
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

    def get_is_subscribed(self, obj):
        return False

    def get_avatar(self, obj):
        request = self.context.get("request")
        if obj.avatar and hasattr(obj.avatar, "url"):
            avatar_url = obj.avatar.url
            if request is not None:
                return request.build_absolute_uri(avatar_url)
            return avatar_url
        return None


USERNAME_REGEX = r"^[\w.@+-]+\Z"


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "username",
            "first_name",
            "last_name",
            "password",
        )

    def validate_username(self, value):
        if not re.match(USERNAME_REGEX, value):
            raise serializers.ValidationError(
                "Поле `username` должно соответствовать "
                "регулярному выражению `^[\\w.@+-]+\\Z`"
            )
        return value

    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data["email"],
            username=validated_data["username"],
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"],
            password=validated_data["password"],
        )
        return user


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
        user = self.context["request"].user
        value = self.validated_data["avatar"]
        format, imgstr = value.split(";base64,")
        ext = format.split("/")[-1]
        decoded_file = base64.b64decode(imgstr)
        file_name = f"{uuid.uuid4()}.{ext}"
        user.avatar.save(file_name, ContentFile(decoded_file), save=True)
        return user


class SetPasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(required=True)
    current_password = serializers.CharField(required=True)

    def validate_current_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Текущий пароль неверен")
        return value

    def validate_new_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError(
                "Пароль должен содержать не менее 8 символов"
            )
        return value


class UserWithRecipesSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "username",
            "first_name",
            "last_name",
            "is_subscribed",
            "recipes",
            "recipes_count",
            "avatar",
        )

    def get_is_subscribed(self, obj):
        user = self.context.get("request").user
        if user.is_anonymous:
            return False
        return Subscription.objects.filter(user=user, author=obj).exists()

    def get_recipes(self, obj):
        request = self.context.get("request")
        recipes_limit = request.query_params.get("recipes_limit")
        qs = obj.recipes.all()
        if recipes_limit is not None and recipes_limit.isdigit():
            qs = qs[: int(recipes_limit)]
        return RecipeMinifiedSerializer(
            qs, many=True, context=self.context
        ).data

    def get_recipes_count(self, obj):
        return obj.recipes.count()

    def get_avatar(self, obj):
        request = self.context.get("request")
        if obj.avatar and hasattr(obj.avatar, "url"):
            avatar_url = obj.avatar.url
            if request is not None:
                return request.build_absolute_uri(avatar_url)
            return avatar_url
        return None
