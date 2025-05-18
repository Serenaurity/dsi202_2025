# myproject/myapp/forms.py
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import (
    UserProfile, Product, Order, Review, 
    ExercisePlan, MealPlan, Progress
)

class BaseForm(forms.ModelForm):
    """Base form class สำหรับลดความซ้ำซ้อนของโค้ด"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # ปรับแต่ง widget สำหรับทุกฟิลด์
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.TextInput) or isinstance(field.widget, forms.EmailInput):
                field.widget.attrs.update({'class': 'form-control rounded-lg'})
            elif isinstance(field.widget, forms.Textarea):
                field.widget.attrs.update({'class': 'form-control rounded-lg', 'rows': 3})
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs.update({'class': 'form-select rounded-lg'})
            elif isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-check-input'})
            elif isinstance(field.widget, forms.DateInput):
                field.widget = forms.DateInput(attrs={
                    'class': 'form-control rounded-lg',
                    'type': 'date'
                })

class LoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control rounded-lg',
        'placeholder': 'Username',
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control rounded-lg',
        'placeholder': 'Password',
    }))

class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # ปรับแต่ง widgets ในวิธีเดียว แทนที่จะกำหนดทีละฟิลด์
        form_fields = ['username', 'email', 'password1', 'password2']
        for field in form_fields:
            self.fields[field].widget.attrs.update({
                'class': 'form-control rounded-lg',
                'placeholder': self.fields[field].label,
            })

class UserProfileForm(BaseForm):
    class Meta:
        model = UserProfile
        fields = ['date_of_birth', 'gender', 'height', 'weight', 'goal', 'activity_level', 'profile_picture']
        
class ProductSearchForm(forms.Form):
    query = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'class': 'form-control rounded-lg',
        'placeholder': 'Search products...',
    }))
    category = forms.ChoiceField(required=False, choices=[('', 'All Categories')] + Product.CATEGORY_CHOICES, 
                                widget=forms.Select(attrs={'class': 'form-select rounded-lg'}))
    
    min_price = forms.DecimalField(required=False, min_value=0, widget=forms.NumberInput(attrs={
        'class': 'form-control rounded-lg',
        'placeholder': 'Min Price',
    }))
    max_price = forms.DecimalField(required=False, min_value=0, widget=forms.NumberInput(attrs={
        'class': 'form-control rounded-lg',
        'placeholder': 'Max Price',
    }))

class ReviewForm(BaseForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']

class ProgressForm(BaseForm):
    class Meta:
        model = Progress
        fields = ['weight', 'body_fat', 'chest', 'waist', 'arms', 'legs', 'notes']

# ฟอร์มสำหรับกรองแผนออกกำลังกาย
class ExercisePlanFilterForm(forms.Form):
    GOAL_CHOICES = [('', 'All Goals')] + ExercisePlan.GOAL_CHOICES
    DURATION_CHOICES = [
        ('', 'All Durations'),
        ('4', '4 Weeks'),
        ('8', '8 Weeks'),
        ('12', '12 Weeks'),
    ]
    
    goal = forms.ChoiceField(choices=GOAL_CHOICES, required=False, 
                            widget=forms.Select(attrs={'class': 'form-select rounded-lg'}))
    duration = forms.ChoiceField(choices=DURATION_CHOICES, required=False,
                                widget=forms.Select(attrs={'class': 'form-select rounded-lg'}))

# ฟอร์มสำหรับกรองแผนอาหาร
class MealPlanFilterForm(forms.Form):
    GOAL_CHOICES = [('', 'All Goals')] + MealPlan.GOAL_CHOICES
    DIET_TYPE_CHOICES = [('', 'All Diet Types')] + MealPlan.DIET_TYPE_CHOICES
    
    goal = forms.ChoiceField(choices=GOAL_CHOICES, required=False,
                            widget=forms.Select(attrs={'class': 'form-select rounded-lg'}))
    diet_type = forms.ChoiceField(choices=DIET_TYPE_CHOICES, required=False,
                                widget=forms.Select(attrs={'class': 'form-select rounded-lg'}))