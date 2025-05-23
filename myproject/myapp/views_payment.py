# myapp/views_payment.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db import transaction
from decimal import Decimal

from .models import (
    Order, Payment, PaymentMethod, ShippingAddress, 
    ShippingMethod, OrderItem
)
from .utils.payment import PromptPayQRGenerator, calculate_shipping_fee


@login_required
def checkout(request):
    """หน้าชำระเงิน"""
    try:
        cart = Order.objects.get(user=request.user, status='pending')
        items = cart.items.all()
        
        if not items:
            messages.error(request, 'ตะกร้าสินค้าว่างเปล่า')
            return redirect('cart')
            
    except Order.DoesNotExist:
        messages.error(request, 'ไม่พบตะกร้าสินค้า')
        return redirect('product_list')
    
    # ดึงข้อมูลที่จำเป็น
    shipping_addresses = ShippingAddress.objects.filter(user=request.user)
    shipping_methods = ShippingMethod.objects.filter(is_active=True)
    payment_methods = PaymentMethod.objects.filter(is_active=True)
    
    if request.method == 'POST':
        # รับข้อมูลจากฟอร์ม
        shipping_address_id = request.POST.get('shipping_address')
        shipping_method_id = request.POST.get('shipping_method')
        payment_method_id = request.POST.get('payment_method')
        
        # สร้างที่อยู่ใหม่ถ้าเลือก "new"
        if shipping_address_id == 'new':
            shipping_address = ShippingAddress.objects.create(
                user=request.user,
                recipient_name=request.POST.get('recipient_name'),
                phone=request.POST.get('phone'),
                address_line1=request.POST.get('address_line1'),
                address_line2=request.POST.get('address_line2', ''),
                subdistrict=request.POST.get('subdistrict'),
                district=request.POST.get('district'),
                province=request.POST.get('province'),
                postal_code=request.POST.get('postal_code'),
            )
        else:
            shipping_address = get_object_or_404(ShippingAddress, id=shipping_address_id, user=request.user)
        
        shipping_method = get_object_or_404(ShippingMethod, id=shipping_method_id)
        payment_method = get_object_or_404(PaymentMethod, id=payment_method_id)
        
        # คำนวณค่าจัดส่ง
        shipping_fee = calculate_shipping_fee(shipping_method, items)
        
        with transaction.atomic():
            # อัปเดตข้อมูลการสั่งซื้อ
            cart.shipping_address = shipping_address
            cart.shipping_method = shipping_method
            cart.shipping_fee = shipping_fee
            cart.save()
            
            # หักสต๊อกสินค้า
            for item in items:
                if item.product.stock < item.quantity:
                    messages.error(request, f'สินค้า {item.product.name} มีไม่เพียงพอ')
                    return redirect('cart')
                
                item.product.stock -= item.quantity
                item.product.save()
            
            # สร้างข้อมูลการชำระเงิน
            payment = Payment.objects.create(
                order=cart,
                payment_method=payment_method,
                amount=cart.total_amount + shipping_fee,
                status='pending'
            )
            
            # ถ้าเลือก PromptPay ให้สร้าง QR Code
            if payment_method.code == 'promptpay':
                generator = PromptPayQRGenerator(
                    payment_method.promptpay_id,
                    float(payment.amount)
                )
                filename, img_file = generator.save_to_field(
                    cart.order_number or f"TEMP{cart.id}",
                    payment_method.promptpay_name
                )
                payment.qr_code.save(filename, img_file)
            
            # อัปเดตสถานะ Order
            cart.status = 'paid' if payment_method.code == 'cash_on_delivery' else 'pending'
            cart.save()
            
            # สร้างเลขที่ใบเสร็จถ้าชำระแล้ว
            if cart.status == 'paid':
                cart.generate_invoice_number()
        
        return redirect('payment_detail', payment_id=payment.id)
    
    # คำนวณยอดรวม
    subtotal = cart.total_amount
    default_shipping = shipping_methods.first()
    shipping_fee = calculate_shipping_fee(default_shipping, items) if default_shipping else 0
    total = subtotal + shipping_fee
    
    context = {
        'cart': cart,
        'items': items,
        'shipping_addresses': shipping_addresses,
        'shipping_methods': shipping_methods,
        'payment_methods': payment_methods,
        'subtotal': subtotal,
        'shipping_fee': shipping_fee,
        'total': total,
    }
    return render(request, 'myapp/checkout.html', context)


@login_required  
def payment_detail(request, payment_id):
    """หน้าแสดงรายละเอียดการชำระเงิน"""
    payment = get_object_or_404(Payment, id=payment_id, order__user=request.user)
    
    if request.method == 'POST' and payment.status == 'pending':
        # อัปโหลดสลิป
        if 'slip_image' in request.FILES:
            payment.slip_image = request.FILES['slip_image']
            payment.status = 'processing'
            payment.save()
            
            messages.success(request, 'อัปโหลดหลักฐานการชำระเงินเรียบร้อย รอการตรวจสอบ')
            
            # TODO: ส่งอีเมลแจ้งเตือน admin
            
    context = {
        'payment': payment,
        'order': payment.order,
    }
    return render(request, 'myapp/payment_detail.html', context)


@login_required
def confirm_payment(request, payment_id):
    """ยืนยันการชำระเงิน (สำหรับ admin)"""
    if not request.user.is_staff:
        messages.error(request, 'คุณไม่มีสิทธิ์เข้าถึงหน้านี้')
        return redirect('home')
    
    payment = get_object_or_404(Payment, id=payment_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'approve':
            payment.status = 'paid'
            payment.paid_at = timezone.now()
            payment.save()
            
            # อัปเดตสถานะ Order
            order = payment.order
            order.status = 'paid'
            order.save()
            order.generate_invoice_number()
            
            messages.success(request, 'ยืนยันการชำระเงินเรียบร้อย')
            
        elif action == 'reject':
            payment.status = 'failed'
            payment.save()
            
            # คืนสต๊อกสินค้า
            for item in payment.order.items.all():
                item.product.stock += item.quantity
                item.product.save()
            
            messages.warning(request, 'ปฏิเสธการชำระเงิน')
    
    return redirect('admin_payment_list')


@login_required
def shipping_address_form(request):
    """ฟอร์มเพิ่ม/แก้ไขที่อยู่จัดส่ง"""
    address_id = request.GET.get('id')
    
    if address_id:
        address = get_object_or_404(ShippingAddress, id=address_id, user=request.user)
    else:
        address = None
    
    if request.method == 'POST':
        if address:
            # แก้ไข
            address.recipient_name = request.POST.get('recipient_name')
            address.phone = request.POST.get('phone')
            address.address_line1 = request.POST.get('address_line1')
            address.address_line2 = request.POST.get('address_line2', '')
            address.subdistrict = request.POST.get('subdistrict')
            address.district = request.POST.get('district')
            address.province = request.POST.get('province')
            address.postal_code = request.POST.get('postal_code')
            address.save()
            messages.success(request, 'แก้ไขที่อยู่เรียบร้อย')
        else:
            # สร้างใหม่
            ShippingAddress.objects.create(
                user=request.user,
                recipient_name=request.POST.get('recipient_name'),
                phone=request.POST.get('phone'),
                address_line1=request.POST.get('address_line1'),
                address_line2=request.POST.get('address_line2', ''),
                subdistrict=request.POST.get('subdistrict'),
                district=request.POST.get('district'),
                province=request.POST.get('province'),
                postal_code=request.POST.get('postal_code'),
                is_default=request.POST.get('is_default', False)
            )
            messages.success(request, 'เพิ่มที่อยู่เรียบร้อย')
        
        return redirect('profile_update')
    
    context = {
        'address': address,
        'provinces': get_thai_provinces(),  # ฟังก์ชันดึงรายชื่อจังหวัด
    }
    return render(request, 'myapp/shipping_address_form.html', context)


def get_thai_provinces():
    """รายชื่อจังหวัดในประเทศไทย"""
    return [
        'กรุงเทพมหานคร', 'กระบี่', 'กาญจนบุรี', 'กาฬสินธุ์', 'กำแพงเพชร',
        'ขอนแก่น', 'จันทบุรี', 'ฉะเชิงเทรา', 'ชลบุรี', 'ชัยนาท',
        'ชัยภูมิ', 'ชุมพร', 'เชียงราย', 'เชียงใหม่', 'ตรัง',
        'ตราด', 'ตาก', 'นครนายก', 'นครปฐม', 'นครพนม',
        'นครราชสีมา', 'นครศรีธรรมราช', 'นครสวรรค์', 'นนทบุรี', 'นราธิวาส',
        'น่าน', 'บึงกาฬ', 'บุรีรัมย์', 'ปทุมธานี', 'ประจวบคีรีขันธ์',
        'ปราจีนบุรี', 'ปัตตานี', 'พระนครศรีอยุธยา', 'พังงา', 'พัทลุง',
        'พิจิตร', 'พิษณุโลก', 'เพชรบุรี', 'เพชรบูรณ์', 'แพร่',
        'พะเยา', 'ภูเก็ต', 'มหาสารคาม', 'มุกดาหาร', 'แม่ฮ่องสอน',
        'ยโสธร', 'ยะลา', 'ร้อยเอ็ด', 'ระนอง', 'ระยอง',
        'ราชบุรี', 'ลพบุรี', 'ลำปาง', 'ลำพูน', 'เลย',
        'ศรีสะเกษ', 'สกลนคร', 'สงขลา', 'สตูล', 'สมุทรปราการ',
        'สมุทรสงคราม', 'สมุทรสาคร', 'สระแก้ว', 'สระบุรี', 'สิงห์บุรี',
        'สุโขทัย', 'สุพรรณบุรี', 'สุราษฎร์ธานี', 'สุรินทร์', 'หนองคาย',
        'หนองบัวลำภู', 'อ่างทอง', 'อุดรธานี', 'อุทัยธานี', 'อุตรดิตถ์',
        'อุบลราชธานี', 'อำนาจเจริญ'
    ]