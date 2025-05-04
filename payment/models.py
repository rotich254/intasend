from django.db import models

# Create your models here.

class Payment(models.Model):
    PENDING = 'pending'
    COMPLETE = 'complete'
    FAILED = 'failed'
    
    STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (COMPLETE, 'Complete'),
        (FAILED, 'Failed'),
    ]
    
    MPESA = 'mpesa'
    CARD = 'card'
    GOOGLE_PAY = 'google_pay'
    BANK = 'bank'
    OTHER = 'other'
    UNKNOWN = 'unknown'
    
    PAYMENT_METHOD_CHOICES = [
        (MPESA, 'M-Pesa'),
        (CARD, 'Card Payment'),
        (GOOGLE_PAY, 'Google Pay'),
        (BANK, 'Bank Transfer'),
        (OTHER, 'Other Method'),
        (UNKNOWN, 'Unknown Method'),
    ]
    
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='KES')
    reference = models.CharField(max_length=100, blank=True)
    checkout_id = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=PENDING)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default=UNKNOWN)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    payer_phone = models.CharField(max_length=20, blank=True, null=True)
    payer_email = models.EmailField(blank=True, null=True)
    payer_name = models.CharField(max_length=255, blank=True, null=True)
    
    def __str__(self):
        return f"Payment of {self.amount} {self.currency} ({self.status})"
