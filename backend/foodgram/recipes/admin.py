from django.contrib import admin
from .models import Recipe, RecipeIngredient, Ingredient


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


class RecipeAdmin(admin.ModelAdmin):
    list_display = ('id', 'author', 'name')
    search_fields = ('name',)
    list_filter = ('author',)
    empty_value_display = 'empty'
    inlines = [RecipeIngredientInline]


class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    list_filter = ('name',)
    search_fields = ('name',)


admin.site.register(Recipe, RecipeAdmin)
admin.site.register(RecipeIngredient, IngredientRecipeAdmin)
admin.site.register(Ingredient, IngredientAdmin)
