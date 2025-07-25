from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api.views import IngredientViewSet

from .views import RecipeViewSet, SubscriptionListView, UserViewSet

router = DefaultRouter()
router.register("users", UserViewSet, basename="users")
router.register("ingredients", IngredientViewSet, basename="ingredients")
router.register("recipes", RecipeViewSet, basename="recipes")

urlpatterns = [
    path(
        "users/subscriptions/",
        SubscriptionListView.as_view(),
        name="subscriptions",
    ),
    path("", include(router.urls)),
    path("auth/", include("djoser.urls.authtoken")),
]
