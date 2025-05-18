# /myproject/myapp/middleware.py

from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse
from django.utils import timezone
from .models import Subscription

class AuthenticationMiddleware:
    """
    Middleware to handle authentication requirements for specific paths.
    Redirects unauthenticated users to the login page with a message.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
        # Paths that require authentication
        self.auth_required_paths = [
            '/dashboard/',
            '/exercise-plan/',
            '/meal-plan/',
            '/progress/',
            '/orders/',
            '/profile/',
            '/wishlist/',
            '/support/',
            '/nutrition-plan/',
            '/my-subscriptions/',
        ]
        
    def __call__(self, request):
        # Check if the path requires authentication
        path = request.path
        requires_auth = any(path.startswith(auth_path) for auth_path in self.auth_required_paths)
        
        if requires_auth and not request.user.is_authenticated:
            # Store the current path to redirect back after login
            next_url = request.get_full_path()
            
            # Add a message to inform the user why they are being redirected
            messages.info(request, 'กรุณาเข้าสู่ระบบเพื่อเข้าถึงหน้านี้')
            
            # Redirect to login page with next parameter
            return redirect(f"{reverse('login')}?next={next_url}")
        
        # Continue processing the request
        response = self.get_response(request)
        return response

class SubscriptionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # ดำเนินการก่อนที่ view จะประมวลผล
        
        # ข้ามการตรวจสอบสำหรับหน้าที่ไม่ต้องการสถานะสมาชิก
        public_urls = [
            reverse('home'),
            reverse('login'),
            reverse('logout'),
            reverse('register'),
            reverse('product_list'),
            reverse('subscription_list'),
        ]
        
        # ข้ามการตรวจสอบสำหรับการทำงานของ admin
        if request.path.startswith('/admin/'):
            return self.get_response(request)
            
        # ข้ามการตรวจสอบสำหรับ URL ที่ไม่ต้องการสถานะสมาชิก
        if request.path in public_urls or any(request.path.startswith(url) for url in ['/product/', '/static/', '/media/']):
            return self.get_response(request)
        
        # ตรวจสอบว่าผู้ใช้ล็อกอินหรือไม่
        if not request.user.is_authenticated:
            return self.get_response(request)
        
        # ตรวจสอบสถานะสมาชิก
        has_active_subscription = Subscription.objects.filter(
            user=request.user, 
            status='active',
            end_date__gte=timezone.now().date()
        ).exists()
        
        # ถ้าไม่มีสมาชิกที่ใช้งานอยู่และกำลังพยายามเข้าถึงฟีเจอร์ที่จำกัด
        subscription_required_paths = [
            '/exercise-plan/',
            '/meal-plan/',
            '/track-progress/',
            '/nutrition-plan/',
        ]
        
        if not has_active_subscription and any(request.path.startswith(path) for path in subscription_required_paths):
            messages.warning(request, 'คุณต้องเป็นสมาชิกเพื่อใช้ฟีเจอร์นี้ กรุณาสมัครสมาชิกหรืออัพเกรดแพ็คเกจของคุณ')
            return redirect('subscription_list')
        
        response = self.get_response(request)
        return response