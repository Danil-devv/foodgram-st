from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models


username_validator = RegexValidator(
    regex=r"^[\w.@+-]+\Z",
    message="Введите корректный никнейм: буквы, цифры, символы «@ . + - _»",
)


class User(AbstractUser):
    email = models.EmailField("Email", unique=True, max_length=254)
    username = models.CharField(
        "Никнейм",
        max_length=150,
        unique=True,
        validators=[username_validator],
        help_text="150 символов или меньше. Буквы, цифры и @/./+/-/_.",
    )
    first_name = models.CharField("Имя", max_length=150)
    last_name = models.CharField("Фамилия", max_length=150)
    avatar = models.ImageField("Аватар", upload_to="users/", blank=True, null=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "first_name", "last_name"]

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        ordering = ("username",)

    def __str__(self) -> str:
        return self.email


class Subscription(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="subscriptions_from_me",
        verbose_name="Подписчик",
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="subscriptions_to_me",
        verbose_name="Автор",
    )
    created_at = models.DateTimeField("Дата подписки", auto_now_add=True)

    class Meta:
        verbose_name = "Подписка"
        verbose_name_plural = "Подписки"
        ordering = ("-created_at",)
        constraints = [
            models.UniqueConstraint(
                fields=("user", "author"),
                name="unique_user_author_subscription",
            )
        ]
