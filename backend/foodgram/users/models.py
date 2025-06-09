from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator


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
    is_subscribed = models.BooleanField(
        verbose_name='Подписан на данного пользователя',
        default=False
    )
    avatar = models.ImageField(
        verbose_name='Изображение аватара',
        blank=True,
        null=True,
        upload_to="users/avatars/",
    )
    is_blocked = models.BooleanField(
        default=False,
        verbose_name='Заблокирован'
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'last_name', 'first_name']

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username


class Subscription(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='user_subscribed',
        verbose_name='Пользователь'
    )
    subscribed = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscribers',
        verbose_name='Подписчик'
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        unique_together = ('user', 'subscribed')
        ordering = ['id']

    def __str__(self):
        return (f"{self.user.username} подписан "
                f"на {self.subscribed.username}")


class Favorite(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='user_recipe',
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        'recipes.Recipe',
        on_delete=models.CASCADE,
        related_name='users_in_favorite',
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
        related_name='user_cart',
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        'recipes.Recipe',
        on_delete=models.CASCADE,
        related_name="user_in_shopping_carts",
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
