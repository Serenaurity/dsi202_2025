from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from allauth.socialaccount.models import SocialAccount
from .models import UserProfile

@receiver(post_save, sender=SocialAccount)
def create_profile_for_social_user(sender, instance, created, **kwargs):
    """สร้าง UserProfile สำหรับผู้ใช้ที่ล็อกอินผ่าน Social Account"""
    if created:
        user = instance.user
        # ตรวจสอบว่ามี UserProfile แล้วหรือไม่
        if not hasattr(user, 'profile'):
            # สร้าง UserProfile ใหม่
            user_profile = UserProfile(user=user)
            
            # ถ้ามีข้อมูลใน social account ให้ดึงมาใช้
            if instance.provider == 'google':
                extra_data = instance.extra_data
                if 'name' in extra_data:
                    # อาจจะดึงข้อมูลอื่นๆ เพิ่มเติมตามที่ต้องการ
                    pass
                    
            user_profile.save()