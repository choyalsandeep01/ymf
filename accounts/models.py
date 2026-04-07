from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_CHOICES = [
        ('USER', 'User'),
        ('VOLUNTEER', 'Volunteer'),
        ('ADMIN', 'Admin'),
    ]
    
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='USER')
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    profile_pic = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
    
    def is_admin_role(self):
        return self.role == 'ADMIN' or self.is_superuser
    
    def is_volunteer_role(self):
        return self.role == 'VOLUNTEER' or self.is_admin_role()
    
    def is_user_role(self):
        return self.role == 'USER'
