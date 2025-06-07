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

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username
