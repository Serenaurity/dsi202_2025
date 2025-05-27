# CareME Django Project

## Features
- User registration and login (with Google login via django-allauth)
- Shopping cart and checkout
- PromptPay QR code payment (no external PromptPay library required)
- Shipping address collection
- Order management and order detail view

## Setup Instructions

### 1. Clone the repository
```bash
git clone <your-repo-url>
cd <your-repo-directory>
```

### 2. Install system dependencies (for Docker)
If using Docker, your Dockerfile should include:
```dockerfile
RUN apt-get update && apt-get install -y build-essential libpq-dev libjpeg-dev zlib1g-dev
```

### 3. Install Python dependencies
Install with pip:
```bash
pip install -r requirements_django.txt
```
Or for Jupyter:
```bash
pip install -r requirements_jupyter.txt
```

### 4. Run migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Create a superuser (optional)
```bash
python manage.py createsuperuser
```

### 6. Run the development server
```bash
python manage.py runserver
```

## PromptPay QR Code Payment
- The system generates a PromptPay QR code for payment using a pure Python implementation (no external PromptPay library required).
- The PromptPay ID is set to `0931307270` by default. You can change this in `myapp/services.py`.
- The QR code is compatible with all Thai banking apps.

## Troubleshooting
- **IntegrityError on checkout:** The system prevents duplicate payments for the same order.
- **TemplateDoesNotExist:** Make sure all required templates exist in `myapp/templates/myapp/`.
- **QR code not scannable:** The QR code uses a reliable payload format. Double-check your PromptPay ID and amount.
- **Dependency conflicts:** Do not pin `traitlets` or other Jupyter dependencies to specific versions unless necessary.

## Requirements
- Python 3.9+
- Django 4.2
- qrcode
- Pillow
- psycopg2-binary (for PostgreSQL)
- django-allauth, django-extensions, djangorestframework, jupyterlab, notebook (for extra features)

## License
MIT

Preview Video : https://youtu.be/RhTB0RYkl7E