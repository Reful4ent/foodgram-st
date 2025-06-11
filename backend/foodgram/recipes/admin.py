from django.contrib import admin
from .models import Recipe, RecipeIngredient, Ingredient
from django.utils.safestring import mark_safe
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Subscription, Favorite, ShoppingCart


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
    list_filter = ('author',)
    empty_value_display = '-пусто-'
    inlines = [RecipeIngredientInline]

    @admin.display(description='В избранном')
    def get_favorites_count(self, obj):
        return obj.in_favorites.count()

    @admin.display(description='Ингредиенты')
    @mark_safe
    def get_ingredients_list(self, obj):
        ingredients = obj.recipe_ingredients.select_related('ingredient')
        items = [(f'<br>{i.ingredient.name}'
                  f' - {i.amount}') for i in ingredients]
        return f"<br>{''.join(items)}" if items else "-"

    @admin.display(description='Изображение')
    @mark_safe
    def get_image_preview(self, obj):
        if obj.image:
            return (f'<img src="{obj.image.url}" width="100"'
                    ' style="max-height: 60px; object-fit: cover;" />')
        return "-"


class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit', 'get_recipes_count')
    list_filter = ('measurement_unit',)
    search_fields = ('name', 'measurement_unit',)

    @admin.display(description='Рецептов')
    def get_recipes_count(self, obj):
        return obj.recipes.count()


class SubscriptionInline(admin.TabularInline):
    model = Subscription
    fk_name = 'user'
    extra = 0
    verbose_name = 'Подписка'
    verbose_name_plural = 'Подписки пользователя'


class FavoriteInline(admin.TabularInline):
    model = Favorite
    fk_name = 'user'
    extra = 0
    verbose_name = 'Избранное'
    verbose_name_plural = 'Избранные рецепты'


class ShoppingCartInline(admin.TabularInline):
    model = ShoppingCart
    fk_name = 'user'
    extra = 0
    verbose_name = 'Корзина'
    verbose_name_plural = 'Корзина покупок'


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('id',
                    'username',
                    'get_fio',
                    'email',
                    'get_avatar',
                    'get_recipes_count',
                    'get_subscriptions_count',
                    'get_subscribers_count')
    list_filter = ('email',
                   'username')
    inlines = [SubscriptionInline, FavoriteInline, ShoppingCartInline]

    fieldsets = (
        (None, {'fields': ('email', 'username', 'password')}),
        ('Персональные данные', {
            'fields': ('first_name',
                       'last_name',
                       'avatar')
        })
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email',
                       'username',
                       'password',
                       'first_name',
                       'last_name'),
        }),
    )

    @admin.display(description='ФИО')
    def get_fio(self, obj):
        return f"{obj.first_name} {obj.last_name}"

    @admin.display(description='Рецепты')
    def get_recipes_count(self, obj):
        return obj.recipes.count()

    @admin.display(description='Подписки')
    def get_subscriptions_count(self, obj):
        return obj.subscribed_users.count()

    @admin.display(description='Подписчики')
    def get_subscribers_count(self, obj):
        return obj.author.count()

    @admin.display(description='Аватар')
    @mark_safe
    def get_avatar(self, obj):
        if obj.avatar:
            return (f'<img src="{obj.avatar.url}" width="50"'
                    'height="50" style="border-radius:50%;">')
        return ''


class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'author')
    list_filter = ('user', 'author')
    search_fields = ('user__username', 'author__username')


class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')
    list_filter = ('user',)
    search_fields = ('user__username', 'recipe__username')


class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')
    list_filter = ('user',)
    search_fields = ('user__username', 'recipe__username')


admin.site.register(Subscription, SubscriptionAdmin)
admin.site.register(Favorite, FavoriteAdmin)
admin.site.register(ShoppingCart, ShoppingCartAdmin)
admin.site.register(RecipeIngredient, IngredientRecipeAdmin)
admin.site.register(Ingredient, IngredientAdmin)
