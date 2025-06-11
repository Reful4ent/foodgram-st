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

    def get_fio(self, obj):
        return f"{obj.first_name} {obj.last_name}"
    get_fio.short_description = 'ФИО'

    def get_recipes_count(self, obj):
        return obj.recipes.count()
    get_recipes_count.short_description = 'Рецепты'

    def get_subscriptions_count(self, obj):
        return obj.user_subscribed.count()
    get_subscriptions_count.short_description = 'Подписки'

    def get_subscribers_count(self, obj):
        return obj.following.count()
    get_subscribers_count.short_description = 'Подписчики'

    @mark_safe
    def get_avatar(self, obj):
        if obj.avatar:
            return (f'<img src="{obj.avatar.url}" width="50"'
                    'height="50" style="border-radius:50%;">')
        return ''
    get_avatar.short_description = 'Аватар'


class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'following')
    list_filter = ('user', 'following')
    search_fields = ('user__username', 'following__username')


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
