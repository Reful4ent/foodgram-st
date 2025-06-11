from django.db import models
from django.core.validators import MinValueValidator
from ingredients.models import Ingredient
from users.models import User

MIN_VALUE_COOKING_TIME = 1
MIN_VALUE_INGREDIENTS_COUNT = 1


# Create your models here.
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
        ordering = ('recipe', 'ingredient')

    def __str__(self):
        return (f'{self.ingredient.name} в рецепте '
                f'{self.recipe.name} - {self.amount}')
