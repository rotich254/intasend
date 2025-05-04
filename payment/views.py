from django.shortcuts import render, redirect
from django.conf import settings
from django.urls import reverse
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login, authenticate
from django.contrib import messages
from django.db.models import Sum
import json
import uuid
import logging
import csv
from datetime import datetime, timedelta
from intasend import APIService
from .models import Payment

# Set up logging
logger = logging.getLogger(__name__)

# Custom decorator for payment-specific features
def payment_login_required(function):
    """Custom login required decorator that adds a payment-specific message"""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.info(request, "You need to login to access payment details and reports.")
            return redirect(f"{settings.LOGIN_URL}?next={request.path}")
        return function(request, *args, **kwargs)
    return wrapper

def home(request):
    """Home page with payment form"""
    sandbox_message = "Using Intasend SANDBOX mode - no real payments will be processed" if settings.INTASEND_TEST_MODE else ""
    return render(request, 'payment/home.html', {'sandbox_message': sandbox_message})

def register(request):
    """User registration view"""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            login(request, user)
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(request, 'payment/register.html', {'form': form})

def create_checkout(request):
    """Create a checkout session with Intasend"""
    if request.method != 'POST':
        return redirect('home')
    
    try:
        amount = float(request.POST.get('amount', 0))
        if amount <= 0:
            return render(request, 'payment/home.html', {'error': 'Please enter a valid amount'})
        
        # Log the payment attempt
        logger.info(f"Processing payment attempt for amount: {amount}")
        logger.info(f"Using TEST MODE: {settings.INTASEND_TEST_MODE}")
        
        # Create a payment record
        payment = Payment.objects.create(
            amount=amount,
            payer_phone=request.POST.get('phone_number', ''),
            payer_email=request.POST.get('email', ''),
            payer_name=f"{request.POST.get('first_name', '')} {request.POST.get('last_name', '')}".strip()
        )
        
        # Generate a unique reference
        reference = f"payment-{uuid.uuid4().hex[:8]}"
        payment.reference = reference
        payment.save()
        
        logger.info(f"Created payment record with reference: {reference}")
        
        # Initialize the Intasend API service
        service = APIService(
            publishable_key=settings.INTASEND_PUBLISHABLE_KEY,
            token=settings.INTASEND_SECRET_KEY,
            test=settings.INTASEND_TEST_MODE
        )
        
        # Gather customer information
        phone_number = request.POST.get('phone_number', '')
        email = request.POST.get('email', '')
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        
        # Ensure phone number has country code for sandbox
        if settings.INTASEND_TEST_MODE and phone_number and not phone_number.startswith('+'):
            if not phone_number.startswith('254'):
                phone_number = '254' + phone_number.lstrip('0')
                logger.info(f"Formatted phone number for sandbox: {phone_number}")
        
        # Log API call details
        logger.info(f"Calling Intasend API with: phone={phone_number}, email={email}, amount={amount}, reference={reference}")
        
        # Create checkout using Intasend SDK
        response = service.collect.checkout(
            phone_number=phone_number,
            email=email,
            amount=amount,
            currency="KES",
            comment="Payment via Django app",
            first_name=first_name,
            last_name=last_name,
            api_ref=reference,
            redirect_url=request.build_absolute_uri(reverse('payment_callback'))
        )
        
        # Log the full response for debugging
        logger.info(f"Checkout Response: {json.dumps(response, default=str)}")
        
        if 'url' in response:
            # Get the invoice ID from the response
            invoice_id = None
            if 'invoice' in response and isinstance(response['invoice'], dict):
                invoice_id = response['invoice'].get('id', '')
            elif 'id' in response:
                invoice_id = response.get('id')
                
            if invoice_id:
                payment.checkout_id = invoice_id
                payment.save()
                logger.info(f"Payment checkout created successfully: {invoice_id}")
            else:
                logger.warning("No invoice ID found in response, using reference as checkout_id")
                payment.checkout_id = reference
                payment.save()
            
            # Redirect to Intasend checkout URL
            return redirect(response.get('url'))
        else:
            error_msg = 'Failed to create payment session'
            if 'errors' in response:
                error_msg = f"API Error: {json.dumps(response['errors'])}"
            elif 'message' in response:
                error_msg = f"API Error: {response['message']}"
            elif isinstance(response, dict):
                error_msg = f"API Error: {json.dumps(response)}"
                
            logger.error(f"Payment creation failed: {error_msg}")
            return render(request, 'payment/home.html', {'error': error_msg})
            
    except Exception as e:
        import traceback
        error = f"Error: {str(e)}"
        logger.error(f"Exception in payment processing: {error}")
        logger.error(traceback.format_exc())
        return render(request, 'payment/home.html', {'error': error})

@csrf_exempt
def payment_callback(request):
    """Handle the callback from Intasend after payment"""
    logger.info(f"Payment callback received: {request.method}")
    logger.info(f"Callback GET parameters: {request.GET}")
    logger.info(f"Callback POST parameters: {request.POST}")
    
    if request.method == 'GET' or request.method == 'POST':
        # Check for different possible parameter names in both GET and POST
        checkout_id = request.GET.get('invoice_id', '') or request.POST.get('invoice_id', '')
        if not checkout_id:
            checkout_id = request.GET.get('id', '') or request.POST.get('id', '')
        if not checkout_id:
            checkout_id = request.GET.get('checkout_id', '') or request.POST.get('checkout_id', '')
            
        status = request.GET.get('status', '') or request.POST.get('status', '')
        if not status:
            status = request.GET.get('state', '') or request.POST.get('state', '')
            
        logger.info(f"Processing callback for checkout ID: {checkout_id}, status: {status}")
        
        # Handle sandbox mode - in sandbox, we'll simulate a successful payment
        # if no clear status is provided
        if settings.INTASEND_TEST_MODE and not status:
            logger.info("Sandbox mode: simulating successful payment")
            status = 'SUCCESS'
        
        # If we still don't have a checkout ID, check if we can find a payment by reference
        if not checkout_id:
            reference = request.GET.get('reference', '') or request.POST.get('reference', '')
            if reference:
                try:
                    payment = Payment.objects.filter(reference=reference).first()
                    if payment:
                        checkout_id = payment.checkout_id or reference
                        logger.info(f"Found payment by reference: {reference}, using checkout_id: {checkout_id}")
                except Exception as e:
                    logger.error(f"Error finding payment by reference: {str(e)}")
        
        if not checkout_id:
            logger.error("Invalid callback: No checkout ID provided")
            return render(request, 'payment/result.html', {
                'success': False, 
                'message': 'Invalid request - missing checkout ID'
            })
        
        try:
            # Try to find the payment record
            payment = None
            try:
                payment = Payment.objects.get(checkout_id=checkout_id)
                logger.info(f"Found payment record by checkout_id: {payment.id}")
            except Payment.DoesNotExist:
                # Try to find by reference if checkout_id lookup fails
                try:
                    payment = Payment.objects.filter(reference=checkout_id).first()
                    if payment:
                        logger.info(f"Found payment record by reference: {payment.id}")
                except Exception:
                    pass
            
            if not payment:
                logger.error(f"Payment record not found for checkout ID: {checkout_id}")
                return render(request, 'payment/result.html', {
                    'success': False,
                    'message': f'Payment record not found for ID: {checkout_id}'
                })
            
            # Initialize the Intasend API service to check status
            service = APIService(
                publishable_key=settings.INTASEND_PUBLISHABLE_KEY,
                token=settings.INTASEND_SECRET_KEY,
                test=settings.INTASEND_TEST_MODE
            )
            
            payment_status = None
            payment_method = Payment.UNKNOWN
            
            # Get payment status from Intasend
            try:
                logger.info(f"Checking payment status with Intasend for invoice ID: {checkout_id}")
                status_response = service.collect.status(invoice_id=checkout_id)
                logger.info(f"Status Response: {json.dumps(status_response, default=str)}")
                
                # Extract payment status - handle different response formats
                if 'state' in status_response:
                    payment_status = status_response.get('state', '').lower()
                elif 'status' in status_response:
                    payment_status = status_response.get('status', '').lower()
                
                # Try to extract payment method from response
                if 'payment_method' in status_response:
                    method = status_response.get('payment_method', '').lower()
                    if 'mpesa' in method:
                        payment_method = Payment.MPESA
                    elif 'card' in method or 'visa' in method or 'mastercard' in method:
                        payment_method = Payment.CARD
                    elif 'google' in method or 'gpay' in method:
                        payment_method = Payment.GOOGLE_PAY
                    elif 'bank' in method:
                        payment_method = Payment.BANK
                    else:
                        payment_method = Payment.OTHER
                
                # Alternatively check channel info
                elif 'channel' in status_response:
                    channel = status_response.get('channel', '').lower()
                    if 'mpesa' in channel:
                        payment_method = Payment.MPESA
                    elif 'card' in channel or 'visa' in channel or 'mastercard' in channel:
                        payment_method = Payment.CARD
                    elif 'google' in channel:
                        payment_method = Payment.GOOGLE_PAY
                    elif 'bank' in channel:
                        payment_method = Payment.BANK
                    else:
                        payment_method = Payment.OTHER
                
                # Check if provider field exists and contains card info
                elif 'provider' in status_response:
                    provider = status_response.get('provider', '').lower()
                    if 'mpesa' in provider:
                        payment_method = Payment.MPESA
                    elif 'card' in provider or 'visa' in provider or 'mastercard' in provider:
                        payment_method = Payment.CARD
                    elif 'google' in provider:
                        payment_method = Payment.GOOGLE_PAY
                    elif 'bank' in provider:
                        payment_method = Payment.BANK
                    else:
                        payment_method = Payment.OTHER
                
                # Direct check for card payment indicators in any field
                else:
                    for key, value in status_response.items():
                        if isinstance(value, str):
                            value_lower = value.lower()
                            if 'card' in value_lower or 'visa' in value_lower or 'mastercard' in value_lower:
                                payment_method = Payment.CARD
                                break
                            elif 'mpesa' in value_lower:
                                payment_method = Payment.MPESA
                                break
                            elif 'google' in value_lower or 'gpay' in value_lower:
                                payment_method = Payment.GOOGLE_PAY
                                break
                
            except Exception as e:
                logger.error(f"Error getting status from API: {str(e)}")
            
            logger.info(f"Detected payment status from API: {payment_status}")
            logger.info(f"Detected payment method: {payment_method}")
            
            # If no status from API, use the one from URL parameters
            if not payment_status and status:
                payment_status = status.lower()
                logger.info(f"Using status from URL: {payment_status}")
            
            # Handle sandbox mode with missing status
            if settings.INTASEND_TEST_MODE and not payment_status:
                logger.info("Sandbox mode: No status detected, simulating success")
                payment_status = 'success'
            
            # Update payment method
            payment.payment_method = payment_method
            
            if payment_status in ['complete', 'success', 'paid']:
                payment.status = Payment.COMPLETE
                # Set completion timestamp
                import datetime
                payment.completed_at = datetime.datetime.now()
                payment.save()
                logger.info(f"Payment marked as COMPLETE")
                return render(request, 'payment/result.html', {
                    'success': True,
                    'message': 'Payment successful!',
                    'payment': payment
                })
            elif payment_status in ['pending', 'processing']:
                logger.info(f"Payment is still PENDING")
                return render(request, 'payment/result.html', {
                    'success': False,
                    'message': 'Payment is still pending. Please check back later.',
                    'payment': payment
                })
            else:
                payment.status = Payment.FAILED
                payment.save()
                logger.info(f"Payment marked as FAILED")
                return render(request, 'payment/result.html', {
                    'success': False,
                    'message': f'Payment failed or was cancelled. Status: {payment_status}',
                    'payment': payment
                })
                
        except Exception as e:
            logger.error(f"Error processing callback: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return render(request, 'payment/result.html', {
                'success': False,
                'message': f'Error processing payment: {str(e)}'
            })
    
    logger.warning(f"Invalid callback request method: {request.method}")
    return render(request, 'payment/result.html', {'success': False, 'message': 'Invalid request method'})

@payment_login_required
def payment_status(request, payment_id):
    """Check the status of a payment"""
    try:
        payment = Payment.objects.get(id=payment_id)
        logger.info(f"Checking status for payment ID: {payment_id}")
        
        # Handle sandbox mode - in sandbox, if status is still pending after some time, 
        # we'll simulate a successful payment
        if settings.INTASEND_TEST_MODE and payment.status == Payment.PENDING:
            import datetime
            # If payment is older than 1 minute, consider it successful in sandbox
            time_threshold = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=1)
            if payment.created_at < time_threshold:
                logger.info(f"Sandbox mode: Simulating success for older pending payment")
                payment.status = Payment.COMPLETE
                payment.save()
                return render(request, 'payment/status.html', {'payment': payment, 'sandbox_mode': True})
        
        # Initialize the Intasend API service
        service = APIService(
            publishable_key=settings.INTASEND_PUBLISHABLE_KEY,
            token=settings.INTASEND_SECRET_KEY,
            test=settings.INTASEND_TEST_MODE
        )
        
        # Get updated status if we have a checkout_id
        if payment.checkout_id:
            try:
                logger.info(f"Checking payment status with Intasend for checkout ID: {payment.checkout_id}")
                status_response = service.collect.status(invoice_id=payment.checkout_id)
                logger.info(f"Status Response: {json.dumps(status_response, default=str)}")
                
                payment_status = None
                if 'state' in status_response:
                    payment_status = status_response.get('state', '').lower()
                elif 'status' in status_response:
                    payment_status = status_response.get('status', '').lower()
                    
                logger.info(f"Detected payment status: {payment_status}")
                
                # Update payment method if still unknown or if we have better information
                if payment.payment_method == Payment.UNKNOWN:
                    payment_method = Payment.UNKNOWN
                    
                    # Try to extract payment method from response
                    if 'payment_method' in status_response:
                        method = status_response.get('payment_method', '').lower()
                        if 'mpesa' in method:
                            payment_method = Payment.MPESA
                        elif 'card' in method:
                            payment_method = Payment.CARD
                        elif 'google' in method or 'gpay' in method:
                            payment_method = Payment.GOOGLE_PAY
                        elif 'bank' in method:
                            payment_method = Payment.BANK
                        else:
                            payment_method = Payment.OTHER
                    
                    # Alternatively check channel info
                    elif 'channel' in status_response:
                        channel = status_response.get('channel', '').lower()
                        if 'mpesa' in channel:
                            payment_method = Payment.MPESA
                        elif 'card' in channel:
                            payment_method = Payment.CARD
                        elif 'google' in channel:
                            payment_method = Payment.GOOGLE_PAY
                        elif 'bank' in channel:
                            payment_method = Payment.BANK
                        else:
                            payment_method = Payment.OTHER
                    
                    # Check if provider field exists and contains card info
                    elif 'provider' in status_response:
                        provider = status_response.get('provider', '').lower()
                        if 'mpesa' in provider:
                            payment_method = Payment.MPESA
                        elif 'card' in provider or 'visa' in provider or 'mastercard' in provider:
                            payment_method = Payment.CARD
                        elif 'google' in provider:
                            payment_method = Payment.GOOGLE_PAY
                        elif 'bank' in provider:
                            payment_method = Payment.BANK
                        
                    # If we determined a payment method, update it
                    if payment_method != Payment.UNKNOWN:
                        logger.info(f"Updating payment method to: {payment_method}")
                        payment.payment_method = payment_method
                        payment.save()
                
                if payment_status in ['complete', 'success', 'paid']:
                    if payment.status != Payment.COMPLETE:
                        payment.status = Payment.COMPLETE
                        payment.save()
                        logger.info(f"Updated payment to COMPLETE")
                elif payment_status in ['failed', 'cancelled', 'rejected']:
                    if payment.status != Payment.FAILED:
                        payment.status = Payment.FAILED
                        payment.save()
                        logger.info(f"Updated payment to FAILED")
            except Exception as e:
                logger.error(f"Error checking payment status: {str(e)}")
        
        return render(request, 'payment/status.html', {'payment': payment, 'sandbox_mode': settings.INTASEND_TEST_MODE})
    except Payment.DoesNotExist:
        logger.error(f"Payment record not found for ID: {payment_id}")
        return redirect('home')

@payment_login_required
def payment_reports(request):
    """View for displaying and filtering payment reports"""
    # Get filter parameters
    status = request.GET.get('status', '')
    payment_method = request.GET.get('payment_method', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    search = request.GET.get('search', '')
    
    # Base queryset
    payments = Payment.objects.all().order_by('-created_at')
    
    # Apply filters
    if status:
        payments = payments.filter(status=status)
    
    if payment_method:
        payments = payments.filter(payment_method=payment_method)
    
    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
            payments = payments.filter(created_at__gte=date_from_obj)
        except (ValueError, TypeError):
            pass
    
    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d')
            # Add one day to include the end date in the range
            date_to_obj = date_to_obj + timedelta(days=1)
            payments = payments.filter(created_at__lt=date_to_obj)
        except (ValueError, TypeError):
            pass
    
    if search:
        payments = payments.filter(reference__icontains=search) | payments.filter(checkout_id__icontains=search)
    
    # Calculate statistics
    total_payments = payments.count()
    successful_payments = payments.filter(status=Payment.COMPLETE).count()
    pending_payments = payments.filter(status=Payment.PENDING).count()
    failed_payments = payments.filter(status=Payment.FAILED).count()
    
    total_amount = payments.filter(status=Payment.COMPLETE).aggregate(Sum('amount'))['amount__sum'] or 0
    
    # Calculate success rate and average transaction
    success_rate = 0
    avg_transaction = 0
    
    if total_payments > 0:
        success_rate = int((successful_payments / total_payments) * 100)
    
    if successful_payments > 0:
        avg_transaction = float(total_amount) / successful_payments
    
    # Last 7 days stats
    seven_days_ago = datetime.now() - timedelta(days=7)
    payments_7days = payments.filter(created_at__gte=seven_days_ago)
    total_7days = payments_7days.filter(status=Payment.COMPLETE).aggregate(Sum('amount'))['amount__sum'] or 0
    count_7days = payments_7days.filter(status=Payment.COMPLETE).count()
    
    # Check if export to CSV is requested
    if request.GET.get('export') == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="payments-report-{datetime.now().strftime("%Y%m%d")}.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Reference', 'Amount', 'Currency', 'Method', 'Status', 'Created Date', 'Completed Date', 'Customer'])
        
        for payment in payments:
            writer.writerow([
                payment.reference,
                payment.amount,
                payment.currency,
                payment.get_payment_method_display(),
                payment.get_status_display(),
                payment.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                payment.completed_at.strftime('%Y-%m-%d %H:%M:%S') if payment.completed_at else 'N/A',
                payment.payer_name or payment.payer_email or payment.payer_phone or 'Unknown'
            ])
        
        return response
    
    # Prepare context with filters and statistics
    context = {
        'payments': payments,
        'filters': {
            'status': status,
            'payment_method': payment_method,
            'date_from': date_from,
            'date_to': date_to,
            'search': search,
        },
        'stats': {
            'total_payments': total_payments,
            'successful_payments': successful_payments,
            'pending_payments': pending_payments,
            'failed_payments': failed_payments,
            'total_amount': total_amount,
            'total_7days': total_7days,
            'count_7days': count_7days,
            'success_rate': success_rate,
            'avg_transaction': avg_transaction,
        }
    }
    
    return render(request, 'payment/reports.html', context)
