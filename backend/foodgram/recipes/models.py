from django.db import models
from django.core.validators import MinValueValidator
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator

MIN_VALUE_COOKING_TIME = 1
MIN_VALUE_INGREDIENTS_COUNT = 1


class Ingredient(models.Model):
    name = models.CharField(
        unique=True,
        max_length=128,
        verbose_name='Название'
    )
    measurement_unit = models.CharField(
        max_length=64,
        verbose_name='Единица измерения'
    )

    class Meta:
        verbose_name = 'Ингредиенты'
        verbose_name_plural = 'Ингредиенты'
        ordering = ['name']

    def __str__(self):
        return f'{self.name} ({self.measurement_unit})'


class User(AbstractUser):
    email = models.EmailField(
        unique=True,
        max_length=254,
        verbose_name='Почтовый ящик',
    )
    username = models.CharField(
        unique=True,
        max_length=150,
        verbose_name='Никнейм',
        validators=[RegexValidator(
            regex=r'^[\w.@+-]+$',
            message=(
                'Никнейм пользователя может содержать только буквы,'
                ' цифры и символы: . @ + - _'
            )
        )]
    )
    first_name = models.CharField(
        max_length=150,
        verbose_name='Имя'
    )
    last_name = models.CharField(
        max_length=150,
        verbose_name='Фамилия'
    )
    avatar = models.ImageField(
        verbose_name='Изображение аватара',
        blank=True,
        null=True,
        upload_to="recipes/avatars/",
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'last_name', 'first_name']

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ['username']

    def __str__(self):
        return self.username


class Subscription(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='user_subscribed',
        verbose_name='Пользователь'
    )
    following = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Подписки авторов',
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        unique_together = ('user', 'following')
        ordering = ['id']

    def __str__(self):
        return (f"{self.user.username} подписан "
                f"на {self.following.username}")


class Favorite(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favourites',
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        'recipes.Recipe',
        on_delete=models.CASCADE,
        related_name='in_favorites',
        verbose_name='Рецепт'
    )

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        unique_together = ('user', 'recipe')
        ordering = ['id']

    def __str__(self):
        return (f"{self.user.username} в избранном "
                f"{self.recipe.name}")


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shop_cart',
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        'recipes.Recipe',
        on_delete=models.CASCADE,
        related_name="shopping_carts",
        verbose_name="Рецепт",
    )

    class Meta:
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Список покупок'
        unique_together = ('user', 'recipe')
        ordering = ['id']

    def __str__(self):
        return (f"{self.user.username} в корзине "
                f"{self.recipe.name}")


class Recipe(models.Model):
    name = models.CharField(
        max_length=256,
        verbose_name='Название'
    )
    text = models.TextField(
        verbose_name='Описание'
    )
    cooking_time = models.IntegerField(
        validators=[MinValueValidator(MIN_VALUE_COOKING_TIME)],
        verbose_name='Время приготовления (в минутах)'
    )
    image = models.ImageField(
        verbose_name='Изображение рецепта',
        upload_to='recipes/images'
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        related_name='recipes',
        verbose_name='Ингредиенты'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="recipes",
        verbose_name="Автор",
    )


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients',
        verbose_name='Рецепт'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients',
        verbose_name='Ингредиент'
    )
    amount = models.IntegerField(
        validators=[MinValueValidator(MIN_VALUE_INGREDIENTS_COUNT)],
        verbose_name='Количество'
    )

    class Meta:
        verbose_name = 'Ингредиент рецепта'
        verbose_name_plural = 'Ингредиенты рецептов'
        unique_together = ('recipe', 'ingredient')
        ordering = ('recipe', 'ingredient',)

    def __str__(self):
        return (f'{self.ingredient.name} в рецепте '
                f'{self.recipe.name} - {self.amount}')
