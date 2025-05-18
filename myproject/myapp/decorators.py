# myapp/decorators.py
from django.shortcuts import redirect
from django.contrib import messages
from django.utils import timezone
from functools import wraps
from .models import Subscription , FeatureUsage

# myapp/decorators.py
def subscription_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # ตรวจสอบว่าผู้ใช้มีสมาชิกที่ใช้งานอยู่หรือไม่
        active_subscription = Subscription.objects.filter(
            user=request.user, 
            status='active',
            end_date__gte=timezone.now().date()
        ).first()
        
        if not active_subscription:
            messages.warning(request, 'คุณต้องเป็นสมาชิกเพื่อใช้ฟีเจอร์นี้ กรุณาสมัครสมาชิกหรืออัพเกรดแพ็คเกจของคุณ')
            return redirect('subscription_list')
        
        # บันทึกการใช้งานฟีเจอร์
        feature_name = view_func.__name__
        if feature_name in ['exercise_plan', 'meal_plan', 'view_exercise_plan', 'view_meal_plan']:
            if 'exercise' in feature_name:
                feature = 'exercise_plan'
            elif 'meal' in feature_name:
                feature = 'meal_plan'
            
            FeatureUsage.objects.create(
                user=request.user,
                subscription=active_subscription,
                feature=feature
            )
        
        return view_func(request, *args, **kwargs)
    
    return _wrapped_view