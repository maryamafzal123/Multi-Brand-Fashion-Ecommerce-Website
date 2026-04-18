from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra):
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra):
        extra.setdefault('is_staff', True)
        extra.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra)

class User(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = [('customer', 'Customer'), ('admin', 'Admin')]

    email      = models.EmailField(unique=True)
    full_name  = models.CharField(max_length=150)
    phone      = models.CharField(max_length=20, blank=True)
    role       = models.CharField(max_length=20, choices=ROLE_CHOICES, default='customer')
    is_active  = models.BooleanField(default=True)
    is_staff   = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = UserManager()
    USERNAME_FIELD  = 'email'
    REQUIRED_FIELDS = ['full_name']

    def __str__(self):
        return self.email

class Address(models.Model):
    user        = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')
    label       = models.CharField(max_length=50, default='Home')
    street      = models.TextField()
    city        = models.CharField(max_length=100)
    province    = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20, blank=True)
    is_default  = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.email} — {self.label}"