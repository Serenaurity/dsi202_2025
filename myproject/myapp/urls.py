from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('products/', views.ProductListView.as_view(), name='product_list'),
    path('products/<int:pk>/', views.ProductDetailView.as_view(), name='product_detail'),
    path('subscriptions/', views.SubscriptionPlanListView.as_view(), name='subscription_list'),
    path('subscriptions/<int:pk>/', views.SubscriptionDetailView.as_view(), name='subscription_detail'),
    path('subscriptions/<int:plan_id>/subscribe/', views.subscribe, name='subscribe'),
    path('my-subscriptions/', views.UserSubscriptionListView.as_view(), name='user_subscriptions'),
    path('cart/', views.view_cart, name='cart'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
]