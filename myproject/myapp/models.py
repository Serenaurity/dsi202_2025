from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal

class Product(models.Model):
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name

class SubscriptionPlan(models.Model):
    DURATION_CHOICES = [
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
    ]
    
    name = models.CharField(max_length=200)
    description = models.TextField()
    duration = models.CharField(max_length=10, choices=DURATION_CHOICES, default='monthly')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.name} ({self.get_duration_display()})"

class Subscription(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscriptions')
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE)
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    
    def __str__(self):
        return f"{self.user.username} - {self.plan.name}"
    
    def save(self, *args, **kwargs):
        # Calculate end_date based on plan duration if not set
        if not self.end_date:
            if self.plan.duration == 'monthly':
                self.end_date = self.start_date + timezone.timedelta(days=30)
            elif self.plan.duration == 'quarterly':
                self.end_date = self.start_date + timezone.timedelta(days=90)
            elif self.plan.duration == 'yearly':
                self.end_date = self.start_date + timezone.timedelta(days=365)
        
        # Check if subscription has expired
        if self.end_date < timezone.now() and self.status == 'active':
            self.status = 'expired'
            
        super().save(*args, **kwargs)

# myapp/models.py
# ในคลาส Subscription เพิ่มเมธอด property สำหรับคำนวณจำนวนวันที่เหลือ

    @property
    def remaining_days(self):
        """คำนวณจำนวนวันที่เหลือของสมาชิก"""
        if self.status != 'active':
            return 0
        
        today = timezone.now().date()
        if self.end_date < today:
            return 0
        
        return (self.end_date - today).days    

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'รอดำเนินการ'),
        ('paid', 'ชำระแล้ว'),
        ('shipped', 'จัดส่งแล้ว'),
        ('delivered', 'ได้รับสินค้าแล้ว'),
        ('cancelled', 'ยกเลิก'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    order_number = models.CharField(max_length=20, unique=True, null=True, blank=True)
    
    def __str__(self):
        return f"คำสั่งซื้อ #{self.id} - {self.user.username}"
        
    def save(self, *args, **kwargs):
        if not self.order_number and self.id:
            self.order_number = f"ORD-{self.id:06d}"
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Order #{self.id} - {self.user.username}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return f"{self.quantity} x {self.product.name}"
    
    def save(self, *args, **kwargs):
        # Set price from product if not explicitly provided
        if not self.price:
            self.price = self.product.price
        super().save(*args, **kwargs)

# models.py - เพิ่มโมเดล

# โมเดลสำหรับความก้าวหน้าของผู้ใช้
class Progress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='progress')
    date = models.DateField(default=timezone.now)
    weight = models.FloatField(null=True, blank=True)
    exercise_minutes = models.IntegerField(default=0)
    notes = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.date}"

# โมเดลสำหรับบทความ
class Article(models.Model):
    CATEGORY_CHOICES = [
        ('exercise', 'การออกกำลังกาย'),
        ('nutrition', 'โภชนาการ'),
        ('wellness', 'สุขภาพองค์รวม'),
    ]
    
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    content = models.TextField()
    image = models.ImageField(upload_to='articles/', blank=True, null=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)
    published = models.BooleanField(default=True)
    
    def __str__(self):
        return self.title

# โมเดลสำหรับวิดีโอสอน
class Video(models.Model):
    CATEGORY_CHOICES = [
        ('beginner', 'สำหรับผู้เริ่มต้น'),
        ('intermediate', 'ระดับกลาง'),
        ('advanced', 'ระดับสูง'),
        ('equipment', 'การใช้อุปกรณ์'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    video_url = models.URLField()
    thumbnail = models.ImageField(upload_to='video_thumbnails/')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    duration = models.IntegerField(help_text="ความยาวในวินาที")
    date = models.DateTimeField(auto_now_add=True)
    published = models.BooleanField(default=True)
    
    def __str__(self):
        return self.title

# โมเดลสำหรับแผนโภชนาการ
class NutritionPlan(models.Model):
    GOAL_CHOICES = [
        ('weight_loss', 'ลดน้ำหนัก'),
        ('muscle_gain', 'เพิ่มกล้ามเนื้อ'),
        ('maintenance', 'รักษาสภาพ'),
        ('general_health', 'สุขภาพทั่วไป'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    goal = models.CharField(max_length=20, choices=GOAL_CHOICES, default='general_health')
    dietary_restriction = models.TextField(blank=True, help_text="ข้อจำกัดด้านอาหาร เช่น แพ้อาหาร")
    calorie_target = models.IntegerField(default=2000)
    protein_ratio = models.IntegerField(default=30, help_text="เปอร์เซ็นต์ของโปรตีน")
    carb_ratio = models.IntegerField(default=40, help_text="เปอร์เซ็นต์ของคาร์โบไฮเดรต")
    fat_ratio = models.IntegerField(default=30, help_text="เปอร์เซ็นต์ของไขมัน")
    
    def __str__(self):
        return f"แผนโภชนาการของ {self.user.username}"

# โมเดลสำหรับฟอรั่ม
class ForumTopic(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    last_activity = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name

class ForumThread(models.Model):
    topic = models.ForeignKey(ForumTopic, on_delete=models.CASCADE, related_name='threads')
    title = models.CharField(max_length=200)
    content = models.TextField()
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title

class ForumReply(models.Model):
    thread = models.ForeignKey(ForumThread, on_delete=models.CASCADE, related_name='replies')
    content = models.TextField()
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"ตอบกลับโดย {self.author.username}"

# models.py - เพิ่มโมเดลสำหรับแผนออกกำลังกายและโภชนาการ

class UserProfile(models.Model):
    GENDER_CHOICES = [
        ('male', 'ชาย'),
        ('female', 'หญิง'),
        ('other', 'อื่นๆ')
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    birth_date = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, null=True, blank=True)
    height = models.FloatField(help_text="ความสูง (ซม.)", null=True, blank=True)
    weight = models.FloatField(help_text="น้ำหนัก (กก.)", null=True, blank=True)
    activity_level = models.IntegerField(
        choices=[
            (1, 'ไม่ค่อยได้ออกกำลังกาย'),
            (2, 'ออกกำลังกายเบาๆ 1-3 วัน/สัปดาห์'),
            (3, 'ออกกำลังกายปานกลาง 3-5 วัน/สัปดาห์'),
            (4, 'ออกกำลังกายหนัก 6-7 วัน/สัปดาห์'),
            (5, 'ออกกำลังกายหนักมาก (นักกีฬา)')
        ],
        default=1
    )
    medical_conditions = models.TextField(blank=True, help_text="โรคประจำตัวหรือข้อจำกัดทางการแพทย์")
    has_completed_profile = models.BooleanField(default=False)
    
    def __str__(self):
        return f"โปรไฟล์ของ {self.user.username}"
    
    def calculate_bmr(self):
        """คำนวณอัตราการเผาผลาญพลังงานพื้นฐาน (BMR)"""
        if not self.weight or not self.height or not self.birth_date or not self.gender:
            return None
            
        age = (timezone.now().date() - self.birth_date).days // 365
        
        if self.gender == 'male':
            return 88.362 + (13.397 * self.weight) + (4.799 * self.height) - (5.677 * age)
        else:
            return 447.593 + (9.247 * self.weight) + (3.098 * self.height) - (4.330 * age)
    
    def calculate_tdee(self):
        """คำนวณพลังงานที่ร่างกายใช้ทั้งหมดในแต่ละวัน (TDEE)"""
        bmr = self.calculate_bmr()
        if not bmr:
            return None
            
        activity_multipliers = {
            1: 1.2,    # ไม่ค่อยได้ออกกำลังกาย
            2: 1.375,  # ออกกำลังกายเบาๆ
            3: 1.55,   # ออกกำลังกายปานกลาง
            4: 1.725,  # ออกกำลังกายหนัก
            5: 1.9     # ออกกำลังกายหนักมาก
        }
        
        return round(bmr * activity_multipliers.get(self.activity_level, 1.2))

class ExercisePlan(models.Model):
    GOAL_CHOICES = [
        ('weight_loss', 'ลดน้ำหนัก'),
        ('fat_loss', 'ลดไขมัน'),
        ('muscle_gain', 'สร้างกล้ามเนื้อ'),
        ('endurance', 'เพิ่มความอดทน'),
        ('general_fitness', 'สุขภาพทั่วไป')
    ]
    
    LEVEL_CHOICES = [
        ('beginner', 'มือใหม่'),
        ('intermediate', 'ปานกลาง'),
        ('advanced', 'ขั้นสูง')
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='exercise_plans')
    goal = models.CharField(max_length=20, choices=GOAL_CHOICES)
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES)
    days_per_week = models.IntegerField(default=3, choices=[(i, str(i)) for i in range(1, 8)])
    preferred_time = models.CharField(
        max_length=20,
        choices=[('morning', 'เช้า'), ('afternoon', 'บ่าย'), ('evening', 'เย็น')],
        default='evening'
    )
    training_focus = models.CharField(
        max_length=20,
        choices=[
            ('full_body', 'ทั้งร่างกาย'),
            ('upper_lower', 'ส่วนบน/ส่วนล่าง'),
            ('push_pull_legs', 'ดัน/ดึง/ขา')
        ],
        default='full_body'
    )
    available_equipment = models.BooleanField(default=False, help_text="มีอุปกรณ์ออกกำลังกายที่บ้านหรือไม่")
    created_at = models.DateTimeField(auto_now_add=True)
    start_date = models.DateField(default=timezone.now)
    
    def __str__(self):
        return f"แผนออกกำลังกายของ {self.user.username} - {self.get_goal_display()}"

class Exercise(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    muscle_group = models.CharField(
        max_length=20,
        choices=[
            ('chest', 'หน้าอก'),
            ('back', 'หลัง'),
            ('shoulders', 'ไหล่'),
            ('arms', 'แขน'),
            ('legs', 'ขา'),
            ('core', 'แกนกลาง'),
            ('full_body', 'ทั้งร่างกาย')
        ]
    )
    difficulty = models.CharField(
        max_length=20,
        choices=[('beginner', 'มือใหม่'), ('intermediate', 'ปานกลาง'), ('advanced', 'ขั้นสูง')]
    )
    instructions = models.TextField()
    video_url = models.URLField(blank=True)
    equipment_required = models.BooleanField(default=False)
    
    def __str__(self):
        return self.name

class WorkoutDay(models.Model):
    exercise_plan = models.ForeignKey(ExercisePlan, on_delete=models.CASCADE, related_name='workout_days')
    day_number = models.IntegerField()
    focus = models.CharField(
        max_length=20,
        choices=[
            ('rest', 'พักผ่อน'),
            ('cardio', 'คาร์ดิโอ'),
            ('strength', 'เวทเทรนนิ่ง'),
            ('flexibility', 'ความยืดหยุ่น'),
            ('hiit', 'HIIT'),
            ('upper_body', 'ส่วนบน'),
            ('lower_body', 'ส่วนล่าง'),
            ('full_body', 'ทั้งร่างกาย')
        ]
    )
    
    def __str__(self):
        return f"วันที่ {self.day_number} - {self.get_focus_display()}"
    
    class Meta:
        ordering = ['day_number']

class WorkoutExercise(models.Model):
    workout_day = models.ForeignKey(WorkoutDay, on_delete=models.CASCADE, related_name='exercises')
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE)
    sets = models.IntegerField(default=3)
    reps = models.CharField(max_length=20, default="10-12")
    rest_time = models.IntegerField(default=60, help_text="เวลาพักระหว่างเซ็ต (วินาที)")
    notes = models.CharField(max_length=255, blank=True)
    order = models.IntegerField(default=0)
    
    def __str__(self):
        return f"{self.exercise.name} - {self.sets} x {self.reps}"
    
    class Meta:
        ordering = ['order']

class MealPlan(models.Model):
    GOAL_CHOICES = [
        ('weight_loss', 'ลดน้ำหนัก'),
        ('muscle_gain', 'สร้างกล้ามเนื้อ'),
        ('maintenance', 'รักษาสภาพ'),
        ('general_health', 'สุขภาพทั่วไป')
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='meal_plans')
    goal = models.CharField(max_length=20, choices=GOAL_CHOICES)
    daily_calories = models.IntegerField(default=2000)
    protein_ratio = models.IntegerField(default=30, help_text="เปอร์เซ็นต์ของโปรตีน")
    carb_ratio = models.IntegerField(default=40, help_text="เปอร์เซ็นต์ของคาร์โบไฮเดรต")
    fat_ratio = models.IntegerField(default=30, help_text="เปอร์เซ็นต์ของไขมัน")
    meals_per_day = models.IntegerField(default=3, choices=[(i, str(i)) for i in range(2, 7)])
    dietary_restrictions = models.TextField(blank=True, help_text="ข้อจำกัดด้านอาหาร เช่น มังสวิรัติ, แพ้อาหาร")
    allergies = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    start_date = models.DateField(default=timezone.now)
    
    def __str__(self):
        return f"แผนอาหารของ {self.user.username} - {self.get_goal_display()}"
    
    def calculate_macros(self):
        """คำนวณสารอาหารหลักในแต่ละวัน"""
        protein_cals = self.daily_calories * (self.protein_ratio / 100)
        carb_cals = self.daily_calories * (self.carb_ratio / 100)
        fat_cals = self.daily_calories * (self.fat_ratio / 100)
        
        # 1g โปรตีน = 4 แคลอรี่, 1g คาร์บ = 4 แคลอรี่, 1g ไขมัน = 9 แคลอรี่
        protein_g = round(protein_cals / 4)
        carb_g = round(carb_cals / 4)
        fat_g = round(fat_cals / 9)
        
        return {
            'protein': protein_g,
            'carbs': carb_g,
            'fat': fat_g
        }

class Recipe(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    instructions = models.TextField()
    prep_time = models.IntegerField(help_text="เวลาเตรียม (นาที)")
    cook_time = models.IntegerField(help_text="เวลาปรุง (นาที)")
    servings = models.IntegerField(default=1)
    calories_per_serving = models.IntegerField()
    protein = models.FloatField(help_text="โปรตีน (กรัม)")
    carbs = models.FloatField(help_text="คาร์โบไฮเดรต (กรัม)")
    fat = models.FloatField(help_text="ไขมัน (กรัม)")
    image = models.ImageField(upload_to='recipes/', blank=True, null=True)
    
    MEAL_TYPE_CHOICES = [
        ('breakfast', 'อาหารเช้า'),
        ('lunch', 'อาหารกลางวัน'),
        ('dinner', 'อาหารเย็น'),
        ('snack', 'อาหารว่าง')
    ]
    meal_type = models.CharField(max_length=20, choices=MEAL_TYPE_CHOICES)
    
    DIET_TYPE_CHOICES = [
        ('any', 'ทั่วไป'),
        ('vegetarian', 'มังสวิรัติ'),
        ('vegan', 'วีแกน'),
        ('low_carb', 'คาร์บต่ำ'),
        ('high_protein', 'โปรตีนสูง')
    ]
    diet_type = models.CharField(max_length=20, choices=DIET_TYPE_CHOICES, default='any')
    
    def __str__(self):
        return self.name

class Ingredient(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='ingredients')
    name = models.CharField(max_length=100)
    amount = models.CharField(max_length=50)
    
    def __str__(self):
        return f"{self.amount} {self.name}"

class DailyMeal(models.Model):
    meal_plan = models.ForeignKey(MealPlan, on_delete=models.CASCADE, related_name='daily_meals')
    day_number = models.IntegerField()
    
    def __str__(self):
        return f"วันที่ {self.day_number} ของแผนอาหาร"
    
    class Meta:
        ordering = ['day_number']

class MealItem(models.Model):
    daily_meal = models.ForeignKey(DailyMeal, on_delete=models.CASCADE, related_name='meal_items')
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    meal_time = models.CharField(max_length=20, choices=Recipe.MEAL_TYPE_CHOICES)
    
    def __str__(self):
        return f"{self.get_meal_time_display()}: {self.recipe.name}"

class Content(models.Model):
    CATEGORY_CHOICES = [
        ('weight_loss', 'ลดน้ำหนัก'),
        ('muscle_building', 'สร้างกล้ามเนื้อ'),
        ('cardio', 'คาร์ดิโอ'),
        ('general', 'ทั่วไป'),
    ]
    
    title = models.CharField(max_length=200)
    content = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='general')
    image = models.ImageField(upload_to='content/', blank=True, null=True)
    is_published = models.BooleanField(default=True)
    published_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.title

class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wishlist_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'product')  # ป้องกันการเพิ่มสินค้าซ้ำ
        
    def __str__(self):
        return f"{self.user.username} - {self.product.name}"

# myapp/models.py
class FeatureUsage(models.Model):
    """บันทึกการใช้งานฟีเจอร์ที่จำกัดให้เฉพาะสมาชิก"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='feature_usage')
    subscription = models.ForeignKey(Subscription, on_delete=models.SET_NULL, null=True, related_name='usage')
    feature = models.CharField(max_length=50, choices=[
        ('exercise_plan', 'แผนออกกำลังกาย'),
        ('meal_plan', 'แผนอาหาร'),
        ('progress_tracking', 'ติดตามความก้าวหน้า'),
        ('nutrition_plan', 'แผนโภชนาการ'),
    ])
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.get_feature_display()} - {self.timestamp.strftime('%d/%m/%Y %H:%M')}"