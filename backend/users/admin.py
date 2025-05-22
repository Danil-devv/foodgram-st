from django.contrib import admin

from .models import Subscription, User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    search_fields = ["first_name", "last_name", "email"]
    list_display = (
        "id",
        "email",
        "username",
        "first_name",
        "last_name",
        "is_staff",
    )


admin.site.register(Subscription)
