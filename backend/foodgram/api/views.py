from django.http import FileResponse
from http import HTTPStatus
from django.contrib.auth import get_user_model
from django_filters.rest_framework import (
    DjangoFilterBackend,
    FilterSet,
    BooleanFilter,
    NumberFilter
)
from djoser.views import UserViewSet
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.permissions import (
    IsAuthenticatedOrReadOnly,
    IsAuthenticated,
    AllowAny
)
from django.shortcuts import get_object_or_404
from .serializers import (
    RecipeShortSerializer,
    UserSerializer,
    IngredientSerializer,
    RecipeSerializer,
    UserSubscriptionRecipeSerializer,
    AvatarUploadSerializer,
)
from recipes.models import (
    Recipe,
    Ingredient,
    Subscription,
    Favorite,
    ShoppingCart
)
from .permission import IsAuthorOrReadOnly
from datetime import datetime


User = get_user_model()
# Create your views here.


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 6
    page_size_query_param = 'limit'
    page_query_param = "page"
    max_page_size = 50


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    pagination_class = None
    serializer_class = IngredientSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['name']


class CustomUserViewSet(UserViewSet):
    queryset = User.objects.all()
    pagination_class = StandardResultsSetPagination
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    @action(methods=['get'], detail=False,
            permission_classes=[IsAuthenticated])
    def me(self, request):
        return super().me(request)

    @action(methods=['put', 'delete'], detail=True,
            permission_classes=[IsAuthenticated])
    def avatar(self, request, id):
        if request.method == 'DELETE' and request.user.avatar:
            request.user.avatar.delete()
            request.user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        if not request.data:
            return Response(
                {'error': 'Отсутствуют данные'},
                status=status.HTTP_400_BAD_REQUEST
            )
        avatarUploadSerializer = AvatarUploadSerializer(
            request.user,
            data=request.data,
            partial=True,
            context={'request': request}
        )
        avatarUploadSerializer.is_valid(raise_exception=True)
        avatarUploadSerializer.save()
        return Response(
            {"avatar": avatarUploadSerializer.data.get("avatar")},
            status=status.HTTP_200_OK
        )

    @action(methods=['post', 'delete'], detail=True,
            permission_classes=[IsAuthenticated])
    def subscribe(self, request, id):
        user = get_object_or_404(User, id=id)

        if request.method == 'POST':
            user_id = request.user.id
            author_id = user.id

            if user_id == author_id:
                return Response({'error': 'Нельзя подписаться на себя'},
                                status=status.HTTP_400_BAD_REQUEST)

            subscription, created = Subscription.objects.get_or_create(
                user_id=user_id,
                author_id=author_id
            )

            if not created:
                return Response(
                    {'error': f'Вы уже подписаны на пользователя {subscription.user}'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            userSubRecipeSerializer = UserSubscriptionRecipeSerializer(
                user,
                context={
                    'request': request,
                }
            )
            return Response(userSubRecipeSerializer.data,
                            status=status.HTTP_201_CREATED)
        subscribe = request.user.author.filter(author=user)
        if subscribe.exists():
            subscribe.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {'error': f'Нельзя удалить отсутствующую подписку на {user.username}'},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(methods=['get'], detail=False,
            permission_classes=[IsAuthenticated])
    def subscriptions(self, request):
        author_users_ids = Subscription.objects.filter(
            user=request.user
        ).values_list('author_id', flat=True)
        queryset = User.objects.filter(id__in=author_users_ids)

        pages = self.paginate_queryset(queryset)
        serializer = UserSubscriptionRecipeSerializer(
            pages,
            many=True,
            context={
                'request': request
            }
        )

        return self.get_paginated_response(serializer.data)
