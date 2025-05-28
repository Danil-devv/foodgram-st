from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.db.models import Count
from django.utils.safestring import mark_safe

from .models import Subscription, User


class HasRecipesFilter(admin.SimpleListFilter):
    title = "Есть рецепты"
    parameter_name = "has_recipes"

    def lookups(self, request, model_admin):
        return ("yes", "да"), ("no", "нет")

    def queryset(self, request, queryset):
        if self.value() == "yes":
            return queryset.filter(recipe_count__gt=0)
        if self.value() == "no":
            return queryset.filter(recipe_count=0)
        return queryset


class HasSubscriptionsFilter(admin.SimpleListFilter):
    title = "Есть подписки"
    parameter_name = "has_subs"

    def lookups(self, request, model_admin):
        return ("yes", "да"), ("no", "нет")

    def queryset(self, request, queryset):
        if self.value() == "yes":
            return queryset.filter(subscription_count__gt=0)
        if self.value() == "no":
            return queryset.filter(subscription_count=0)
        return queryset


class HasSubscribersFilter(admin.SimpleListFilter):
    title = "Есть подписчики"
    parameter_name = "has_followers"

    def lookups(self, request, model_admin):
        return ("yes", "да"), ("no", "нет")

    def queryset(self, request, queryset):
        if self.value() == "yes":
            return queryset.filter(follower_count__gt=0)
        if self.value() == "no":
            return queryset.filter(follower_count=0)
        return queryset


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = (
        "id",
        "username",
        "full_name",
        "email",
        "avatar_thumb",
        "recipe_count",
        "subscription_count",
        "follower_count",
        "is_staff",
    )
    list_display_links = ("username",)

    search_fields = ("username", "first_name", "last_name", "email")

    list_filter = (
        "is_staff",
        HasRecipesFilter,
        HasSubscriptionsFilter,
        HasSubscribersFilter,
    )

    readonly_fields = (
        "avatar_thumb",
        "recipe_count",
        "subscription_count",
        "follower_count",
    )

    def get_queryset(self, request):
        qs = (
            super()
            .get_queryset(request)
            .annotate(
                recipe_count=Count("recipes", distinct=True),
                subscription_count=Count(
                    "subscriptions_from_me", distinct=True
                ),
                follower_count=Count("subscriptions_to_me", distinct=True),
            )
        )
        return qs

    @admin.display(description="ФИО", ordering="first_name")
    def full_name(self, user):
        return f"{user.first_name} {user.last_name}".strip()

    @admin.display(description="Рецептов", ordering="recipe_count")
    def recipe_count(self, user):
        return user.recipe_count

    @admin.display(description="Подписок", ordering="subscription_count")
    def subscription_count(self, user):
        return user.subscription_count

    @admin.display(description="Подписчиков", ordering="follower_count")
    def follower_count(self, user):
        return user.follower_count

    @admin.display(description="Аватар", boolean=False)
    def avatar_thumb(self, user):
        if user.avatar:
            return mark_safe(
                f'<img src="{user.avatar.url}" '
                f'style="height:64px;width:64px;object-fit:cover;border-radius:4px;" />'
            )
        return "—"


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "author", "created_at")
    search_fields = ("user__username", "author__username")
    list_filter = ("created_at",)
