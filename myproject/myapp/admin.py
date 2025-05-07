from django.contrib import admin
from .models import Product, SubscriptionPlan, Subscription, Order, OrderItem

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'price', 'stock', 'is_active')
    list_editable = ('price', 'stock', 'is_active')
    search_fields = ('name',)
    list_filter = ('is_active', 'created_at')

@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'duration', 'price', 'is_active')
    list_filter = ('duration', 'is_active')
    search_fields = ('name',)

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'plan', 'start_date', 'end_date', 'status')
    list_filter = ('status', 'start_date')
    search_fields = ('user__username', 'plan__name')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'total_amount', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('user__username',)

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'product', 'quantity', 'price')
    search_fields = ('product__name',)
