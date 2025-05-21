from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, SubscriptionListView

router = DefaultRouter()
router.register("users", UserViewSet, basename="users")

urlpatterns = [
    path("users/subscriptions/", SubscriptionListView.as_view(), name="subscriptions"),
    path("", include(router.urls)),
]
