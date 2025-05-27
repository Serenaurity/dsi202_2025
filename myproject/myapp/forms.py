# forms.py - เพิ่มฟอร์มสำหรับกรอกข้อมูล

from django import forms
from .models import UserProfile, ExercisePlan, MealPlan, NutritionPlan
# เพิ่มใน forms.py
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # เพิ่มคลาสให้กับ input fields สำหรับ Tailwind CSS
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500'

class UserProfileForm(forms.ModelForm):
    birth_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        help_text="วันเกิดของคุณ",
        label="วันเกิด"
    )
    
    class Meta:
        model = UserProfile
        fields = ['birth_date', 'gender', 'height', 'weight', 'activity_level', 'medical_conditions']
        labels = {
            'gender': 'เพศ',
            'height': 'ความสูง (ซม.)',
            'weight': 'น้ำหนัก (กก.)',
            'activity_level': 'ระดับการออกกำลังกาย',
            'medical_conditions': 'โรคประจำตัวหรือข้อจำกัดทางการแพทย์'
        }

class ExercisePlanForm(forms.ModelForm):
    class Meta:
        model = ExercisePlan
        fields = ['goal', 'level', 'days_per_week', 'preferred_time', 'training_focus', 'available_equipment']
        labels = {
            'goal': 'เป้าหมายการออกกำลังกาย',
            'level': 'ระดับความสามารถ',
            'days_per_week': 'จำนวนวันออกกำลังกายต่อสัปดาห์',
            'preferred_time': 'ช่วงเวลาที่ต้องการออกกำลังกาย',
            'training_focus': 'รูปแบบการฝึก',
            'available_equipment': 'มีอุปกรณ์ออกกำลังกายที่บ้าน'
        }

class MealPlanForm(forms.ModelForm):
    class Meta:
        model = MealPlan
        fields = ['goal', 'daily_calories', 'protein_ratio', 'carb_ratio', 'fat_ratio', 'meals_per_day', 'dietary_restrictions', 'allergies']
        labels = {
            'goal': 'เป้าหมายโภชนาการ',
            'daily_calories': 'แคลอรี่ต่อวัน',
            'protein_ratio': 'สัดส่วนโปรตีน (%)',
            'carb_ratio': 'สัดส่วนคาร์โบไฮเดรต (%)',
            'fat_ratio': 'สัดส่วนไขมัน (%)',
            'meals_per_day': 'จำนวนมื้ออาหารต่อวัน',
            'dietary_restrictions': 'ข้อจำกัดด้านอาหาร',
            'allergies': 'อาหารที่แพ้'
        }
        widgets = {
            'protein_ratio': forms.NumberInput(attrs={'min': 10, 'max': 50}),
            'carb_ratio': forms.NumberInput(attrs={'min': 10, 'max': 70}),
            'fat_ratio': forms.NumberInput(attrs={'min': 10, 'max': 50}),
        }

# เพิ่มคลาสนี้ลงในไฟล์ forms.py
class NutritionPreferencesForm(forms.ModelForm):
    class Meta:
        model = NutritionPlan
        fields = ['goal', 'calorie_target', 'protein_ratio', 'carb_ratio', 'fat_ratio', 'dietary_restriction']
        labels = {
            'goal': 'เป้าหมาย',
            'calorie_target': 'เป้าหมายแคลอรี่ต่อวัน',
            'protein_ratio': 'สัดส่วนโปรตีน (%)',
            'carb_ratio': 'สัดส่วนคาร์โบไฮเดรต (%)',
            'fat_ratio': 'สัดส่วนไขมัน (%)',
            'dietary_restriction': 'ข้อจำกัดด้านอาหาร'
        }
        widgets = {
            'dietary_restriction': forms.Textarea(attrs={'rows': 3}),
        }