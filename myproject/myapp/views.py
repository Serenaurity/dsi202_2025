from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.db.models import Q
from django.utils import timezone
from .models import Product, SubscriptionPlan, Subscription, Order, OrderItem

# Home Page (FBV)
def home(request):
    featured_products = Product.objects.filter(is_active=True).order_by('-created_at')[:4]
    subscription_plans = SubscriptionPlan.objects.filter(is_active=True)
    context = {
        'featured_products': featured_products,
        'subscription_plans': subscription_plans
    }
    return render(request, 'myapp/home.html', context)

# Product List View
class ProductListView(ListView):
    model = Product
    template_name = 'myapp/product_list.html'
    context_object_name = 'products'
    
    def get_queryset(self):
        queryset = super().get_queryset().filter(is_active=True).order_by('-created_at')
        query = self.request.GET.get('q')  # Get the search term from the URL
        if query:
            # Filter products where name or description contains the query (case-insensitive)
            queryset = queryset.filter(
                Q(name__icontains=query) | Q(description__icontains=query)
            )
        return queryset

# Product Detail View
class ProductDetailView(DetailView):
    model = Product
    template_name = 'myapp/product_detail.html'
    context_object_name = 'product'

# Subscription Plan List View
class SubscriptionPlanListView(ListView):
    model = SubscriptionPlan
    template_name = 'myapp/subscription_list.html'
    context_object_name = 'subscription_plans'
    
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)

# Subscription Detail View
class SubscriptionDetailView(DetailView):
    model = SubscriptionPlan
    template_name = 'myapp/subscription_detail.html'
    context_object_name = 'subscription_plan'

# User's Subscription View
class UserSubscriptionListView(LoginRequiredMixin, ListView):
    model = Subscription
    template_name = 'myapp/user_subscription_list.html'
    context_object_name = 'subscriptions'
    
    def get_queryset(self):
        return Subscription.objects.filter(user=self.request.user)

# Add to Cart (FBV)
@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    # Get or create order with 'pending' status (cart)
    order, created = Order.objects.get_or_create(
        user=request.user,
        status='pending'
    )
    
    # If order was just created, set initial total_amount
    if created:
        order.total_amount = 0
        order.save()
    
    # Check if item already in cart, if so increase quantity
    try:
        order_item = OrderItem.objects.get(order=order, product=product)
        order_item.quantity += 1
        order_item.save()
    except OrderItem.DoesNotExist:
        # Create new order item
        order_item = OrderItem.objects.create(
            order=order,
            product=product,
            quantity=1,
            price=product.price
        )
    
    # Update order total
    order.total_amount = sum(item.price * item.quantity for item in order.items.all())
    order.save()
    
    return redirect('cart')

# View Cart (FBV)
@login_required
def view_cart(request):
    try:
        cart = Order.objects.get(user=request.user, status='pending')
        items = cart.items.all()
    except Order.DoesNotExist:
        cart = None
        items = []
    
    context = {
        'cart': cart,
        'items': items
    }
    return render(request, 'myapp/cart.html', context)

# Subscribe to plan (FBV)
@login_required
def subscribe(request, plan_id):
    plan = get_object_or_404(SubscriptionPlan, id=plan_id)
    
    # Check if user already has an active subscription to this plan
    existing_subscription = Subscription.objects.filter(
        user=request.user,
        plan=plan,
        status='active'
    ).first()
    
    if existing_subscription:
        # Redirect to existing subscription
        return redirect('user_subscriptions')
    
    # Create new subscription (payment would be handled here in production)
    subscription = Subscription.objects.create(
        user=request.user,
        plan=plan
    )
    
    return redirect('user_subscriptions')