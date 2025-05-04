from django.shortcuts import render, redirect
from django.conf import settings
from django.urls import reverse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import uuid
from intasend import APIService
from .models import Payment

def home(request):
    """Home page with payment form"""
    return render(request, 'payment/home.html')

def create_checkout(request):
    """Create a checkout session with Intasend"""
    if request.method != 'POST':
        return redirect('home')
    
    try:
        amount = float(request.POST.get('amount', 0))
        if amount <= 0:
            return render(request, 'payment/home.html', {'error': 'Please enter a valid amount'})
        
        # Create a payment record
        payment = Payment.objects.create(amount=amount)
        
        # Generate a unique reference
        reference = f"payment-{uuid.uuid4().hex[:8]}"
        payment.reference = reference
        payment.save()
        
        # Initialize the Intasend API service
        service = APIService(
            publishable_key=settings.INTASEND_PUBLISHABLE_KEY,
            token=settings.INTASEND_SECRET_KEY,
            test=settings.INTASEND_TEST_MODE
        )
        
        # Create checkout using Intasend SDK
        response = service.collect.checkout(
            phone_number=request.POST.get('phone_number', ''),
            email=request.POST.get('email', ''),
            amount=amount,
            currency="KES",
            comment="Payment via Django app",
            first_name=request.POST.get('first_name', ''),
            last_name=request.POST.get('last_name', ''),
            api_ref=reference,
            redirect_url=request.build_absolute_uri(reverse('payment_callback'))
        )
        
        print(f"Checkout Response: {response}")
        
        if 'url' in response:
            payment.checkout_id = response.get('invoice', {}).get('id', '')
            payment.save()
            
            # Redirect to Intasend checkout URL
            return redirect(response.get('url'))
        else:
            error_msg = 'Failed to create payment session'
            if 'errors' in response:
                error_msg = f"API Error: {json.dumps(response['errors'])}"
            elif 'message' in response:
                error_msg = f"API Error: {response['message']}"
                
            return render(request, 'payment/home.html', {'error': error_msg})
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        return render(request, 'payment/home.html', {'error': f'Error: {str(e)}'})

@csrf_exempt
def payment_callback(request):
    """Handle the callback from Intasend after payment"""
    if request.method == 'GET':
        checkout_id = request.GET.get('invoice_id', '')
        status = request.GET.get('status', '')
        
        if not checkout_id:
            return render(request, 'payment/result.html', {'success': False, 'message': 'Invalid request'})
        
        try:
            payment = Payment.objects.get(checkout_id=checkout_id)
            
            # Initialize the Intasend API service to check status
            service = APIService(
                publishable_key=settings.INTASEND_PUBLISHABLE_KEY,
                token=settings.INTASEND_SECRET_KEY,
                test=settings.INTASEND_TEST_MODE
            )
            
            # Get payment status from Intasend
            status_response = service.collect.status(invoice_id=checkout_id)
            print(f"Status Response: {status_response}")
            
            payment_status = status_response.get('state', '').lower()
            
            if payment_status == 'complete':
                payment.status = Payment.COMPLETE
                payment.save()
                return render(request, 'payment/result.html', {
                    'success': True,
                    'message': 'Payment successful!',
                    'payment': payment
                })
            elif payment_status == 'pending':
                return render(request, 'payment/result.html', {
                    'success': False,
                    'message': 'Payment is still pending. Please check back later.',
                    'payment': payment
                })
            else:
                payment.status = Payment.FAILED
                payment.save()
                return render(request, 'payment/result.html', {
                    'success': False,
                    'message': 'Payment failed or was cancelled',
                    'payment': payment
                })
                
        except Payment.DoesNotExist:
            return render(request, 'payment/result.html', {
                'success': False,
                'message': 'Payment record not found'
            })
    
    return render(request, 'payment/result.html', {'success': False, 'message': 'Invalid request method'})

def payment_status(request, payment_id):
    """Check the status of a payment"""
    try:
        payment = Payment.objects.get(id=payment_id)
        
        # Initialize the Intasend API service
        service = APIService(
            publishable_key=settings.INTASEND_PUBLISHABLE_KEY,
            token=settings.INTASEND_SECRET_KEY,
            test=settings.INTASEND_TEST_MODE
        )
        
        # Get updated status if we have a checkout_id
        if payment.checkout_id:
            try:
                status_response = service.collect.status(invoice_id=payment.checkout_id)
                payment_status = status_response.get('state', '').lower()
                
                if payment_status == 'complete' and payment.status != Payment.COMPLETE:
                    payment.status = Payment.COMPLETE
                    payment.save()
                elif payment_status == 'failed' and payment.status != Payment.FAILED:
                    payment.status = Payment.FAILED
                    payment.save()
            except Exception as e:
                print(f"Error checking payment status: {str(e)}")
        
        return render(request, 'payment/status.html', {'payment': payment})
    except Payment.DoesNotExist:
        return redirect('home')
