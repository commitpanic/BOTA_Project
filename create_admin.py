import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bota_project.settings')
django.setup()

from accounts.models import User

# Create superuser
email = 'superadmin@bota.dev'
callsign = 'SUPERADMIN'
password = 'admin123'

# Delete if exists
User.objects.filter(email=email).delete()
User.objects.filter(callsign=callsign).delete()

# Create new superuser
user = User.objects.create_superuser(
    email=email,
    callsign=callsign,
    password=password
)

print(f"✅ Superuser created successfully!")
print(f"📧 Email: {email}")
print(f"📻 Callsign: {callsign}")
print(f"🔑 Password: {password}")
print(f"\n🔗 Login at: http://127.0.0.1:8000/admin/")
print(f"🔗 Or frontend: http://127.0.0.1:8000/login/")
