from django.contrib.auth import get_user_model
from django_filters.rest_framework import DjangoFilterBackend
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
    SubscribeSerializer,
    FavoriteSerializer
)
from users.models import Subscription
from ingredients.models import Ingredient
from recipes.models import Recipe
from .permission import IsAuthorOrReadOnly


User = get_user_model()
# Create your views here.


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'limit'
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
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(methods=['put', 'delete'], detail=True,
            permission_classes=[IsAuthenticated])
    def avatar(self, request, id):
        if request.method == 'DELETE' and request.user.avatar:
            request.user.avatar.delete()
            request.user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        if request.method == 'PUT':
            if not request.data:
                return Response(status=status.HTTP_400_BAD_REQUEST)
            user_serializer = UserSerializer(
                request.user,
                data=request.data,
                partial=True,
                context={'request': request}
            )
            user_serializer.is_valid(raise_exception=True)
            user_serializer.save()
            return Response(
                {"avatar": user_serializer.data.get("avatar")},
                status=status.HTTP_200_OK
            )

        return Response(status=status.HTTP_400_BAD_REQUEST)
    
    @action(methods=['post', 'delete'], detail=True,
            permission_classes=[IsAuthenticated])
    def subscribe(self, request, id):
        user = get_object_or_404(User, id=id)
        subscribe = request.user.subscribers.filter(subscribed=user)
        if request.method == 'POST':
            subscribeSerializer = SubscribeSerializer(
                data={
                    'user': request.user.id,
                    'subscribed': user.id
                },
                context={
                    'request': request
                }
            )
            subscribeSerializer.is_valid(raise_exception=True)
            subscribeSerializer.save()

            userSubRecipeSerializer = UserSubscriptionRecipeSerializer(
                user,
                context={
                    'request': request,
                    'recipes_limit': request.query_params.get('recipes_limit')
                }
            )
            return Response(userSubRecipeSerializer.data,
                            status=status.HTTP_201_CREATED)
        else:
            if subscribe.exists():
                subscribe.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['get'], detail=False,
            permission_classes=[IsAuthenticated])
    def subscriptions(self, request):

        subscribed_users_ids = Subscription.objects.filter(
            user=request.user
        ).values_list('subscribed_id', flat=True)
        queryset = User.objects.filter(id__in=subscribed_users_ids)

        pages = self.paginate_queryset(queryset)
        serializer = UserSubscriptionRecipeSerializer(
            pages,
            many=True,
            context={
                'request': request
            }
        )

        return self.get_paginated_response(serializer.data)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    pagination_class = StandardResultsSetPagination
    serializer_class = RecipeSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]
    filter_backends = [DjangoFilterBackend]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context

    @action(methods=['post', 'delete'], detail=True,
            permission_classes=[IsAuthenticated])
    def favorite(self, request, pk):
        recipe = get_object_or_404(Recipe, id=pk)
        favorite = request.user.user_recipe.filter(recipe=recipe)
        if request.method == 'POST':
            if favorite.exists():
                return Response(status=status.HTTP_400_BAD_REQUEST)
            favoriteSerializer = FavoriteSerializer(
                data={
                    'user': request.user.id,
                    'recipe': recipe.id
                },
                context={
                    'request': request
                }
            )
            favoriteSerializer.is_valid(raise_exception=True)
            favoriteSerializer.save()
            recipeShortSerializer = RecipeShortSerializer(
                recipe,
                context={
                    'request': request
                }
            )
            return Response(recipeShortSerializer.data,
                            status=status.HTTP_201_CREATED)
        else:
            if favorite.exists():
                favorite.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(status=status.HTTP_400_BAD_REQUEST)
