from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import RecipeViewSet, recipe_short_link_redirect

router = DefaultRouter()
router.register("recipes", RecipeViewSet, basename="recipes")

urlpatterns = [
    path("", include(router.urls)),
    path(
        "s/<str:short_id>/",
        recipe_short_link_redirect,
        name="recipe-short-link",
    ),
]
