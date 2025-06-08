from rest_framework import serializers
from ingredients.models import Ingredient
from recipes.models import Recipe, RecipeIngredient
from users.models import Subscription, Favorite, ShoppingCart
from django.contrib.auth import get_user_model
from djoser.serializers import UserCreateSerializer as BaseUserCreateSerializer
from django.core.files.base import ContentFile
import base64


User = get_user_model()
MIN_VALUE_INGREDIENTS_COUNT = 1
MIN_VALUE_COOKING_TIME = 1


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = (
            'id',
            'name',
            'measurement_unit',
        )


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(
                base64.b64decode(imgstr),
                name=f"avatar.{ext}"
            )
        return super().to_internal_value(data)


class UserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField('get_is_subscribed')
    avatar = Base64ImageField(required=False, allow_null=True)

    def get_is_subscribed(self, obj):
        user = self.context['request'].user
        if user:
            return (
                user.is_authenticated
                and user.subscribers.filter(subscribed__exact=obj).exists()
            )
        return False

    class Meta:
        model = User
        fields = ('email',
                  'id',
                  'username',
                  'first_name',
                  'last_name',
                  'is_subscribed',
                  'avatar')


class UserCreateSerializer(BaseUserCreateSerializer):
    class Meta(BaseUserCreateSerializer.Meta):
        model = User
        fields = ('id',
                  'email',
                  'username',
                  'first_name',
                  'last_name',
                  'password')


class SubscribeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = ("user", "subscribed")

    def validate(self, data):
        user_id = data.get('user')
        subscribed_id = data.get('subscribed')

        if user_id == subscribed_id:
            raise serializers.ValidationError('Нельзя подписаться на себя')

        if Subscription.objects.filter(user_id=user_id,
                                       subscribed_id=subscribed_id).exists():
            raise serializers.ValidationError("Вы уже подписаны "
                                              "на этого пользователя")

        return data


class UserSubscriptionRecipeSerializer(serializers.ModelSerializer):
    recipes = serializers.SerializerMethodField('get_recipes')
    recipes_count = serializers.SerializerMethodField('get_recipies_count')

    class Meta:
        model = User
        fields = ('id',
                  'email',
                  'username',
                  'first_name',
                  'last_name',
                  'is_subscribed',
                  'avatar',
                  'recipes',
                  'recipes_count')

    def get_recipes(self, obj):
        request = self.context.get('request')
        if not request:
            return []

        recipes_queryset = obj.recipes.all()

        limit = request.query_params.get("recipes_limit")
        if limit and limit.isdigit():
            recipes_queryset = recipes_queryset[:int(limit)]

        return RecipeShortSerializer(
            recipes_queryset,
            many=True,
            context={'request': request}
        ).data

    def get_recipies_count(self, obj):
        return obj.recipes.count()


class RecipeShortSerializer(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = ("id", "name", "image", "cooking_time")


class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit')

    class Meta:
        model = RecipeIngredient
        fields = ('id',
                  'name',
                  'measurement_unit',
                  'amount')


class RecipeIngredientCreateSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    amount = serializers.IntegerField(min_value=MIN_VALUE_INGREDIENTS_COUNT)

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class RecipeSerializer(serializers.ModelSerializer):
    image = Base64ImageField(required=True, allow_null=False)
    author = UserSerializer(read_only=True)
    ingredients = RecipeIngredientCreateSerializer(many=True, write_only=True)
    is_favorited = serializers.SerializerMethodField('get_is_favorited')
    is_in_shopping_cart = serializers.SerializerMethodField('get_is_in_shopping_cart')
    amount = serializers.IntegerField(
        write_only=True,
        required=False,
        min_value=MIN_VALUE_INGREDIENTS_COUNT,
    )
    cooking_time = serializers.IntegerField(
        min_value=MIN_VALUE_COOKING_TIME
    )

    class Meta:
        model = Recipe
        fields = ('id',
                  'author',
                  'ingredients',
                  'name',
                  'image',
                  'text',
                  'cooking_time',
                  'amount',
                  'is_favorited',
                  'is_in_shopping_cart')
        read_only_fields = ["author"]

    def get_is_favorited(self, obj):
        user = self.context['request'].user
        if user:
            return (
                user.is_authenticated
                and user.user_recipe.filter(recipe__exact=obj).exists()
            )
        return False

    def get_is_in_shopping_cart(self, obj):
        user = self.context['request'].user
        if user:
            return (
                user.is_authenticated
                and user.user_cart.filter(recipe__exact=obj).exists()
            )
        return False

    def validate(self, attrs):
        ingredients = self.initial_data.get('ingredients')
        if ingredients is None or len(ingredients) == 0:
            raise serializers.ValidationError(
                'Список ингредиентов не должен быть пустым!.')

        ingredients_ids = [ingredient['id']
                           for ingredient in ingredients]

        if len(ingredients_ids) != len(set(ingredients_ids)):
            raise serializers.ValidationError(
                'Ингредиенты не должны повторяться.')
        return attrs

    def push_ingredients(self, recipe, ingredients):
        recipe.recipe_ingredients.all().delete()

        return RecipeIngredient.objects.bulk_create([
            RecipeIngredient(
                recipe=recipe,
                ingredient=ingredient['id'],
                amount=ingredient['amount']
            )
            for ingredient in ingredients
        ])

    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients', None)
        recipe = Recipe.objects.create(author=self.context["request"].user,
                                       **validated_data)

        self.push_ingredients(recipe, ingredients_data)
        return recipe

    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('ingredients', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if ingredients_data is not None:
            instance.recipe_ingredients.all().delete()
            self.push_ingredients(instance, ingredients_data)

        return instance

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        representation["ingredients"] = RecipeIngredientSerializer(
            instance.recipe_ingredients.all(), many=True
        ).data
        return representation


class FavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Favorite
        fields = ('user', 'recipe')


class ShoppingCartSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShoppingCart
        fields = ('user', 'recipe')
