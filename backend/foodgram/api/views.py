from django.http import FileResponse
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
from io import BytesIO
from django.shortcuts import get_object_or_404, redirect
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
        if request.method == 'PUT':
            if not request.data:
                return Response(status=status.HTTP_400_BAD_REQUEST)
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

        return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['post', 'delete'], detail=True,
            permission_classes=[IsAuthenticated])
    def subscribe(self, request, id):
        user = get_object_or_404(User, id=id)
        subscribe = request.user.following.filter(following=user)

        if request.method == 'POST':
            user_id = request.user.id
            following_id = user.id

            if user_id == following_id:
                return Response({'error': 'Нельзя подписаться на себя'},
                                status=status.HTTP_400_BAD_REQUEST)

            if Subscription.objects.filter(
                user_id=user_id,
                following_id=following_id
            ).exists():
                return Response({
                    'error': 'Вы уже подписаны на этого пользователя'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            Subscription.objects.create(
                user_id=user_id,
                following_id=following_id
            )

            userSubRecipeSerializer = UserSubscriptionRecipeSerializer(
                user,
                context={
                    'request': request,
                    'recipes_limit': request.query_params.get('recipes_limit')
                }
            )
            return Response(userSubRecipeSerializer.data,
                            status=status.HTTP_201_CREATED)
        if subscribe.exists():
            subscribe.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['get'], detail=False,
            permission_classes=[IsAuthenticated])
    def subscriptions(self, request):
        following_users_ids = Subscription.objects.filter(
            user=request.user
        ).values_list('following_id', flat=True)
        queryset = User.objects.filter(id__in=following_users_ids)

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
    author = NumberFilter(method="filter_by_author")

    class Meta:
        model = Recipe
        fields = ['is_favorited', 'is_in_shopping_cart', 'author']

    def filter_is_favorited(self, queryset, name, value):
        user = self.request.user
        if user.is_authenticated and value:
            return queryset.filter(in_favorites__user=user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        user = self.request.user
        if user.is_authenticated and value:
            return queryset.filter(shopping_carts__user=user)
        return queryset

    def filter_by_author(self, queryset, name, value):
        user = self.request.user
        if user.is_authenticated:
            author = get_object_or_404(User, id=value)
            if author:
                return queryset.filter(author_id=author)
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

    @staticmethod
    def _toggle_item(request, pk, model, serializer_class, related_name):
        recipe = get_object_or_404(Recipe, id=pk)
        relation = getattr(request.user, related_name).filter(recipe=recipe)
        if request.method == 'POST':
            if relation.exists():
                return Response(status=status.HTTP_400_BAD_REQUEST)
            model.objects.create(
                user=request.user,
                recipe=recipe
            )
            serializer = serializer_class(
                recipe, 
                context={
                    'request': request
                }
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if relation.exists():
            relation.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['post', 'delete'], detail=True,
            permission_classes=[IsAuthenticated])
    def favorite(self, request, pk):
        return self._toggle_item(
            request,
            pk,
            Favorite,
            RecipeShortSerializer,
            'favourites'
        )

    @action(methods=['post', 'delete'], detail=True,
            permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, pk):
        return self._toggle_item(
            request,
            pk,
            ShoppingCart,
            RecipeShortSerializer,
            'shop_cart')

    @action(methods=["get"], detail=False,
            permission_classes=[IsAuthenticated])
    def download_shopping_cart(self, request):
        recipes_in_cart = Recipe.objects.filter(
            shopping_carts__user=request.user
        ).prefetch_related('recipe_ingredients__ingredient')

        ingredients_summary = {}
        recipes_list = []

        for recipe in recipes_in_cart:
            recipes_list.append(f"{recipe.name} "
                                f"(автор: {recipe.author.username})")
            for recipe_ingredient in recipe.recipe_ingredients.all():
                ingredient = recipe_ingredient.ingredient
                amount = recipe_ingredient.amount
                name = ingredient.name.capitalize()
                unit = ingredient.measurement_unit
                if name not in ingredients_summary:
                    ingredients_summary[name] = {
                        'amount': 0,
                        'unit': unit,
                        'recipes': set()
                    }
                ingredients_summary[name]['amount'] += amount
                ingredients_summary[name]['recipes'].add(f"{recipe.name} (автор: {recipe.author.username})")

        date_str = datetime.now().strftime("%d.%m.%Y")
        shopping_list = [
            f"Список покупок (составлено: {date_str}):"
        ] + [
            f"{idx + 1}. {name} - {data['amount']} {data['unit']}"
            f" (для рецептов: {', '.join(data['recipes'])})"
            for idx, (name, data) in enumerate(ingredients_summary.items())
        ]

        report = '\n'.join([
            'Отчет по списку покупок',
            'Продукты:',
            *shopping_list,
            'Рецепты в корзине:',
            *recipes_list
        ])

        file_content = report.encode('utf-8')  # преобразуем в bytes
        file_buffer = BytesIO()
        file_buffer.write(file_content)
        file_buffer.seek(0)

        response = FileResponse(
            file_buffer,
            as_attachment=True,
            filename='shopping_list.txt'
        )

        return response

    @action(methods=['get'], detail=True, url_path='get-link')
    def get_link(self, request, pk):
        get_object_or_404(Recipe, id=pk)
        short_link = f"https://foodgram.example.org/s/{pk}"
        return Response({'short-link': short_link}, status=status.HTTP_200_OK)


def short_link_redirect(request, short_code):
    recipe = get_object_or_404(Recipe, id=short_code)
    return redirect(f'/recipes/{recipe.id}/')
