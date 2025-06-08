from django.http import HttpResponse
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
    SubscribeSerializer,
    FavoriteSerializer,
    ShoppingCartSerializer
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


class RecipeFilter(FilterSet):
    is_favorited = BooleanFilter(method="filter_is_favorited")
    is_in_shopping_cart = BooleanFilter(method="filter_is_in_shopping_cart")
    author = NumberFilter(field_name="author__id")

    class Meta:
        model = Recipe
        fields = ['is_favorited', 'is_in_shopping_cart', 'author']

    def filter_is_favorited(self, queryset, name, value):
        user = self.request.user
        if user.is_authenticated and value:
            return queryset.filter(users_in_favorite__user=user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        user = self.request.user
        if user.is_authenticated and value:
            return queryset.filter(user_in_shopping_carts__user=user)
        return queryset


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    pagination_class = StandardResultsSetPagination
    serializer_class = RecipeSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter

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

    @action(methods=['post', 'delete'], detail=True,
            permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, pk):
        recipe = get_object_or_404(Recipe, id=pk)
        shopcart = request.user.user_cart.filter(recipe=recipe)

        if request.method == "POST":
            if shopcart.exists():
                return Response(status=status.HTTP_400_BAD_REQUEST)
            shoppingCartSerializer = ShoppingCartSerializer(
                data={
                    'user': request.user.id,
                    'recipe': recipe.id
                },
                context={
                    'request': request
                }
            )
            shoppingCartSerializer.is_valid(raise_exception=True)
            shoppingCartSerializer.save()
            recipeShortSerializer = RecipeShortSerializer(
                recipe,
                context={
                    'request': request
                }
            )
            return Response(recipeShortSerializer.data,
                            status=status.HTTP_201_CREATED)
        else:
            if shopcart.exists():
                shopcart.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(methods=["get"], detail=False,
            permission_classes=[IsAuthenticated])
    def download_shopping_cart(self, request):
        # Get all recipes in the user's shopping cart with their ingredients
        recipes_in_cart = Recipe.objects.filter(
            user_in_shopping_carts__user=request.user
        ).prefetch_related('recipe_ingredients__ingredient')

        ingredients_summary = {}

        for recipe in recipes_in_cart:
            # Access the recipe ingredients through the intermediate model
            for recipe_ingredient in recipe.recipe_ingredients.all():
                ingredient = recipe_ingredient.ingredient
                amount = recipe_ingredient.amount
                name = ingredient.name
                unit = ingredient.measurement_unit

                if name in ingredients_summary:
                    ingredients_summary[name]['amount'] += amount
                else:
                    ingredients_summary[name] = {
                        'amount': amount,
                        'unit': unit
                    }

        shopping_list = ["Список покупок:\n"]
        for name, data in ingredients_summary.items():
            shopping_list.append(f"{name} - {data['amount']} {data['unit']}")

        file_content = "\n".join(shopping_list)

        response = HttpResponse(
            file_content,
            content_type="text/plain; charset=utf-8"
        )
        response['Content-Disposition'] = 'attachment; filename="shopping_list.txt"'

        return response
    
    @action(methods=['get'], detail=True, url_path='get-link')
    def get_link(self, request, pk):
        get_object_or_404(Recipe, id=pk)
        link = request.build_absolute_uri(f"/recipes/{pk}/")
        return Response({"short-link": link}, status=status.HTTP_200_OK)
