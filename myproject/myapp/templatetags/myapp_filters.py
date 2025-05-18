# myapp/templatetags/myapp_filters.py
from django import template
from itertools import groupby

register = template.Library()

@register.filter
def multiply(value, arg):
    """คูณค่าด้วยอาร์กิวเมนต์"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return value

@register.filter
def modulo(value, arg):
    """หารเอาเศษ (modulo)"""
    try:
        return int(value) % int(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def divisibleby(value, arg):
    """ตรวจสอบว่าหารลงตัวหรือไม่"""
    try:
        return int(value) // int(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def strip(value):
    """ตัดช่องว่างต้นและท้ายข้อความ"""
    return value.strip() if value else ""

@register.filter
def splitlines(value):
    """แยกข้อความออกเป็นบรรทัด"""
    return value.splitlines() if value else []

@register.filter
def yesno(value, arg):
    """แปลงค่าบูลีนเป็นข้อความ"""
    args = arg.split(",")
    if len(args) != 2:
        return value
    return args[0] if value else args[1]

@register.filter(name='groupby')
def groupby_filter(value, key):
    """จัดกลุ่มรายการตามคีย์ที่กำหนด"""
    if not value:
        return []
    
    keyfunc = lambda x: getattr(x, key)
    return [{'grouper': k, 'list': list(g)} for k, g in groupby(sorted(value, key=keyfunc), key=keyfunc)]

@register.filter
def div(value, arg):
    """หารค่าด้วยอาร์กิวเมนต์"""
    try:
        # เพิ่มการตรวจสอบค่า None
        if value is None or arg is None:
            return None
        # ป้องกันการหารด้วย 0
        if float(arg) == 0:
            return None
        return float(value) / float(arg)
    except (ValueError, TypeError, ZeroDivisionError):
        return None

@register.filter
def sum_quantity(items):
    """รวมจำนวนสินค้าทั้งหมดในตะกร้า"""
    try:
        return sum(item.quantity for item in items)
    except:
        return 0