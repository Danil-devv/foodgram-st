from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import SubscriptionListView, UserViewSet

router = DefaultRouter()
router.register("users", UserViewSet, basename="users")

urlpatterns = [
    path(
        "users/subscriptions/",
        SubscriptionListView.as_view(),
        name="subscriptions",
    ),
    path("", include(router.urls)),
]
