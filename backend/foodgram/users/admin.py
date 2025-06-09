from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Subscription, Favorite, ShoppingCart


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
    list_display = ('email',
                    'username',
                    'first_name',
                    'last_name')
    list_filter = ('email',
                   'username')
    inlines = [SubscriptionInline, FavoriteInline, ShoppingCartInline]

    fieldsets = (
        (None, {'fields': ('email', 'username', 'password')}),
        ('Персональные данные', {
            'fields': ('first_name',
                       'last_name',
                       'avatar')
        }),
        ('Статус', {'fields': ('is_blocked',)}),
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


class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'subscribed')
    list_filter = ('user', 'subscribed')
    search_fields = ('user__username', 'subscribed__username')


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
