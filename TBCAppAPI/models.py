from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.

class AuthModel(AbstractUser):
    full_name = models.CharField(max_length=225)
    email = models.EmailField(unique=True)  # Use EmailField for email validation
    username = None
    phone_number = models.CharField(max_length=20, null=True, blank=True)  # Optional
    role = models.CharField(max_length=50, default='user', choices=[
        ('user', 'User'),
        ('therapist', 'Therapist'),
        ('admin', 'Admin'),
    ])

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email
    
class Therapist(models.Model):
    user = models.OneToOneField(AuthModel, on_delete=models.CASCADE, related_name="therapist_profile")
    specialty = models.CharField(max_length=255)
    bio = models.TextField(null=True, blank=True)
    years_of_experience = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.user.full_name

class Session(models.Model):
    user = models.ForeignKey(AuthModel, on_delete=models.CASCADE, related_name="sessions")
    therapist = models.ForeignKey(Therapist, on_delete=models.CASCADE, related_name="sessions")
    title = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    date = models.DateField()
    status = models.CharField(max_length=20, default='pending')
    blockchain_reference = models.CharField(max_length=64, null=True, blank=True)  # For hashes
    created_at = models.DateTimeField(auto_now_add=True)

class Payment(models.Model):
    user = models.ForeignKey(AuthModel, on_delete=models.CASCADE, related_name="payments")
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name="payments")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ], default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

