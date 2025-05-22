from django.shortcuts import get_object_or_404
from rest_framework import (
    generics,
    mixins,
    pagination,
    permissions,
    status,
    viewsets,
)
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Subscription, User
from .serializers import (
    AvatarSerializer,
    SetPasswordSerializer,
    UserCreateSerializer,
    UserSerializer,
    UserWithRecipesSerializer,
)


class UserViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_serializer_class(self):
        if self.action == "create":
            return UserCreateSerializer
        return UserSerializer

    @action(
        methods=["get"],
        detail=False,
        permission_classes=[IsAuthenticated],
        url_path="me",
    )
    def me(self, request):
        serializer = self.get_serializer(
            request.user, context={"request": request}
        )
        return Response(serializer.data)

    @action(
        methods=["put", "delete"],
        detail=False,
        permission_classes=[IsAuthenticated],
        url_path="me/avatar",
    )
    def avatar(self, request):
        user = request.user
        if request.method == "PUT":
            serializer = AvatarSerializer(
                data=request.data, context={"request": request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            avatar_url = user.avatar.url if user.avatar else None
            if avatar_url:
                avatar_url = request.build_absolute_uri(avatar_url)
            return Response({"avatar": avatar_url})
        if request.method == "DELETE":
            user.avatar.delete(save=True)
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=["post"],
        detail=False,
        permission_classes=[IsAuthenticated],
        url_path="set_password",
    )
    def set_password(self, request):
        serializer = SetPasswordSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        user = request.user
        user.set_password(serializer.validated_data["new_password"])
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=["post", "delete"],
        detail=True,
        permission_classes=[IsAuthenticated],
        url_path="subscribe",
    )
    def subscribe(self, request, pk=None):
        user = request.user
        author = get_object_or_404(User, pk=pk)
        if request.method == "POST":
            if user == author:
                return Response(
                    {"errors": "Нельзя подписаться на самого себя"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if Subscription.objects.filter(user=user, author=author).exists():
                return Response(
                    {"errors": "Вы уже подписаны на этого пользователя"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            Subscription.objects.create(user=user, author=author)
            serializer = UserWithRecipesSerializer(
                author, context={"request": request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == "DELETE":
            sub = Subscription.objects.filter(user=user, author=author).first()
            if sub is None:
                return Response(
                    {"errors": "Вы не подписаны на этого пользователя"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            sub.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)


class SubscriptionPagination(pagination.PageNumberPagination):
    page_size_query_param = "limit"


class SubscriptionListView(generics.ListAPIView):
    serializer_class = UserWithRecipesSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = SubscriptionPagination

    def get_queryset(self):
        user = self.request.user
        return User.objects.filter(subscribers__user=user).distinct()
