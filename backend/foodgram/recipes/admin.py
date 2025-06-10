from django.contrib import admin
from .models import Recipe, RecipeIngredient, Ingredient
from django.utils.safestring import mark_safe


class IngredientRecipeAdmin(admin.ModelAdmin):
    list_display = ('id', 'recipe', 'ingredient', 'amount',)
    list_filter = ('recipe', 'ingredient')
    search_fields = ('name',)


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1
    min_num = 1
    verbose_name = 'Ингредиент'
    verbose_name_plural = 'Ингредиенты'
    fields = ('ingredient', 'amount')


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'cooking_time',
        'author',
        'get_favorites_count',
        'get_ingredients_list',
        'get_image_preview',
    )
    search_fields = ('name', 'author__username')
    list_filter = ('author', 'name')
    empty_value_display = '-пусто-'
    inlines = [RecipeIngredientInline]

    def get_favorites_count(self, obj):
        return obj.in_favorites.count()
    get_favorites_count.short_description = 'В избранном'

    @mark_safe
    def get_ingredients_list(self, obj):
        ingredients = obj.recipe_ingredients.select_related('ingredient')
        items = [(f'<li>{i.ingredient.name}'
                  f' - {i.amount}</li>') for i in ingredients]
        return f"<ul>{''.join(items)}</ul>" if items else "-"
    get_ingredients_list.short_description = 'Ингредиенты'

    @mark_safe
    def get_image_preview(self, obj):
        if obj.image:
            return (f'<img src="{obj.image.url}" width="100"'
                    ' style="max-height: 60px; object-fit: cover;" />')
        return "-"
    get_image_preview.short_description = 'Изображение'


class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit', 'get_recipes_count')
    list_filter = ('measurement_unit',)
    search_fields = ('name', 'measurement_unit',)

    def get_recipes_count(self, obj):
        return obj.recipes.count()
    get_recipes_count.short_description = 'Рецептов'


admin.site.register(Recipe, RecipeAdmin)
admin.site.register(RecipeIngredient, IngredientRecipeAdmin)
admin.site.register(Ingredient, IngredientAdmin)
