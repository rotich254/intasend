# Intasend Payment Gateway Integration

A simple Django web application that integrates with Intasend payment gateway to accept payments through M-Pesa, card, and other payment methods.

## Features

- Simple payment form to collect amount and customer details
- Integration with Intasend checkout API
- Support for multiple payment methods (M-Pesa, card, etc.)
- Payment status tracking
- Callback handling

## Setup Instructions

1. Clone the repository
2. Install the required packages:
```
pip install -r requirements.txt
```
3. Set up your Intasend API keys in `intasend_payment/settings.py`:
```python
INTASEND_PUBLISHABLE_KEY = 'your_publishable_key'
INTASEND_SECRET_KEY = 'your_secret_key'
INTASEND_TEST_MODE = True  # Set to False for production
```
4. Run migrations:
```
python manage.py makemigrations
python manage.py migrate
```
5. Create a superuser for the admin panel:
```
python manage.py createsuperuser
```
6. Run the development server:
```
python manage.py runserver
```
7. Access the application at http://127.0.0.1:8000/

## Intasend API Keys

To get API keys:
1. Sign up for an [Intasend account](https://intasend.com/)
2. Go to Developer > API Keys in your dashboard
3. Create new API keys or use the sandbox keys for testing

## Usage

1. Enter the payment amount and customer details in the form
2. Click "Proceed to Payment"
3. Complete the payment on the Intasend checkout page
4. You will be redirected back to the application with the payment result

## Admin Interface

Access the admin interface at http://127.0.0.1:8000/admin/ to view and manage payment records.

## Testing

You can use Intasend's test mode to simulate payments without real money transactions. 