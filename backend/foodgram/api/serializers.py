from rest_framework import serializers
from recipes.models import (
    Recipe,
    RecipeIngredient,
    Ingredient,
    MIN_VALUE_COOKING_TIME, 
    MIN_VALUE_INGREDIENTS_COUNT
)
from django.contrib.auth import get_user_model
from djoser.serializers import UserCreateSerializer
from djoser.serializers import UserSerializer as DjoserUserSerializer
from django.core.files.base import ContentFile
import base64


User = get_user_model()


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


class AvatarUploadSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField()

    def update(self, instance, validated_data):
        avatar = validated_data.get('avatar')
        if avatar is None:
            raise serializers.ValidationError(
                {'avatar': 'Это поле является обязательным.'}
            )

        instance.avatar = avatar
        instance.save()
        return instance

    class Meta:
        model = User
        fields = ('avatar',)


class UserSerializer(DjoserUserSerializer):
    is_subscribed = serializers.SerializerMethodField('get_is_subscribed')

    def get_is_subscribed(self, obj):
        user = self.context['request'].user
        if user:
            return (
                user.is_authenticated
                and user.following.filter(following__exact=obj).exists()
            )
        return False

    class Meta(DjoserUserSerializer.Meta):
        fields = DjoserUserSerializer.Meta.fields + (
            'is_subscribed',
            'avatar'
        )


class BaseUserCreateSerializer(UserCreateSerializer):
    class Meta(UserCreateSerializer.Meta):
        model = User
        fields = ('id',
                  'email',
                  'username',
                  'first_name',
                  'last_name',
                  'password')


class UserSubscriptionRecipeSerializer(UserSerializer):
    recipes = serializers.SerializerMethodField('get_recipes')
    recipes_count = serializers.IntegerField(source='recipes.count',
                                             read_only=True)

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


class RecipeShortSerializer(serializers.ModelSerializer):
    read_only_fields = ("id", "name", "image", "cooking_time")

    class Meta:
        model = Recipe
        fields = ("id", "name", "image", "cooking_time")


class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit')
    read_only_fields = ("id", "name", "measurement_unit", "amount")

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
    is_in_shopping_cart = serializers.SerializerMethodField(
        'get_is_in_shopping_cart'
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
                  'is_favorited',
                  'is_in_shopping_cart')
        read_only_fields = ["author"]

    def get_is_favorited(self, obj):
        user = self.context['request'].user
        if user:
            return (
                user.is_authenticated
                and user.favourites.filter(recipe__exact=obj).exists()
            )
        return False

    def get_is_in_shopping_cart(self, obj):
        user = self.context['request'].user
        if user:
            return (
                user.is_authenticated
                and user.shop_cart.filter(recipe__exact=obj).exists()
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

        return RecipeIngredient.objects.bulk_create(
            RecipeIngredient(
                recipe=recipe,
                ingredient=ingredient['id'],
                amount=ingredient['amount']
            )
            for ingredient in ingredients
        )

    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        validated_data['author'] = self.context['request'].user
        recipe = super().create(validated_data)
        self.push_ingredients(recipe, ingredients_data)
        return recipe

    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        instance = super().update(instance, validated_data)
        instance.recipe_ingredients.all().delete()
        self.push_ingredients(instance, ingredients_data)

        return instance

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        representation["ingredients"] = RecipeIngredientSerializer(
            instance.recipe_ingredients.all(), many=True
        ).data
        return representation
