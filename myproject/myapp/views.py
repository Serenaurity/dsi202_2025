from django.contrib import messages
from django.db.models import Count
from .models import (
    UserProfile, ExercisePlan, WorkoutDay, MealPlan, DailyMeal, 
    Exercise, WorkoutExercise, Recipe, Ingredient, MealItem,
    ForumTopic, ForumThread, Article, Video, Content,
    Product, Order, OrderItem, SubscriptionPlan, Subscription
)
from .forms import UserProfileForm, ExercisePlanForm, MealPlanForm, NutritionPreferencesForm
from .forms import CustomUserCreationForm
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login, authenticate
from django.shortcuts import render, redirect
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView
from django.db.models import Q, Sum
from django.utils import timezone
from itertools import cycle
from allauth.socialaccount.models import SocialAccount
from .decorators import subscription_required
# In views.py, update the register function:
# In views.py, update the login view (or create one if using Django's default view)

from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import AuthenticationForm

def login_view(request):
    """Custom login view with better message handling"""
    
    # If user is already authenticated, redirect to dashboard
    if request.user.is_authenticated:
        # Redirect to 'next' parameter if available, otherwise to dashboard
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
                
                # Redirect to 'next' parameter if available, otherwise to dashboard
                next_url = request.POST.get('next', '')
                if next_url:
                    return redirect(next_url)
                else:
                    return redirect('dashboard')
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
            # สร้าง UserProfile สำหรับผู้ใช้ใหม่
            UserProfile.objects.create(user=user)
            # ล็อกอินผู้ใช้หลังลงทะเบียน
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=password)
            login(request, user)
            messages.success(request, 'ลงทะเบียนสำเร็จ! ยินดีต้อนรับสู่ CareME')
            
            # Redirect to profile setup first to get user information
            return redirect('profile_setup')
    else:
        form = CustomUserCreationForm()
    
    context = {
        'form': form
    }
    return render(request, 'myapp/register.html', context)

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

@login_required
def subscribe(request, plan_id):
    """สมัครหรือต่ออายุสมาชิก"""
    plan = get_object_or_404(SubscriptionPlan, id=plan_id)
    
    # ตรวจสอบว่าผู้ใช้มีสมาชิกที่ใช้งานอยู่หรือไม่
    active_subscription = Subscription.objects.filter(
        user=request.user,
        status='active',
        end_date__gte=timezone.now().date()
    ).first()
    
    if active_subscription:
        # ต่ออายุสมาชิก
        # คำนวณวันที่สิ้นสุดใหม่
        if plan.duration == 'monthly':
            new_end_date = active_subscription.end_date + timezone.timedelta(days=30)
        elif plan.duration == 'quarterly':
            new_end_date = active_subscription.end_date + timezone.timedelta(days=90)
        elif plan.duration == 'yearly':
            new_end_date = active_subscription.end_date + timezone.timedelta(days=365)
        
        active_subscription.end_date = new_end_date
        active_subscription.plan = plan
        active_subscription.save()
        
        messages.success(request, f'ต่ออายุสมาชิก {plan.name} สำเร็จ! สมาชิกของคุณจะมีอายุถึงวันที่ {new_end_date.strftime("%d/%m/%Y")}')
    else:
        # สร้างสมาชิกใหม่
        # กำหนดวันที่สิ้นสุด
        start_date = timezone.now().date()
        if plan.duration == 'monthly':
            end_date = start_date + timezone.timedelta(days=30)
        elif plan.duration == 'quarterly':
            end_date = start_date + timezone.timedelta(days=90)
        elif plan.duration == 'yearly':
            end_date = start_date + timezone.timedelta(days=365)
        
        subscription = Subscription.objects.create(
            user=request.user,
            plan=plan,
            start_date=start_date,
            end_date=end_date,
            status='active'
        )
        
        messages.success(request, f'สมัครสมาชิก {plan.name} สำเร็จ! สมาชิกของคุณจะมีอายุถึงวันที่ {end_date.strftime("%d/%m/%Y")}')
    
    return redirect('dashboard')

# views.py - เพิ่มฟังก์ชันวิว

# views.py
# In views.py, update the user_dashboard function:

@login_required
def user_dashboard(request):
    """หน้าแดชบอร์ดผู้ใช้"""
    user = request.user
    
    # Check if user profile is complete
    try:
        user_profile = UserProfile.objects.get(user=user)
        profile_complete = user_profile.has_completed_profile
    except UserProfile.DoesNotExist:
        # Create profile if it doesn't exist
        user_profile = UserProfile.objects.create(user=user)
        profile_complete = False
    
    # If profile is not complete, redirect to profile setup with message
    if not profile_complete:
        messages.info(request, 'กรุณากรอกข้อมูลส่วนตัวเพื่อปรับแต่งแดชบอร์ดของคุณ')
        return redirect('profile_setup')
    
    # Check if user has an active subscription
    active_subscription = Subscription.objects.filter(
        user=user, 
        status='active', 
        end_date__gte=timezone.now().date()
    ).first()
    
    if active_subscription:
        # Calculate remaining days
        remaining_days = (active_subscription.end_date - timezone.now().date()).days
        active_subscription.remaining_days = max(0, remaining_days)
    
    # Get recent orders
    recent_orders = Order.objects.filter(user=user).order_by('-created_at')[:5]
    
    # Get exercise and meal plans
    exercise_plan = ExercisePlan.objects.filter(user=user).order_by('-created_at').first()
    meal_plan = MealPlan.objects.filter(user=user).order_by('-created_at').first()
    
    # Today's workout and meal
    today_workout = None
    today_meal = None
    
    if exercise_plan:
        # Get today's weekday (1-7)
        today_weekday = timezone.now().weekday() + 1  # +1 because weekday() starts at 0 (Monday)
        today_workout = WorkoutDay.objects.filter(
            exercise_plan=exercise_plan,
            day_number=today_weekday
        ).first()
    
    if meal_plan:
        # Get today's weekday (1-7)
        today_weekday = timezone.now().weekday() + 1
        today_meal = DailyMeal.objects.filter(
            meal_plan=meal_plan,
            day_number=today_weekday
        ).first()
    
    # Calculate BMI if height and weight are available
    if user_profile and user_profile.weight and user_profile.height:
        height_m = user_profile.height / 100.0  # Convert cm to m
        bmi = user_profile.weight / (height_m * height_m)
        user_profile.bmi = round(bmi, 1)
    else:
        user_profile.bmi = None
    
    # Get recommended articles based on exercise goal
    if exercise_plan:
        goal_category = {
            'weight_loss': 'weight_loss',
            'fat_loss': 'weight_loss',
            'muscle_gain': 'muscle_building',
            'endurance': 'cardio',
            'general_fitness': 'general'
        }.get(exercise_plan.goal, 'general')
        
        recommended_articles = Content.objects.filter(
            category=goal_category,
            is_published=True
        ).order_by('-published_at')[:3]
    else:
        # General articles if no exercise plan
        recommended_articles = Content.objects.filter(
            is_published=True
        ).order_by('-published_at')[:3]
    
    # Get last activity
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

# หน้าบทความและวิดีโอ
def content_list(request):
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

# หน้าแผนโภชนาการ
@login_required
def nutrition_plan(request):
    user = request.user
    subscription = Subscription.objects.filter(user=user, status='active').first()
    
    if not subscription:
        return redirect('subscription_list')
    
    # รับหรือสร้างแผนโภชนาการเฉพาะบุคคล
    nutrition_plan, created = NutritionPlan.objects.get_or_create(user=user)
    
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

# หน้าชุมชนและฟอรั่ม
@login_required
def community_forum(request):
    topics = ForumTopic.objects.all().order_by('-last_activity')
    popular_threads = ForumThread.objects.annotate(reply_count=Count('replies')).order_by('-reply_count')[:5]
    
    context = {
        'topics': topics,
        'popular_threads': popular_threads,
    }
    return render(request, 'myapp/community_forum.html', context)

# views.py - เพิ่มฟังก์ชันวิวสำหรับแผนออกกำลังกายและโภชนาการ

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
            
            # Redirect to next page or dashboard
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
@subscription_required
def exercise_plan(request):
    """หน้าจัดการแผนออกกำลังกาย"""
    # ตรวจสอบว่าผู้ใช้มีการสมัครสมาชิกที่ใช้งานอยู่
    active_subscription = Subscription.objects.filter(user=request.user, status='active').first()
    if not active_subscription:
        return redirect('subscription_list')
    
    # ตรวจสอบว่าผู้ใช้ได้กรอกข้อมูลส่วนตัวแล้วหรือไม่
    try:
        profile = UserProfile.objects.get(user=request.user)
        if not profile.has_completed_profile:
            messages.warning(request, 'โปรดกรอกข้อมูลส่วนตัวก่อนเพื่อสร้างแผนออกกำลังกาย')
            return redirect('profile_setup')
    except UserProfile.DoesNotExist:
        messages.warning(request, 'โปรดกรอกข้อมูลส่วนตัวก่อนเพื่อสร้างแผนออกกำลังกาย')
        return redirect('profile_setup')
    
    # ดึงแผนออกกำลังกายล่าสุดของผู้ใช้
    exercise_plan = ExercisePlan.objects.filter(user=request.user).order_by('-created_at').first()
    
    if request.method == 'POST':
        # สร้างหรือแก้ไขแผนออกกำลังกาย
        form = ExercisePlanForm(request.POST, instance=exercise_plan)
        if form.is_valid():
            plan = form.save(commit=False)
            plan.user = request.user
            plan.save()
            
            # สร้างแผนการออกกำลังกายรายวัน
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
    # ตรวจสอบว่าผู้ใช้มีการสมัครสมาชิกที่ใช้งานอยู่
    active_subscription = Subscription.objects.filter(user=request.user, status='active').first()
    if not active_subscription:
        return redirect('subscription_list')
    
    # ดึงแผนออกกำลังกายล่าสุดของผู้ใช้
    exercise_plan = ExercisePlan.objects.filter(user=request.user).order_by('-created_at').first()
    
    if not exercise_plan:
        messages.info(request, 'คุณยังไม่มีแผนออกกำลังกาย กรุณาสร้างแผนใหม่')
        return redirect('exercise_plan')
    
    # ดึงแผนการออกกำลังกายรายวัน
    workout_days = WorkoutDay.objects.filter(exercise_plan=exercise_plan).prefetch_related('exercises__exercise')
    
    # จัดการแสดงผลปฏิทิน
    today = timezone.now().date()
    start_date = exercise_plan.start_date
    
    # สร้างปฏิทิน 4 สัปดาห์ (28 วัน)
    calendar_days = []
    for i in range(28):
        day_date = start_date + timezone.timedelta(days=i)
        day_number = i % 7 + 1  # วันที่ 1-7 ในแต่ละสัปดาห์
        
        # หาแผนการออกกำลังกายสำหรับวันนี้
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
    
    # ตรวจสอบว่าเป็นแผนของผู้ใช้นี้
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

@login_required
@subscription_required
def meal_plan(request):
    """หน้าจัดการแผนอาหาร"""
    # ตรวจสอบว่าผู้ใช้มีการสมัครสมาชิกที่ใช้งานอยู่
    active_subscription = Subscription.objects.filter(user=request.user, status='active').first()
    if not active_subscription:
        return redirect('subscription_list')
    
    # ตรวจสอบว่าผู้ใช้ได้กรอกข้อมูลส่วนตัวแล้วหรือไม่
    try:
        profile = UserProfile.objects.get(user=request.user)
        if not profile.has_completed_profile:
            messages.warning(request, 'โปรดกรอกข้อมูลส่วนตัวก่อนเพื่อสร้างแผนอาหาร')
            return redirect('profile_setup')
    except UserProfile.DoesNotExist:
        messages.warning(request, 'โปรดกรอกข้อมูลส่วนตัวก่อนเพื่อสร้างแผนอาหาร')
        return redirect('profile_setup')
    
    # ดึงแผนอาหารล่าสุดของผู้ใช้
    meal_plan = MealPlan.objects.filter(user=request.user).order_by('-created_at').first()
    
    # คำนวณพลังงานที่ร่างกายใช้ทั้งหมดในแต่ละวัน (TDEE)
    tdee = profile.calculate_tdee()
    
    if request.method == 'POST':
        # สร้างหรือแก้ไขแผนอาหาร
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
            if goal == 'weight_loss':
                calories = max(1200, int(tdee * 0.8))  # ลด 20%
            elif goal == 'muscle_gain':
                calories = int(tdee * 1.1)  # เพิ่ม 10%
            else:
                calories = tdee
                
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
    # ตรวจสอบว่าผู้ใช้มีการสมัครสมาชิกที่ใช้งานอยู่
    active_subscription = Subscription.objects.filter(user=request.user, status='active').first()
    if not active_subscription:
        return redirect('subscription_list')
    
    # ดึงแผนอาหารล่าสุดของผู้ใช้
    meal_plan = MealPlan.objects.filter(user=request.user).order_by('-created_at').first()
    
    if not meal_plan:
        messages.info(request, 'คุณยังไม่มีแผนอาหาร กรุณาสร้างแผนใหม่')
        return redirect('meal_plan')
    
    # ดึงแผนอาหารรายวัน
    daily_meals = DailyMeal.objects.filter(meal_plan=meal_plan).prefetch_related('meal_items__recipe')
    
    # คำนวณสารอาหารหลัก
    macros = meal_plan.calculate_macros()
    
    # จัดการแสดงผลปฏิทิน
    today = timezone.now().date()
    start_date = meal_plan.start_date
    
    # สร้างปฏิทิน 4 สัปดาห์ (28 วัน)
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
    
    # ตรวจสอบว่าเป็นแผนของผู้ใช้นี้
    if daily_meal.meal_plan.user != request.user:
        messages.error(request, 'คุณไม่มีสิทธิ์เข้าถึงแผนนี้')
        return redirect('user_dashboard')  # แก้ไขตามชื่อฟังก์ชันที่ถูกต้อง
    
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
   
   # ดึงส่วนผสม
   ingredients = Ingredient.objects.filter(recipe=recipe)
   
   context = {
       'recipe': recipe,
       'ingredients': ingredients
   }
   return render(request, 'myapp/view_recipe.html', context)

# ฟังก์ชั่นช่วยสร้างแผนอาหาร
def generate_meal_plan(meal_plan):
   """สร้างแผนอาหารรายวันตามเป้าหมายและความต้องการทางโภชนาการ"""
   # ลบแผนเดิมหากมี
   DailyMeal.objects.filter(meal_plan=meal_plan).delete()
   
   # สร้างชุดสูตรอาหารที่เหมาะสมตามเป้าหมาย
   diet_type = 'any'  # ค่าเริ่มต้น
   if 'vegetarian' in meal_plan.dietary_restrictions.lower():
       diet_type = 'vegetarian'
   elif 'vegan' in meal_plan.dietary_restrictions.lower():
       diet_type = 'vegan'
   
   # สร้างเมนูอาหารตามเป้าหมาย
   if meal_plan.goal == 'weight_loss':
       breakfast_recipes = Recipe.objects.filter(meal_type='breakfast', diet_type__in=[diet_type, 'any'], calories_per_serving__lt=400).order_by('?')
       lunch_recipes = Recipe.objects.filter(meal_type='lunch', diet_type__in=[diet_type, 'any'], calories_per_serving__lt=500).order_by('?')
       dinner_recipes = Recipe.objects.filter(meal_type='dinner', diet_type__in=[diet_type, 'any'], calories_per_serving__lt=500).order_by('?')
       snack_recipes = Recipe.objects.filter(meal_type='snack', diet_type__in=[diet_type, 'any'], calories_per_serving__lt=200).order_by('?')
   
   elif meal_plan.goal == 'muscle_gain':
       breakfast_recipes = Recipe.objects.filter(meal_type='breakfast', diet_type__in=[diet_type, 'any'], protein__gt=20).order_by('?')
       lunch_recipes = Recipe.objects.filter(meal_type='lunch', diet_type__in=[diet_type, 'any'], protein__gt=30).order_by('?')
       dinner_recipes = Recipe.objects.filter(meal_type='dinner', diet_type__in=[diet_type, 'any'], protein__gt=30).order_by('?')
       snack_recipes = Recipe.objects.filter(meal_type='snack', diet_type__in=[diet_type, 'any'], protein__gt=10).order_by('?')
   
   else:  # general_health, maintenance
       breakfast_recipes = Recipe.objects.filter(meal_type='breakfast', diet_type__in=[diet_type, 'any']).order_by('?')
       lunch_recipes = Recipe.objects.filter(meal_type='lunch', diet_type__in=[diet_type, 'any']).order_by('?')
       dinner_recipes = Recipe.objects.filter(meal_type='dinner', diet_type__in=[diet_type, 'any']).order_by('?')
       snack_recipes = Recipe.objects.filter(meal_type='snack', diet_type__in=[diet_type, 'any']).order_by('?')
   
   # หากไม่มีสูตรอาหารที่ตรงตามเงื่อนไข ใช้ทั้งหมด
   if not breakfast_recipes:
       breakfast_recipes = Recipe.objects.filter(meal_type='breakfast').order_by('?')
   if not lunch_recipes:
       lunch_recipes = Recipe.objects.filter(meal_type='lunch').order_by('?')
   if not dinner_recipes:
       dinner_recipes = Recipe.objects.filter(meal_type='dinner').order_by('?')
   if not snack_recipes:
       snack_recipes = Recipe.objects.filter(meal_type='snack').order_by('?')
   
   # สร้างแผนอาหาร 7 วัน
   for day in range(1, 8):
       daily_meal = DailyMeal.objects.create(
           meal_plan=meal_plan,
           day_number=day
       )
       
       # เพิ่มมื้ออาหาร
       # อาหารเช้า
       if breakfast_recipes:
           breakfast = breakfast_recipes[day % len(breakfast_recipes)]
           MealItem.objects.create(
               daily_meal=daily_meal,
               recipe=breakfast,
               meal_time='breakfast'
           )
       
       # อาหารกลางวัน
       if lunch_recipes:
           lunch = lunch_recipes[day % len(lunch_recipes)]
           MealItem.objects.create(
               daily_meal=daily_meal,
               recipe=lunch,
               meal_time='lunch'
           )
       
       # อาหารเย็น
       if dinner_recipes:
           dinner = dinner_recipes[day % len(dinner_recipes)]
           MealItem.objects.create(
               daily_meal=daily_meal,
               recipe=dinner,
               meal_time='dinner'
           )
       
       # อาหารว่าง (ถ้ามีมากกว่า 3 มื้อ)
       if meal_plan.meals_per_day > 3 and snack_recipes:
           snack = snack_recipes[day % len(snack_recipes)]
           MealItem.objects.create(
               daily_meal=daily_meal,
               recipe=snack,
               meal_time='snack'
           )

# views.py
# เพิ่มการนำเข้าฟังก์ชันช่วยเหลือ
from .utils import distribute_training_days, create_workout_exercises

# ใช้ในฟังก์ชัน generate_workout_plan
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

@login_required
def order_history(request):
    """แสดงประวัติคำสั่งซื้อของผู้ใช้"""
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'myapp/order_history.html', {'orders': orders})

@login_required
def order_detail(request, order_id):
    """แสดงรายละเอียดคำสั่งซื้อ"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'myapp/order_detail.html', {'order': order})

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
    
    context = {
        'user_profile': profile
    }
    return render(request, 'myapp/profile_update.html', context)

@login_required
def password_change(request):
    """เปลี่ยนรหัสผ่าน - ใช้ view มาตรฐานของ Django"""
    return redirect('django.contrib.auth.views.password_change')

@login_required
def wishlist(request):
    """แสดงรายการโปรด"""
    # สมมติว่ามีโมเดล Wishlist
    wishlist_items = Wishlist.objects.filter(user=request.user)
    return render(request, 'myapp/wishlist.html', {'wishlist_items': wishlist_items})

@login_required
def remove_from_wishlist(request, item_id):
    """ลบสินค้าออกจากรายการโปรด"""
    wishlist_item = get_object_or_404(Wishlist, id=item_id, user=request.user)
    wishlist_item.delete()
    messages.success(request, 'ลบสินค้าออกจากรายการโปรดเรียบร้อยแล้ว')
    return redirect('wishlist')

@login_required
def support(request):
    """หน้าติดต่อช่วยเหลือ"""
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        order_number = request.POST.get('order_number')
        message = request.POST.get('message')
        
        # บันทึกข้อความติดต่อลงฐานข้อมูล (ถ้ามีโมเดล ContactMessage)
        # หรือส่งอีเมลแจ้งเตือนไปยังทีมงาน
        
        messages.success(request, 'ส่งข้อความเรียบร้อยแล้ว เราจะติดต่อกลับโดยเร็วที่สุด')
        return redirect('support')
    
    return render(request, 'myapp/support.html')

@login_required
def remove_from_cart(request, item_id):
    """ลบสินค้าออกจากตะกร้า"""
    order_item = get_object_or_404(OrderItem, id=item_id, order__user=request.user, order__status='pending')
    order = order_item.order
    
    # ลบรายการจากตะกร้า
    order_item.delete()
    
    # อัปเดตยอดรวมของคำสั่งซื้อ
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
    
    # อัปเดตยอดรวมของคำสั่งซื้อ
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
        # ดำเนินการชำระเงิน (จำลองว่าสำเร็จเสมอ)
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
        # บันทึกข้อมูลความก้าวหน้า
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