from django.contrib import admin
from .models import (
    Product, SubscriptionPlan, Subscription, Order, OrderItem,
    UserProfile, ExercisePlan, MealPlan, DailyMeal, WorkoutDay, WorkoutExercise,
    Exercise, Recipe, Ingredient, MealItem, Content, Article, Video,
    ForumTopic, ForumThread, ForumReply, Progress, NutritionPlan
)

# Product Management
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'price', 'stock', 'is_active')
    list_editable = ('price', 'stock', 'is_active')
    search_fields = ('name', 'description')
    list_filter = ('is_active', 'created_at')

# Subscription Management
@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'duration', 'price', 'is_active')
    list_editable = ('price', 'is_active')
    search_fields = ('name', 'description')
    list_filter = ('duration', 'is_active')

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'plan', 'start_date', 'end_date', 'status')
    list_filter = ('status', 'start_date')
    search_fields = ('user__username', 'plan__name')

# Order Management
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'order_number', 'user', 'total_amount', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('user__username', 'order_number')

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'product', 'quantity', 'price')
    search_fields = ('product__name', 'order__order_number')

# User Profiles
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'gender', 'height', 'weight', 'activity_level', 'has_completed_profile')
    list_filter = ('gender', 'activity_level', 'has_completed_profile')
    search_fields = ('user__username', 'medical_conditions')

# Exercise Plans
@admin.register(ExercisePlan)
class ExercisePlanAdmin(admin.ModelAdmin):
    list_display = ('user', 'goal', 'level', 'days_per_week', 'created_at')
    list_filter = ('goal', 'level', 'days_per_week', 'created_at')
    search_fields = ('user__username',)

@admin.register(WorkoutDay)
class WorkoutDayAdmin(admin.ModelAdmin):
    list_display = ('exercise_plan', 'day_number', 'focus')
    list_filter = ('focus', 'day_number')
    search_fields = ('exercise_plan__user__username',)

@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    list_display = ('name', 'muscle_group', 'difficulty', 'equipment_required')
    list_filter = ('muscle_group', 'difficulty', 'equipment_required')
    search_fields = ('name', 'description', 'instructions')

@admin.register(WorkoutExercise)
class WorkoutExerciseAdmin(admin.ModelAdmin):
    list_display = ('workout_day', 'exercise', 'sets', 'reps', 'order')
    list_filter = ('workout_day__focus',)
    search_fields = ('exercise__name', 'notes')

# Meal and Nutrition Plans
@admin.register(MealPlan)
class MealPlanAdmin(admin.ModelAdmin):
    list_display = ('user', 'goal', 'daily_calories', 'meals_per_day', 'created_at')
    list_filter = ('goal', 'meals_per_day', 'created_at')
    search_fields = ('user__username', 'dietary_restrictions', 'allergies')

@admin.register(DailyMeal)
class DailyMealAdmin(admin.ModelAdmin):
    list_display = ('meal_plan', 'day_number')
    list_filter = ('day_number',)
    search_fields = ('meal_plan__user__username',)

@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'meal_type', 'diet_type', 'calories_per_serving', 'prep_time', 'cook_time')
    list_filter = ('meal_type', 'diet_type')
    search_fields = ('name', 'description', 'instructions')

@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'name', 'amount')
    search_fields = ('recipe__name', 'name')

@admin.register(MealItem)
class MealItemAdmin(admin.ModelAdmin):
    list_display = ('daily_meal', 'recipe', 'meal_time')
    list_filter = ('meal_time',)
    search_fields = ('recipe__name',)

@admin.register(NutritionPlan)
class NutritionPlanAdmin(admin.ModelAdmin):
    list_display = ('user', 'goal', 'calorie_target', 'protein_ratio', 'carb_ratio', 'fat_ratio')
    list_filter = ('goal',)
    search_fields = ('user__username', 'dietary_restriction')

# Content Management
@admin.register(Content)
class ContentAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'is_published', 'published_at')
    list_editable = ('is_published',)
    list_filter = ('category', 'is_published', 'published_at')
    search_fields = ('title', 'content')

@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'category', 'published', 'date')
    list_editable = ('published',)
    list_filter = ('category', 'published', 'date')
    search_fields = ('title', 'content', 'author__username')
    prepopulated_fields = {'slug': ('title',)}

@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'duration', 'published', 'date')
    list_editable = ('published',)
    list_filter = ('category', 'published', 'date')
    search_fields = ('title', 'description')

# Community Forum
@admin.register(ForumTopic)
class ForumTopicAdmin(admin.ModelAdmin):
    list_display = ('name', 'last_activity')
    search_fields = ('name', 'description')

@admin.register(ForumThread)
class ForumThreadAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'topic', 'created_at', 'updated_at')
    list_filter = ('topic', 'created_at')
    search_fields = ('title', 'content', 'author__username')

@admin.register(ForumReply)
class ForumReplyAdmin(admin.ModelAdmin):
    list_display = ('thread', 'author', 'created_at', 'updated_at')
    list_filter = ('created_at',)
    search_fields = ('content', 'author__username', 'thread__title')

# User Progress
@admin.register(Progress)
class ProgressAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'weight', 'exercise_minutes')
    list_filter = ('date',)
    search_fields = ('user__username', 'notes')