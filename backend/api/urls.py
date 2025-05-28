from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api.views import IngredientViewSet

router = DefaultRouter()
router.register("ingredients", IngredientViewSet, basename="ingredients")

urlpatterns = [
    path("", include("users.urls")),
    path("", include(router.urls)),
    path("", include(("recipes.urls", "recipes"), namespace="recipes")),
    path("auth/", include("djoser.urls.authtoken")),
]
