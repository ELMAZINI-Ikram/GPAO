from django.contrib.auth.models import User
from core.models import UserProfile
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gpao.settings')
django.setup()

# Create default users
users = [
    ('admin', 'admin123', 'ADMIN'),
    ('operateur', 'operateur123', 'OPERATOR'),
    ('magasinier', 'magasinier123', 'STOREKEEPER'),
    ('acheteur', 'acheteur123', 'BUYER'),
    ('directeur', 'directeur123', 'DIRECTOR'),
]

for username, password, role in users:
    if not User.objects.filter(username=username).exists():
        user = User.objects.create_user(username=username, password=password)
        UserProfile.objects.create(user=user, role=role)
        print(f"Created user: {username} with role {role}")
    else:
        print(f"User {username} already exists")

print("All users created successfully!")
