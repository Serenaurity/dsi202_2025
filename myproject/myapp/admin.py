# myproject/myapp/admin.py
from django.contrib import admin
from .models import (
    UserProfile, Product, Order, OrderItem, Wishlist,
    SubscriptionPlan, Subscription, FeatureUsage,
    ExercisePlan, WorkoutDay, Exercise, WorkoutExercise,
    MealPlan, Recipe, Ingredient, DailyMeal, MealItem, NutritionPlan,
    Content, Article, Video, ForumTopic, ForumThread, ForumReply,
    Progress
)

# Base class สำหรับ admin models เพื่อลดความซ้ำซ้อน
class BaseAdmin(admin.ModelAdmin):
    list_per_page = 25
    
    def get_readonly_fields(self, request, obj=None):
        # ถ้าไม่ใช่ superuser ให้แสดงฟิลด์ created_at และ updated_at เป็น readonly
        if not request.user.is_superuser and hasattr(self.model, 'created_at'):
            return ['created_at', 'updated_at']
        return []

# User Management
@admin.register(UserProfile)
class UserProfileAdmin(BaseAdmin):
    list_display = ['user', 'date_of_birth', 'gender', 'goal']
    search_fields = ['user__username', 'user__email']
    list_filter = ['gender', 'goal']

# Shop Management
@admin.register(Product)
class ProductAdmin(BaseAdmin):
    list_display = ['name', 'price', 'stock', 'category', 'is_active']
    list_filter = ['category', 'is_active']
    search_fields = ['name', 'description']

@admin.register(Order)
class OrderAdmin(BaseAdmin):
    list_display = ['user', 'date_ordered', 'complete', 'transaction_id']
    list_filter = ['complete']
    search_fields = ['user__username', 'transaction_id']

@admin.register(OrderItem)
class OrderItemAdmin(BaseAdmin):
    list_display = ['product', 'order', 'quantity']
    
@admin.register(Wishlist)
class WishlistAdmin(BaseAdmin):
    list_display = ['user', 'product', 'added_date']

# Subscription Management
@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(BaseAdmin):
    list_display = ['name', 'price', 'duration', 'is_active']
    list_filter = ['is_active', 'duration']

@admin.register(Subscription)
class SubscriptionAdmin(BaseAdmin):
    list_display = ['user', 'plan', 'start_date', 'end_date', 'is_active']
    list_filter = ['is_active', 'plan']
    search_fields = ['user__username', 'user__email']

# Exercise Management
@admin.register(ExercisePlan)
class ExercisePlanAdmin(BaseAdmin):
    list_display = ['name', 'user', 'goal', 'duration_weeks']
    list_filter = ['goal']
    search_fields = ['name', 'user__username']

@admin.register(Exercise)
class ExerciseAdmin(BaseAdmin):
    list_display = ['name', 'category', 'difficulty']
    list_filter = ['category', 'difficulty']
    search_fields = ['name', 'description']

# ลงทะเบียนโมเดลที่เหลือด้วยการลดรูปแบบที่ซับซ้อน
admin.site.register(WorkoutDay)
admin.site.register(WorkoutExercise)
admin.site.register(MealPlan)
admin.site.register(Recipe)
admin.site.register(Ingredient)
admin.site.register(DailyMeal)
admin.site.register(MealItem)
admin.site.register(NutritionPlan)
admin.site.register(Content)
admin.site.register(Article)
admin.site.register(Video)
admin.site.register(ForumTopic)
admin.site.register(ForumThread)
admin.site.register(ForumReply)
admin.site.register(Progress)
admin.site.register(FeatureUsage)