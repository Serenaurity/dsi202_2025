from django.contrib import messages
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q, Sum
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.generic import ListView, DetailView
from itertools import cycle

from .decorators import subscription_required
from .forms import (
    CustomUserCreationForm, UserProfileForm, ExercisePlanForm,
    MealPlanForm, NutritionPreferencesForm
)
from .models import (
    UserProfile, Product, Order, OrderItem, SubscriptionPlan, Subscription,
    ExercisePlan, WorkoutDay, Exercise, WorkoutExercise,
    MealPlan, DailyMeal, Recipe, Ingredient, MealItem,
    ForumTopic, ForumThread, Article, Video, Content, Progress,
    Wishlist
)
from .utils import distribute_training_days, create_workout_exercises


# ---------- Authentication Views ----------

def login_view(request):
    """Custom login view with better message handling"""
    if request.user.is_authenticated:
        next_url = request.POST.get('next', 'dashboard')
        return redirect(next_url)
    
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            
            if user is not None:
                login(request, user)
                messages.success(request, f'ยินดีต้อนรับกลับมา, {user.username}!')
                
                next_url = request.POST.get('next', '')
                return redirect(next_url) if next_url else redirect('dashboard')
            else:
                messages.error(request, 'ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง')
        else:
            messages.error(request, 'ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง')
    else:
        form = AuthenticationForm()
    
    return render(request, 'myapp/login.html', {'form': form})


def register(request):
    """ฟังก์ชันสำหรับลงทะเบียนผู้ใช้ใหม่"""
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            UserProfile.objects.create(user=user)
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=password)
            login(request, user)
            messages.success(request, 'ลงทะเบียนสำเร็จ! ยินดีต้อนรับสู่ CareME')
            return redirect('profile_setup')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'myapp/register.html', {'form': form})


# ---------- Profile Views ----------

@login_required
def profile_setup(request):
    """หน้าตั้งค่าข้อมูลส่วนตัวสำหรับใช้ในแผน"""
    try:
        profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        profile = UserProfile(user=request.user)
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=profile)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.has_completed_profile = True
            profile.save()
            messages.success(request, 'บันทึกข้อมูลส่วนตัวเรียบร้อยแล้ว')
            
            next_page = request.POST.get('next', 'dashboard')
            return redirect(next_page)
    else:
        form = UserProfileForm(instance=profile)
    
    context = {
        'form': form,
        'next': request.GET.get('next', 'dashboard')
    }
    return render(request, 'myapp/profile_setup.html', context)


@login_required
def profile_update(request):
    """แก้ไขโปรไฟล์ผู้ใช้"""
    user = request.user
    try:
        profile = UserProfile.objects.get(user=user)
    except UserProfile.DoesNotExist:
        profile = UserProfile(user=user)
    
    if request.method == 'POST':
        # อัปเดตข้อมูลผู้ใช้
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.email = request.POST.get('email', '')
        user.save()
        
        # อัปเดตข้อมูลโปรไฟล์
        profile.birth_date = request.POST.get('birth_date')
        profile.gender = request.POST.get('gender')
        profile.height = request.POST.get('height')
        profile.weight = request.POST.get('weight')
        profile.activity_level = request.POST.get('activity_level')
        profile.medical_conditions = request.POST.get('medical_conditions', '')
        profile.has_completed_profile = True
        profile.save()
        
        messages.success(request, 'อัปเดตโปรไฟล์เรียบร้อยแล้ว')
        return redirect('dashboard')
    
    context = {'user_profile': profile}
    return render(request, 'myapp/profile_update.html', context)


# ---------- General Views ----------

def home(request):
    """หน้าหลัก"""
    featured_products = Product.objects.filter(is_active=True).order_by('-created_at')[:4]
    subscription_plans = SubscriptionPlan.objects.filter(is_active=True)
    context = {
        'featured_products': featured_products,
        'subscription_plans': subscription_plans
    }
    return render(request, 'myapp/home.html', context)


@login_required
def user_dashboard(request):
    """หน้าแดชบอร์ดผู้ใช้"""
    user = request.user
    
    # ตรวจสอบว่ามีโปรไฟล์แล้วหรือไม่
    try:
        user_profile = UserProfile.objects.get(user=user)
        profile_complete = user_profile.has_completed_profile
    except UserProfile.DoesNotExist:
        user_profile = UserProfile.objects.create(user=user)
        profile_complete = False
    
    # ถ้ายังไม่ได้กรอกข้อมูลส่วนตัว ให้ไปกรอกก่อน
    if not profile_complete:
        messages.info(request, 'กรุณากรอกข้อมูลส่วนตัวเพื่อปรับแต่งแดชบอร์ดของคุณ')
        return redirect('profile_setup')
    
    # ตรวจสอบการสมัครสมาชิก
    active_subscription = Subscription.objects.filter(
        user=user, 
        status='active', 
        end_date__gte=timezone.now().date()
    ).first()
    
    if active_subscription:
        remaining_days = (active_subscription.end_date - timezone.now().date()).days
        active_subscription.remaining_days = max(0, remaining_days)
    
    # ดึงข้อมูลออเดอร์ล่าสุด
    recent_orders = Order.objects.filter(user=user).order_by('-created_at')[:5]
    
    # ดึงแผนออกกำลังกายและแผนอาหาร
    exercise_plan = ExercisePlan.objects.filter(user=user).order_by('-created_at').first()
    meal_plan = MealPlan.objects.filter(user=user).order_by('-created_at').first()
    
    # ข้อมูลแผนวันนี้
    today_workout = None
    today_meal = None
    
    if exercise_plan:
        today_weekday = timezone.now().weekday() + 1  # +1 เพราะ weekday() เริ่มที่ 0 (จันทร์)
        today_workout = WorkoutDay.objects.filter(
            exercise_plan=exercise_plan,
            day_number=today_weekday
        ).first()
    
    if meal_plan:
        today_weekday = timezone.now().weekday() + 1
        today_meal = DailyMeal.objects.filter(
            meal_plan=meal_plan,
            day_number=today_weekday
        ).first()
    
    # คำนวณ BMI ถ้ามีข้อมูล
    if user_profile and user_profile.weight and user_profile.height:
        height_m = user_profile.height / 100.0  # แปลง cm เป็น m
        bmi = user_profile.weight / (height_m * height_m)
        user_profile.bmi = round(bmi, 1)
    else:
        user_profile.bmi = None
    
    # บทความแนะนำตามเป้าหมาย
    if exercise_plan:
        goal_category_mapping = {
            'weight_loss': 'weight_loss',
            'fat_loss': 'weight_loss',
            'muscle_gain': 'muscle_building',
            'endurance': 'cardio',
            'general_fitness': 'general'
        }
        goal_category = goal_category_mapping.get(exercise_plan.goal, 'general')
        
        recommended_articles = Content.objects.filter(
            category=goal_category,
            is_published=True
        ).order_by('-published_at')[:3]
    else:
        recommended_articles = Content.objects.filter(
            is_published=True
        ).order_by('-published_at')[:3]
    
    # กิจกรรมล่าสุด
    last_activity = None
    if recent_orders.exists():
        last_activity = f"สั่งซื้อรายการ #{recent_orders[0].order_number} เมื่อ {recent_orders[0].created_at.strftime('%d/%m/%Y')}"
    elif exercise_plan:
        last_activity = f"สร้างแผนออกกำลังกายเมื่อ {exercise_plan.created_at.strftime('%d/%m/%Y')}"
    elif meal_plan:
        last_activity = f"สร้างแผนอาหารเมื่อ {meal_plan.created_at.strftime('%d/%m/%Y')}"
    
    context = {
        'user_profile': user_profile,
        'active_subscription': active_subscription,
        'recent_orders': recent_orders,
        'exercise_plan': exercise_plan,
        'today_workout': today_workout,
        'meal_plan': meal_plan,
        'today_meal': today_meal,
        'recommended_articles': recommended_articles,
        'last_activity': last_activity
    }
    
    return render(request, 'myapp/dashboard.html', context)


def content_list(request):
    """หน้าบทความและวิดีโอ"""
    articles = Article.objects.filter(published=True).order_by('-date')
    videos = Video.objects.filter(published=True).order_by('-date')
    category = request.GET.get('category', None)
    
    if category:
        articles = articles.filter(category=category)
        videos = videos.filter(category=category)
    
    context = {
        'articles': articles,
        'videos': videos,
        'category': category,
    }
    return render(request, 'myapp/content_list.html', context)


@login_required
def community_forum(request):
    """หน้าชุมชนและฟอรั่ม"""
    topics = ForumTopic.objects.all().order_by('-last_activity')
    popular_threads = ForumThread.objects.annotate(reply_count=Count('replies')).order_by('-reply_count')[:5]
    
    context = {
        'topics': topics,
        'popular_threads': popular_threads,
    }
    return render(request, 'myapp/community_forum.html', context)


@login_required
def support(request):
    """หน้าติดต่อช่วยเหลือ"""
    if request.method == 'POST':
        # สามารถเพิ่มโค้ดสำหรับบันทึกข้อความติดต่อหรือส่งอีเมลที่นี่
        messages.success(request, 'ส่งข้อความเรียบร้อยแล้ว เราจะติดต่อกลับโดยเร็วที่สุด')
        return redirect('support')
    
    return render(request, 'myapp/support.html')


# ---------- Product & Cart Views ----------

class ProductListView(ListView):
    """แสดงรายการสินค้า"""
    model = Product
    template_name = 'myapp/product_list.html'
    context_object_name = 'products'
    
    def get_queryset(self):
        queryset = super().get_queryset().filter(is_active=True).order_by('-created_at')
        query = self.request.GET.get('q')
        if query:
            queryset = queryset.filter(
                Q(name__icontains=query) | Q(description__icontains=query)
            )
        return queryset


def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    breadcrumbs = [
        {'name': 'หน้าแรก', 'url': 'home'},
        {'name': 'สินค้า', 'url': 'product_list'},
        {'name': product.name, 'url': None},
    ]
    
    context = {
        'product': product,
        'breadcrumbs': breadcrumbs,
    }
    return render(request, 'myapp/product_detail.html', context)


@login_required
def add_to_cart(request, product_id):
    """เพิ่มสินค้าลงตะกร้า"""
    product = get_object_or_404(Product, id=product_id)
    
    # หรือสร้างรายการสั่งซื้อที่มีสถานะ 'pending' (ตะกร้า)
    order, created = Order.objects.get_or_create(
        user=request.user,
        status='pending'
    )
    
    # ถ้าสร้างรายการใหม่ ตั้งค่ายอดรวมเริ่มต้นเป็น 0
    if created:
        order.total_amount = 0
        order.save()
    
    # ตรวจสอบว่ามีสินค้านี้ในตะกร้าแล้วหรือไม่
    try:
        order_item = OrderItem.objects.get(order=order, product=product)
        order_item.quantity += 1
        order_item.save()
    except OrderItem.DoesNotExist:
        # สร้างรายการใหม่
        order_item = OrderItem.objects.create(
            order=order,
            product=product,
            quantity=1,
            price=product.price
        )
    
    # อัปเดตยอดรวม
    order.total_amount = sum(item.price * item.quantity for item in order.items.all())
    order.save()
    
    return redirect('cart')


@login_required
def view_cart(request):
    """ดูตะกร้าสินค้า"""
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


@login_required
def remove_from_cart(request, item_id):
    """ลบสินค้าออกจากตะกร้า"""
    order_item = get_object_or_404(OrderItem, id=item_id, order__user=request.user, order__status='pending')
    order = order_item.order
    
    # ลบรายการออกจากตะกร้า
    order_item.delete()
    
    # อัปเดตยอดรวม
    order.total_amount = sum(item.price * item.quantity for item in order.items.all())
    order.save()
    
    messages.success(request, 'ลบสินค้าออกจากตะกร้าเรียบร้อยแล้ว')
    return redirect('cart')


@login_required
def update_cart_item(request, item_id):
    """อัปเดตจำนวนสินค้าในตะกร้า"""
    order_item = get_object_or_404(OrderItem, id=item_id, order__user=request.user, order__status='pending')
    action = request.POST.get('action')
    
    if action == 'increase':
        order_item.quantity += 1
    elif action == 'decrease':
        if order_item.quantity > 1:
            order_item.quantity -= 1
        else:
            # ถ้าจำนวนเหลือ 1 และกดลด ให้ลบรายการออก
            return redirect('remove_from_cart', item_id=item_id)
    
    order_item.save()
    
    # อัปเดตยอดรวม
    order = order_item.order
    order.total_amount = sum(item.price * item.quantity for item in order.items.all())
    order.save()
    
    return redirect('cart')


@login_required
def checkout(request):
    """ดำเนินการสั่งซื้อ"""
    try:
        cart = Order.objects.get(user=request.user, status='pending')
    except Order.DoesNotExist:
        messages.error(request, 'ไม่พบตะกร้าสินค้าของคุณ')
        return redirect('product_list')
    
    if request.method == 'POST':
        # จำลองการชำระเงินสำเร็จ
        cart.status = 'paid'
        cart.save()
        
        messages.success(request, 'สั่งซื้อสินค้าสำเร็จ! ขอบคุณที่ใช้บริการ')
        return redirect('order_detail', order_id=cart.id)
    
    context = {
        'cart': cart,
        'items': cart.items.all()
    }
    return render(request, 'myapp/checkout.html', context)


@login_required
def order_history(request):
    """แสดงประวัติการสั่งซื้อ"""
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'myapp/order_history.html', {'orders': orders})


@login_required
def order_detail(request, order_id):
    """แสดงรายละเอียดคำสั่งซื้อ"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'myapp/order_detail.html', {'order': order})


@login_required
def wishlist(request):
    """แสดงรายการโปรด"""
    wishlist_items = Wishlist.objects.filter(user=request.user)
    return render(request, 'myapp/wishlist.html', {'wishlist_items': wishlist_items})


@login_required
def remove_from_wishlist(request, item_id):
    """ลบสินค้าออกจากรายการโปรด"""
    wishlist_item = get_object_or_404(Wishlist, id=item_id, user=request.user)
    wishlist_item.delete()
    messages.success(request, 'ลบสินค้าออกจากรายการโปรดเรียบร้อยแล้ว')
    return redirect('wishlist')


# ---------- Subscription Views ----------

class SubscriptionPlanListView(ListView):
    """แสดงรายการแพ็คเกจสมาชิก"""
    model = SubscriptionPlan
    template_name = 'myapp/subscription_list.html'
    context_object_name = 'subscription_plans'
    
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)


class SubscriptionDetailView(DetailView):
    """แสดงรายละเอียดแพ็คเกจสมาชิก"""
    model = SubscriptionPlan
    template_name = 'myapp/subscription_detail.html'
    context_object_name = 'subscription_plan'


class UserSubscriptionListView(LoginRequiredMixin, ListView):
    """แสดงแพ็คเกจสมาชิกของผู้ใช้"""
    model = Subscription
    template_name = 'myapp/user_subscription_list.html'
    context_object_name = 'subscriptions'
    
    def get_queryset(self):
        return Subscription.objects.filter(user=self.request.user)


@login_required
def subscribe(request, plan_id):
    """สมัครหรือต่ออายุสมาชิก"""
    plan = get_object_or_404(SubscriptionPlan, id=plan_id)
    
    # ตรวจสอบว่ามีสมาชิกที่ใช้งานอยู่หรือไม่
    active_subscription = Subscription.objects.filter(
        user=request.user,
        status='active',
        end_date__gte=timezone.now().date()
    ).first()
    
    # กำหนดระยะเวลาสมาชิกตาม plan.duration
    duration_days = {
        'monthly': 30,
        'quarterly': 90,
        'yearly': 365
    }.get(plan.duration, 30)
    
    if active_subscription:
        # ต่ออายุสมาชิก
        new_end_date = active_subscription.end_date + timezone.timedelta(days=duration_days)
        active_subscription.end_date = new_end_date
        active_subscription.plan = plan
        active_subscription.save()
        
        messages.success(request, f'ต่ออายุสมาชิก {plan.name} สำเร็จ! สมาชิกของคุณจะมีอายุถึงวันที่ {new_end_date.strftime("%d/%m/%Y")}')
    else:
        # สร้างสมาชิกใหม่
        start_date = timezone.now().date()
        end_date = start_date + timezone.timedelta(days=duration_days)
        
        Subscription.objects.create(
            user=request.user,
            plan=plan,
            start_date=start_date,
            end_date=end_date,
            status='active'
        )
        
        messages.success(request, f'สมัครสมาชิก {plan.name} สำเร็จ! สมาชิกของคุณจะมีอายุถึงวันที่ {end_date.strftime("%d/%m/%Y")}')
    
    return redirect('dashboard')


# ---------- Exercise Plan Views ----------

@login_required
@subscription_required
def exercise_plan(request):
    """หน้าจัดการแผนออกกำลังกาย"""
    # ตรวจสอบว่าผู้ใช้มีการสมัครสมาชิกที่ใช้งานอยู่
    active_subscription = Subscription.objects.filter(user=request.user, status='active').first()
    if not active_subscription:
        return redirect('subscription_list')
    
    # ตรวจสอบโปรไฟล์ผู้ใช้
    try:
        profile = UserProfile.objects.get(user=request.user)
        if not profile.has_completed_profile:
            messages.warning(request, 'โปรดกรอกข้อมูลส่วนตัวก่อนเพื่อสร้างแผนออกกำลังกาย')
            return redirect('profile_setup')
    except UserProfile.DoesNotExist:
        messages.warning(request, 'โปรดกรอกข้อมูลส่วนตัวก่อนเพื่อสร้างแผนออกกำลังกาย')
        return redirect('profile_setup')
    
    # ดึงแผนออกกำลังกายล่าสุด
    exercise_plan = ExercisePlan.objects.filter(user=request.user).order_by('-created_at').first()
    
    if request.method == 'POST':
        form = ExercisePlanForm(request.POST, instance=exercise_plan)
        if form.is_valid():
            plan = form.save(commit=False)
            plan.user = request.user
            plan.save()
            
            # สร้างแผนรายวัน
            generate_workout_plan(plan)
            
            messages.success(request, 'สร้างแผนออกกำลังกายเรียบร้อยแล้ว')
            return redirect('view_exercise_plan')
    else:
        form = ExercisePlanForm(instance=exercise_plan)
    
    context = {
        'form': form,
        'exercise_plan': exercise_plan
    }
    return render(request, 'myapp/exercise_plan_setup.html', context)


@login_required
@subscription_required
def view_exercise_plan(request):
    """หน้าดูแผนออกกำลังกาย"""
    active_subscription = Subscription.objects.filter(user=request.user, status='active').first()
    if not active_subscription:
        return redirect('subscription_list')
    
    exercise_plan = ExercisePlan.objects.filter(user=request.user).order_by('-created_at').first()
    
    if not exercise_plan:
        messages.info(request, 'คุณยังไม่มีแผนออกกำลังกาย กรุณาสร้างแผนใหม่')
        return redirect('exercise_plan')
    
    # ดึงข้อมูลแผนรายวัน
    workout_days = WorkoutDay.objects.filter(exercise_plan=exercise_plan).prefetch_related('exercises__exercise')
    
    # สร้างข้อมูลปฏิทินสำหรับแสดงผล
    today = timezone.now().date()
    start_date = exercise_plan.start_date
    
    calendar_days = []
    for i in range(28):
        day_date = start_date + timezone.timedelta(days=i)
        day_number = i % 7 + 1  # วันที่ 1-7 ในแต่ละสัปดาห์
        
        # หาแผนออกกำลังกายสำหรับวันนี้
        workout_day = next((day for day in workout_days if day.day_number == day_number), None)
        
        calendar_days.append({
            'date': day_date,
            'is_today': day_date == today,
            'is_past': day_date < today,
            'workout_day': workout_day,
            'week_number': i // 7 + 1
        })
    
    context = {
        'exercise_plan': exercise_plan,
        'workout_days': workout_days,
        'calendar_days': calendar_days
    }
    return render(request, 'myapp/view_exercise_plan.html', context)


@login_required
def view_workout_day(request, day_id):
    """หน้าดูรายละเอียดการออกกำลังกายรายวัน"""
    workout_day = get_object_or_404(WorkoutDay, id=day_id)
    
    # ตรวจสอบสิทธิ์การเข้าถึง
    if workout_day.exercise_plan.user != request.user:
        messages.error(request, 'คุณไม่มีสิทธิ์เข้าถึงแผนนี้')
        return redirect('dashboard')
    
    # ดึงรายการออกกำลังกาย
    workout_exercises = WorkoutExercise.objects.filter(workout_day=workout_day).select_related('exercise')
    
    context = {
        'workout_day': workout_day,
        'workout_exercises': workout_exercises
    }
    return render(request, 'myapp/view_workout_day.html', context)


# ---------- Meal Plan Views ----------

@login_required
@subscription_required
def meal_plan(request):
   """หน้าจัดการแผนอาหาร"""
   active_subscription = Subscription.objects.filter(user=request.user, status='active').first()
   if not active_subscription:
       return redirect('subscription_list')
   
   # ตรวจสอบโปรไฟล์
   try:
       profile = UserProfile.objects.get(user=request.user)
       if not profile.has_completed_profile:
           messages.warning(request, 'โปรดกรอกข้อมูลส่วนตัวก่อนเพื่อสร้างแผนอาหาร')
           return redirect('profile_setup')
   except UserProfile.DoesNotExist:
       messages.warning(request, 'โปรดกรอกข้อมูลส่วนตัวก่อนเพื่อสร้างแผนอาหาร')
       return redirect('profile_setup')
   
   # ดึงแผนอาหารล่าสุด
   meal_plan = MealPlan.objects.filter(user=request.user).order_by('-created_at').first()
   
   # คำนวณ TDEE
   tdee = profile.calculate_tdee()
   
   if request.method == 'POST':
       form = MealPlanForm(request.POST, instance=meal_plan)
       if form.is_valid():
           plan = form.save(commit=False)
           plan.user = request.user
           plan.save()
           
           # สร้างแผนอาหารรายวัน
           generate_meal_plan(plan)
           
           messages.success(request, 'สร้างแผนอาหารเรียบร้อยแล้ว')
           return redirect('view_meal_plan')
   else:
       # ถ้าไม่มีแผนอาหารเดิม ใช้ค่า TDEE เป็นค่าเริ่มต้น
       initial_data = {}
       if not meal_plan and tdee:
           goal = request.GET.get('goal', 'general_health')
           
           # ปรับค่าแคลอรี่ตามเป้าหมาย
           calorie_adjustments = {
               'weight_loss': max(1200, int(tdee * 0.8)),  # ลด 20%
               'muscle_gain': int(tdee * 1.1),  # เพิ่ม 10%
               'maintenance': tdee,
               'general_health': tdee
           }
           calories = calorie_adjustments.get(goal, tdee)
               
           initial_data = {
               'goal': goal,
               'daily_calories': calories
           }
           
       form = MealPlanForm(instance=meal_plan, initial=initial_data)
   
   context = {
       'form': form,
       'meal_plan': meal_plan,
       'tdee': tdee
   }
   return render(request, 'myapp/meal_plan_setup.html', context)


@login_required
@subscription_required
def view_meal_plan(request):
   """หน้าดูแผนอาหาร"""
   active_subscription = Subscription.objects.filter(user=request.user, status='active').first()
   if not active_subscription:
       return redirect('subscription_list')
   
   meal_plan = MealPlan.objects.filter(user=request.user).order_by('-created_at').first()
   
   if not meal_plan:
       messages.info(request, 'คุณยังไม่มีแผนอาหาร กรุณาสร้างแผนใหม่')
       return redirect('meal_plan')
   
   # ดึงแผนอาหารรายวัน
   daily_meals = DailyMeal.objects.filter(meal_plan=meal_plan).prefetch_related('meal_items__recipe')
   
   # คำนวณสารอาหารหลัก
   macros = meal_plan.calculate_macros()
   
   # สร้างปฏิทินสำหรับแสดงผล
   today = timezone.now().date()
   start_date = meal_plan.start_date
   
   calendar_days = []
   for i in range(28):
       day_date = start_date + timezone.timedelta(days=i)
       day_number = i % 7 + 1  # วันที่ 1-7 ในแต่ละสัปดาห์
       
       # หาแผนอาหารสำหรับวันนี้
       daily_meal = next((meal for meal in daily_meals if meal.day_number == day_number), None)
       
       calendar_days.append({
           'date': day_date,
           'is_today': day_date == today,
           'is_past': day_date < today,
           'daily_meal': daily_meal,
           'week_number': i // 7 + 1
       })
   
   context = {
       'meal_plan': meal_plan,
       'daily_meals': daily_meals,
       'calendar_days': calendar_days,
       'macros': macros
   }
   return render(request, 'myapp/view_meal_plan.html', context)


@login_required
def view_daily_meal(request, meal_id):
   """หน้าดูรายละเอียดอาหารรายวัน"""
   daily_meal = get_object_or_404(DailyMeal, id=meal_id)
   
   # ตรวจสอบสิทธิ์การเข้าถึง
   if daily_meal.meal_plan.user != request.user:
       messages.error(request, 'คุณไม่มีสิทธิ์เข้าถึงแผนนี้')
       return redirect('dashboard')
   
   # ดึงรายการอาหาร
   meal_items = MealItem.objects.filter(daily_meal=daily_meal).select_related('recipe')
   
   # จัดกลุ่มตามมื้ออาหาร
   meals_by_time = {}
   for item in meal_items:
       if item.meal_time not in meals_by_time:
           meals_by_time[item.meal_time] = []
       meals_by_time[item.meal_time].append(item)
   
   # คำนวณค่าโภชนาการรวม
   total_calories = 0
   total_protein = 0
   total_carbs = 0
   total_fat = 0
   
   for item in meal_items:
       total_calories += item.recipe.calories_per_serving
       total_protein += item.recipe.protein
       total_carbs += item.recipe.carbs
       total_fat += item.recipe.fat
   
   # ปัดเศษทศนิยม
   total_protein = round(total_protein, 1)
   total_carbs = round(total_carbs, 1)
   total_fat = round(total_fat, 1)
   
   context = {
       'daily_meal': daily_meal,
       'meals_by_time': meals_by_time,
       'total_calories': total_calories,
       'total_protein': total_protein,
       'total_carbs': total_carbs,
       'total_fat': total_fat
   }
   return render(request, 'myapp/view_daily_meal.html', context)


@login_required
def view_recipe(request, recipe_id):
   """หน้าดูรายละเอียดสูตรอาหาร"""
   recipe = get_object_or_404(Recipe, id=recipe_id)
   ingredients = Ingredient.objects.filter(recipe=recipe)
   
   context = {
       'recipe': recipe,
       'ingredients': ingredients
   }
   return render(request, 'myapp/view_recipe.html', context)


@login_required
def nutrition_plan(request):
   """หน้าแผนโภชนาการ"""
   subscription = Subscription.objects.filter(user=request.user, status='active').first()
   
   if not subscription:
       return redirect('subscription_list')
   
   # รับหรือสร้างแผนโภชนาการเฉพาะบุคคล
   nutrition_plan, created = NutritionPlan.objects.get_or_create(user=request.user)
   
   if request.method == 'POST':
       form = NutritionPreferencesForm(request.POST, instance=nutrition_plan)
       if form.is_valid():
           form.save()
           messages.success(request, 'บันทึกข้อมูลโภชนาการเรียบร้อยแล้ว')
   else:
       form = NutritionPreferencesForm(instance=nutrition_plan)
   
   context = {
       'nutrition_plan': nutrition_plan,
       'form': form,
   }
   return render(request, 'myapp/nutrition_plan.html', context)


# ---------- Progress Tracking Views ----------

@login_required
def track_progress(request):
   """หน้าติดตามความก้าวหน้า"""
   progress_entries = Progress.objects.filter(user=request.user).order_by('-date')
   
   context = {
       'progress_entries': progress_entries
   }
   return render(request, 'myapp/track_progress.html', context)


@login_required
def add_progress(request):
   """เพิ่มข้อมูลความก้าวหน้า"""
   if request.method == 'POST':
       weight = request.POST.get('weight')
       exercise_minutes = request.POST.get('exercise_minutes')
       notes = request.POST.get('notes')
       
       Progress.objects.create(
           user=request.user,
           date=timezone.now().date(),
           weight=weight,
           exercise_minutes=exercise_minutes,
           notes=notes
       )
       
       messages.success(request, 'บันทึกความก้าวหน้าเรียบร้อยแล้ว')
       return redirect('track_progress')
   
   return render(request, 'myapp/add_progress.html')


# ---------- Helper Functions ----------

def generate_workout_plan(exercise_plan):
   """สร้างแผนออกกำลังกายรายวันตามเป้าหมายและระดับความสามารถ"""
   # ลบแผนเดิมหากมี
   WorkoutDay.objects.filter(exercise_plan=exercise_plan).delete()
   
   # กำหนดวันออกกำลังกายตามจำนวนวันต่อสัปดาห์
   days_per_week = exercise_plan.days_per_week
   
   # สร้างแผนออกกำลังกายตามรูปแบบการฝึก
   if exercise_plan.training_focus == 'full_body':
       # แผนฝึกทั้งร่างกาย - กระจายวันฝึกให้ห่างกัน
       training_days = distribute_training_days(days_per_week)
       for day in range(1, 8):
           if day in training_days:
               workout_day = WorkoutDay.objects.create(
                   exercise_plan=exercise_plan,
                   day_number=day,
                   focus='full_body'
               )
               create_workout_exercises(workout_day, exercise_plan)
           else:
               WorkoutDay.objects.create(
                   exercise_plan=exercise_plan,
                   day_number=day,
                   focus='rest'
               )
   
   elif exercise_plan.training_focus == 'upper_lower':
       # แผนฝึกส่วนบน/ส่วนล่าง - สลับวันฝึก
       training_days = distribute_training_days(days_per_week)
       upper_lower_cycle = cycle(['upper_body', 'lower_body'])
       
       for day in range(1, 8):
           if day in training_days:
               focus = next(upper_lower_cycle)
               workout_day = WorkoutDay.objects.create(
                   exercise_plan=exercise_plan,
                   day_number=day,
                   focus=focus
               )
               create_workout_exercises(workout_day, exercise_plan)
           else:
               WorkoutDay.objects.create(
                   exercise_plan=exercise_plan,
                   day_number=day,
                   focus='rest'
               )
               
   elif exercise_plan.training_focus == 'push_pull_legs':
       # แผนฝึกแบบ Push/Pull/Legs
       training_days = distribute_training_days(min(6, days_per_week))  # สูงสุด 6 วัน
       ppl_cycle = cycle(['chest', 'back', 'legs'])  # Push, Pull, Legs
       
       for day in range(1, 8):
           if day in training_days:
               muscle_focus = next(ppl_cycle)
               # กำหนด focus สำหรับการแสดงผล
               if muscle_focus == 'chest':
                   display_focus = 'upper_body'  # Push
               elif muscle_focus == 'back':
                   display_focus = 'upper_body'  # Pull
               else:
                   display_focus = 'lower_body'  # Legs
               
               workout_day = WorkoutDay.objects.create(
                   exercise_plan=exercise_plan,
                   day_number=day,
                   focus=display_focus
               )
               create_workout_exercises(workout_day, exercise_plan, primary_muscle=muscle_focus)
           else:
               WorkoutDay.objects.create(
                   exercise_plan=exercise_plan,
                   day_number=day,
                   focus='rest'
               )


def generate_meal_plan(meal_plan):
   """สร้างแผนอาหารรายวันตามเป้าหมายและความต้องการทางโภชนาการ"""
   # ลบแผนเดิมหากมี
   DailyMeal.objects.filter(meal_plan=meal_plan).delete()
   
   # กำหนดประเภทอาหาร
   diet_type = 'any'  # ค่าเริ่มต้น
   if meal_plan.dietary_restrictions:
       if 'vegetarian' in meal_plan.dietary_restrictions.lower():
           diet_type = 'vegetarian'
       elif 'vegan' in meal_plan.dietary_restrictions.lower():
           diet_type = 'vegan'
   
   # กำหนดเงื่อนไขการค้นหาสูตรอาหารตามเป้าหมาย
   meal_conditions = {
       'weight_loss': {
           'breakfast': {'meal_type': 'breakfast', 'diet_type__in': [diet_type, 'any'], 'calories_per_serving__lt': 400},
           'lunch': {'meal_type': 'lunch', 'diet_type__in': [diet_type, 'any'], 'calories_per_serving__lt': 500},
           'dinner': {'meal_type': 'dinner', 'diet_type__in': [diet_type, 'any'], 'calories_per_serving__lt': 500},
           'snack': {'meal_type': 'snack', 'diet_type__in': [diet_type, 'any'], 'calories_per_serving__lt': 200}
       },
       'muscle_gain': {
           'breakfast': {'meal_type': 'breakfast', 'diet_type__in': [diet_type, 'any'], 'protein__gt': 20},
           'lunch': {'meal_type': 'lunch', 'diet_type__in': [diet_type, 'any'], 'protein__gt': 30},
           'dinner': {'meal_type': 'dinner', 'diet_type__in': [diet_type, 'any'], 'protein__gt': 30},
           'snack': {'meal_type': 'snack', 'diet_type__in': [diet_type, 'any'], 'protein__gt': 10}
       }
   }
   
   # ใช้เงื่อนไขตามเป้าหมาย หรือเงื่อนไขทั่วไปถ้าไม่มีเงื่อนไขเฉพาะ
   conditions = meal_conditions.get(meal_plan.goal, {
       'breakfast': {'meal_type': 'breakfast', 'diet_type__in': [diet_type, 'any']},
       'lunch': {'meal_type': 'lunch', 'diet_type__in': [diet_type, 'any']},
       'dinner': {'meal_type': 'dinner', 'diet_type__in': [diet_type, 'any']},
       'snack': {'meal_type': 'snack', 'diet_type__in': [diet_type, 'any']}
   })
   
   # ดึงสูตรอาหารตามเงื่อนไข
   breakfast_recipes = Recipe.objects.filter(**conditions['breakfast']).order_by('?')
   lunch_recipes = Recipe.objects.filter(**conditions['lunch']).order_by('?')
   dinner_recipes = Recipe.objects.filter(**conditions['dinner']).order_by('?')
   snack_recipes = Recipe.objects.filter(**conditions['snack']).order_by('?')
   
   # ถ้าไม่พบสูตรอาหารตามเงื่อนไข ใช้เงื่อนไขทั่วไป
   if not breakfast_recipes.exists():
       breakfast_recipes = Recipe.objects.filter(meal_type='breakfast').order_by('?')
   if not lunch_recipes.exists():
       lunch_recipes = Recipe.objects.filter(meal_type='lunch').order_by('?')
   if not dinner_recipes.exists():
       dinner_recipes = Recipe.objects.filter(meal_type='dinner').order_by('?')
   if not snack_recipes.exists():
       snack_recipes = Recipe.objects.filter(meal_type='snack').order_by('?')
   
   # สร้างแผนอาหาร 7 วัน
   for day in range(1, 8):
       daily_meal = DailyMeal.objects.create(
           meal_plan=meal_plan,
           day_number=day
       )
       
       # เพิ่มมื้ออาหาร
       meals_to_add = [
           {'type': 'breakfast', 'recipes': breakfast_recipes, 'meal_time': 'breakfast'},
           {'type': 'lunch', 'recipes': lunch_recipes, 'meal_time': 'lunch'},
           {'type': 'dinner', 'recipes': dinner_recipes, 'meal_time': 'dinner'}
       ]
       
       # เพิ่มอาหารว่างถ้ามีมากกว่า 3 มื้อ
       if meal_plan.meals_per_day > 3 and snack_recipes.exists():
           meals_to_add.append({'type': 'snack', 'recipes': snack_recipes, 'meal_time': 'snack'})
       
       # สร้างรายการอาหารแต่ละมื้อ
       for meal_info in meals_to_add:
           recipes = meal_info['recipes']
           if recipes.exists():
               recipe = recipes[day % recipes.count()]
               MealItem.objects.create(
                   daily_meal=daily_meal,
                   recipe=recipe,
                   meal_time=meal_info['meal_time']
               )