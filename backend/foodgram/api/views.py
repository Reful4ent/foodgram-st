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
        subscribe = request.user.author.filter(author=user)

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
        if subscribe.exists():
            subscribe.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {'error': 'Нельзя удалить отсутствующую подписку'},
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
    def _toggle_item(request, pk, model):
        recipe = get_object_or_404(Recipe, id=pk)
        relation = getattr(
            request.user,
            model._meta.default_related_name
        )

        if request.method == 'POST':
            _, created = relation.get_or_create(recipe=recipe)
        
            if not created:
                return Response(
                    {'error': 'Уже добавлен'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            serializer = RecipeShortSerializer(
                recipe,
                context={
                    'request': request
                }
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if relation.exists():
            relation.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {'error': 'Нельзя удалить несуществующие данные'},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(methods=['post', 'delete'], detail=True,
            permission_classes=[IsAuthenticated])
    def favorite(self, request, pk):
        return self._toggle_item(
            request,
            pk,
            Favorite
        )

    @action(methods=['post', 'delete'], detail=True,
            permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, pk):
        return self._toggle_item(
            request,
            pk,
            ShoppingCart
        )

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
            f"{idx}. {name} - {data['amount']} {data['unit']}"
            f" (для рецептов: {', '.join(data['recipes'])})"
            for idx, (name, data) in enumerate(ingredients_summary.items(),
                                               start=1)
        ]

        report = '\n'.join([
            'Отчет по списку покупок',
            'Продукты:',
            *shopping_list,
            'Рецепты в корзине:',
            *recipes_list
        ])

        response = FileResponse(
            report,
            as_attachment=True,
            filename='shopping_list.txt'
        )

        return response

    @action(methods=['get'], detail=True, url_path='get-link')
    def get_link(self, request, pk):
        recipe = self.get_object()
        short_code = ''.join(
            [c for c in recipe.name if c.isalnum()])[:6] or 'default'
        return Response(
            {'short-link': f'https://foodgram.ru/s/ {short_code}'},
            status=HTTPStatus.OK
        )
