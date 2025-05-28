from django.shortcuts import get_object_or_404

from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import generics, pagination, permissions, serializers, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import Subscription, User
from .serializers import AvatarSerializer, UserWithRecipesSerializer


class UserViewSet(DjoserUserViewSet):
    queryset = User.objects.all()

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated],
        url_path='me',
        url_name='me'
    )
    def me(self, request, *args, **kwargs):
        return super().me(request, *args, **kwargs)

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [AllowAny()]
        return super().get_permissions()

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
            avatar_url = request.build_absolute_uri(user.avatar.url) if user.avatar else None
            return Response({"avatar": avatar_url})
        user.avatar.delete(save=True)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=["post", "delete"],
        detail=True,
        permission_classes=[IsAuthenticated],
        url_path="subscribe",
    )
    def subscribe(self, request, id=None):
        user = request.user
        author = get_object_or_404(User, id=id)
        if request.method == "POST":
            if user == author:
                raise serializers.ValidationError("Нельзя подписаться на самого себя")
            subscription, created = Subscription.objects.get_or_create(
                user=user,
                author=author,
            )
            if not created:
                raise serializers.ValidationError("Вы уже подписаны на данного автора")
            data = UserWithRecipesSerializer(author, context={"request": request}).data
            return Response(data, status=status.HTTP_201_CREATED)
        get_object_or_404(Subscription, user=user, author=author).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class SubscriptionPagination(pagination.PageNumberPagination):
    page_size = 6
    page_size_query_param = "limit"


class SubscriptionListView(generics.ListAPIView):
    serializer_class = UserWithRecipesSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = SubscriptionPagination

    def get_queryset(self):
        return User.objects.filter(
            subscriptions_to_me__user=self.request.user
        ).distinct()
