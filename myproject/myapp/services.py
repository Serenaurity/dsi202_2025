import qrcode
from io import BytesIO
from django.core.files import File
from django.utils import timezone
from datetime import timedelta
import json

# --- Reliable PromptPay QR Code Generation (from wasit7's gist) ---
def promptpay_payload(mobile_number, amount=None):
    # Convert to PromptPay format
    if mobile_number.startswith('0'):
        mobile_number = '66' + mobile_number[1:]
    # Remove any non-digit characters
    mobile_number = ''.join(filter(str.isdigit, mobile_number))
    # Build payload
    payload = (
        '000201'
        '010212'
        '29370016A000000677010111'
        f'01130066{mobile_number}'
        '5303764'
    )
    if amount:
        amt_str = f"{float(amount):.2f}"
        payload += f'540{len(amt_str):02d}{amt_str}'
    payload += '5802TH'
    # CRC16-CCITT calculation
    def crc16(payload):
        poly = 0x1021
        crc = 0xFFFF
        for c in payload:
            crc ^= ord(c) << 8
            for _ in range(8):
                if crc & 0x8000:
                    crc = (crc << 1) ^ poly
                else:
                    crc <<= 1
                crc &= 0xFFFF
        return format(crc, '04X')
    payload += '6304'
    payload += crc16(payload)
    return payload

def generate_promptpay_qr(mobile_number, amount=None):
    payload = promptpay_payload(mobile_number, amount)
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(payload)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    return img, payload

class PaymentService:
    @staticmethod
    def generate_promptpay_qr(amount, reference1, reference2=None):
        promptpay_id = '0931307270'
        img, payload = generate_promptpay_qr(promptpay_id, amount)
        return img, payload
    
    @staticmethod
    def generate_qr_code(qr_string):
        """Generate QR code image from string"""
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_string)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        return buffer
    
    @staticmethod
    def create_payment(order, payment_method):
        """Create a new payment and QR code"""
        from .models import Payment, QRCodePayment
        
        payment, created = Payment.objects.get_or_create(
            order=order,
            defaults={
                'amount': order.total_amount,
                'payment_method': payment_method,
                'status': 'pending'
            }
        )
        
        qr_payment = getattr(payment, 'qrcode', None)
        if qr_payment is None:
            img, qr_string = PaymentService.generate_promptpay_qr(
                amount=order.total_amount,
                reference1=order.order_number
            )
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            buffer.seek(0)
            qr_payment = QRCodePayment.objects.create(
                payment=payment,
                qr_string=qr_string,
                expires_at=timezone.now() + timedelta(minutes=15)  # QR code expires in 15 minutes
            )
            qr_payment.qr_code.save(
                f'qrcode_{order.order_number}.png',
                File(buffer),
                save=True
            )
        
        return payment, qr_payment
    
    @staticmethod
    def verify_payment(payment_id):
        """Verify payment status (mock implementation)"""
        from .models import Payment
        
        payment = Payment.objects.get(id=payment_id)
        # In production, implement actual payment verification logic here
        # For now, we'll just mark it as completed
        payment.status = 'completed'
        payment.save()
        
        # Update order status
        payment.order.status = 'paid'
        payment.order.save()
        
        return payment 