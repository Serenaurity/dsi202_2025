# myapp/utils/payment.py
import qrcode
import promptpay
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from django.core.files.base import ContentFile
from decimal import Decimal
import os


class PromptPayQRGenerator:
    """สร้าง QR Code สำหรับ PromptPay"""
    
    def __init__(self, promptpay_id, amount=None):
        self.promptpay_id = promptpay_id
        self.amount = amount
    
    def generate_payload(self):
        """สร้าง PromptPay payload"""
        if self.amount:
            # QR Code แบบระบุจำนวนเงิน
            return promptpay.qrcode.generate_payload(
                self.promptpay_id, 
                float(self.amount)
            )
        else:
            # QR Code แบบไม่ระบุจำนวนเงิน
            return promptpay.qrcode.generate_payload(self.promptpay_id)
    
    def create_qr_code(self, logo_path=None):
        """สร้าง QR Code image"""
        # สร้าง QR Code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )
        
        # เพิ่ม payload
        payload = self.generate_payload()
        qr.add_data(payload)
        qr.make(fit=True)
        
        # สร้างรูป QR Code
        img = qr.make_image(fill_color="black", back_color="white")
        
        # ถ้ามี logo ให้ใส่ตรงกลาง
        if logo_path and os.path.exists(logo_path):
            img = self._add_logo(img, logo_path)
        
        return img
    
    def _add_logo(self, qr_img, logo_path):
        """เพิ่ม logo ตรงกลาง QR Code"""
        logo = Image.open(logo_path)
        
        # คำนวณขนาด logo (20% ของ QR Code)
        qr_width, qr_height = qr_img.size
        logo_size = min(qr_width, qr_height) // 5
        
        # ปรับขนาด logo
        logo = logo.resize((logo_size, logo_size), Image.Resampling.LANCZOS)
        
        # สร้างพื้นหลังสีขาวสำหรับ logo
        logo_bg = Image.new('RGB', (logo_size + 20, logo_size + 20), 'white')
        logo_bg.paste(logo, (10, 10))
        
        # วาง logo ตรงกลาง QR Code
        logo_pos = (
            (qr_width - logo_bg.width) // 2,
            (qr_height - logo_bg.height) // 2
        )
        qr_img.paste(logo_bg, logo_pos)
        
        return qr_img
    
    def create_payment_qr(self, order_number, recipient_name):
        """สร้าง QR Code พร้อมข้อมูลการชำระเงิน"""
        # สร้าง QR Code
        qr_img = self.create_qr_code()
        
        # เพิ่มพื้นที่สำหรับข้อความ
        width, height = qr_img.size
        new_height = height + 200
        
        # สร้างรูปใหม่
        final_img = Image.new('RGB', (width, new_height), 'white')
        final_img.paste(qr_img, (0, 0))
        
        # เพิ่มข้อความ
        draw = ImageDraw.Draw(final_img)
        
        # ใช้ font เริ่มต้น
        try:
            # พยายามใช้ font ภาษาไทย
            font_large = ImageFont.truetype("/usr/share/fonts/truetype/tlwg/Sarabun-Bold.ttf", 24)
            font_normal = ImageFont.truetype("/usr/share/fonts/truetype/tlwg/Sarabun.ttf", 18)
        except:
            # ใช้ font เริ่มต้นถ้าไม่มี
            font_large = ImageFont.load_default()
            font_normal = ImageFont.load_default()
        
        # ข้อความ
        text_y = height + 20
        
        # หัวข้อ
        title = "สแกนเพื่อชำระเงิน"
        draw.text((width//2, text_y), title, font=font_large, anchor="mt", fill="black")
        
        # ชื่อผู้รับเงิน
        text_y += 40
        draw.text((width//2, text_y), f"ผู้รับ: {recipient_name}", font=font_normal, anchor="mt", fill="black")
        
        # จำนวนเงิน
        if self.amount:
            text_y += 30
            draw.text((width//2, text_y), f"จำนวน: {self.amount:,.2f} บาท", font=font_normal, anchor="mt", fill="black")
        
        # หมายเลขคำสั่งซื้อ
        text_y += 30
        draw.text((width//2, text_y), f"Order: {order_number}", font=font_normal, anchor="mt", fill="black")
        
        # คำเตือน
        text_y += 40
        warning = "โปรดตรวจสอบจำนวนเงินก่อนชำระ"
        draw.text((width//2, text_y), warning, font=font_normal, anchor="mt", fill="red")
        
        return final_img
    
    def save_to_field(self, order_number, recipient_name):
        """บันทึก QR Code เป็น Django ImageField"""
        img = self.create_payment_qr(order_number, recipient_name)
        
        # แปลงเป็น bytes
        img_io = BytesIO()
        img.save(img_io, format='PNG')
        img_file = ContentFile(img_io.getvalue())
        
        # ตั้งชื่อไฟล์
        filename = f"promptpay_qr_{order_number}.png"
        
        return filename, img_file


def calculate_shipping_fee(shipping_method, items):
    """คำนวณค่าจัดส่ง"""
    base_fee = shipping_method.base_fee
    
    # คำนวณน้ำหนักรวม (สมมติว่ามีฟิลด์ weight ใน Product)
    total_weight = sum(item.quantity for item in items)  # kg
    
    # ค่าจัดส่งเพิ่มเติมตามน้ำหนัก
    if total_weight > 5:
        additional_fee = (total_weight - 5) * 10  # 10 บาทต่อกิโลกรัม
    else:
        additional_fee = 0
    
    return Decimal(base_fee + additional_fee)