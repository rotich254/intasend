from django.contrib import admin
from .models import Payment

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'amount', 'currency', 'reference', 'status', 'created_at')
    list_filter = ('status', 'currency')
    search_fields = ('reference', 'checkout_id')
    readonly_fields = ('created_at', 'updated_at')
