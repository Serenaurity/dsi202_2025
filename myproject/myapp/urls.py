from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

# ไม่ต้องมี app_name = 'myapp' เพื่อหลีกเลี่ยงปัญหาการใช้ URL namespaces
# ถ้าเทมเพลตไม่ได้ถูกเขียนให้รองรับ namespaces

urlpatterns = [
    # การรับรองตัวตน
    path('login/', views.login_view, name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
    path('register/', views.register, name='register'),

    # หน้าหลักและรายการสินค้า
    path('', views.home, name='home'),
    path('products/', views.ProductListView.as_view(), name='product_list'),
    path('products/<int:pk>/', views.ProductDetailView.as_view(), name='product_detail'),
    
    # แพ็คเกจสมาชิก
    path('subscriptions/', views.SubscriptionPlanListView.as_view(), name='subscription_list'),
    path('subscriptions/<int:pk>/', views.SubscriptionDetailView.as_view(), name='subscription_detail'),
    path('subscriptions/<int:plan_id>/subscribe/', views.subscribe, name='subscribe'),
    path('my-subscriptions/', views.UserSubscriptionListView.as_view(), name='user_subscriptions'),
    
    # ตะกร้าสินค้า
    path('cart/', views.view_cart, name='cart'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/update/<int:item_id>/', views.update_cart_item, name='update_cart_item'),
    path('checkout/', views.checkout, name='checkout'),
    
    # แดชบอร์ดและคอนเทนต์
    path('dashboard/', views.user_dashboard, name='dashboard'),
    path('content/', views.content_list, name='content_list'),
    path('community/', views.community_forum, name='community_forum'),
    
    # ความก้าวหน้า
    path('progress/', views.track_progress, name='track_progress'),
    path('progress/add/', views.add_progress, name='add_progress'),

    # ตั้งค่าโปรไฟล์
    path('profile/setup/', views.profile_setup, name='profile_setup'),
    path('profile/update/', views.profile_update, name='profile_update'),
    path('password/change/', auth_views.PasswordChangeView.as_view(
        template_name='myapp/password_change.html', 
        success_url='/dashboard/'), name='password_change'),
    
    # แผนออกกำลังกาย
    path('exercise-plan/', views.exercise_plan, name='exercise_plan'),
    path('exercise-plan/view/', views.view_exercise_plan, name='view_exercise_plan'),
    path('exercise-plan/day/<int:day_id>/', views.view_workout_day, name='view_workout_day'),
    
    # แผนอาหาร
    path('meal-plan/', views.meal_plan, name='meal_plan'),
    path('meal-plan/view/', views.view_meal_plan, name='view_meal_plan'),
    path('meal-plan/day/<int:meal_id>/', views.view_daily_meal, name='view_daily_meal'),
    path('recipe/<int:recipe_id>/', views.view_recipe, name='view_recipe'),

    # ประวัติการสั่งซื้อ
    path('orders/', views.order_history, name='order_history'),
    path('orders/<int:order_id>/', views.order_detail, name='order_detail'),
    
    # หน้าเพิ่มเติม
    path('wishlist/', views.wishlist, name='wishlist'),
    # เพิ่มในรายการ urlpatterns
    path('wishlist/remove/<int:item_id>/', views.remove_from_wishlist, name='remove_from_wishlist'),
    path('support/', views.support, name='support'),
    path('nutrition-plan/', views.nutrition_plan, name='nutrition_plan'),
]
