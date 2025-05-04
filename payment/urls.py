from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('checkout/', views.create_checkout, name='create_checkout'),
    path('callback/', views.payment_callback, name='payment_callback'),
    path('status/<int:payment_id>/', views.payment_status, name='payment_status'),
] 