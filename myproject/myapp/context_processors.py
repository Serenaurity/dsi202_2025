# /myproject/myapp/context_processors.py
from django.db import models
from .models import Order, OrderItem

def cart_items_count(request):
    """
    Context processor to add cart_items_count to all templates
    """
    count = 0
    if request.user.is_authenticated:
        try:
            # Get the current cart (pending order)
            cart = Order.objects.get(user=request.user, status='pending')
            # Get total quantity of items in cart
            count = OrderItem.objects.filter(order=cart).aggregate(total=models.Sum('quantity'))['total'] or 0
        except Order.DoesNotExist:
            # No cart exists
            pass
    
    return {'cart_items_count': count}