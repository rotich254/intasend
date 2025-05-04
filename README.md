# Intasend Payment Gateway Integration

A simple Django web application that integrates with Intasend payment gateway to accept payments through M-Pesa, card, and other payment methods.

## Live Demo

The application is deployed and available at: [https://intasend.onrender.com/](https://intasend.onrender.com/)

### Demo Credentials
- To view reports: Create an account through the registration page
- For test payments: Use the sandbox testing information provided on the homepage

## Features

- Simple payment form to collect amount and customer details
- Integration with Intasend checkout API
- Support for multiple payment methods (M-Pesa, card, Google Pay)
- Payment status tracking
- Callback handling
- Payment reports and analytics dashboard
- User registration and authentication
- CSV export for payment data

## Setup Instructions

1. Clone the repository
```
git clone https://github.com/rotich254/intasend.git
cd intasend
```

2. Install the required packages:
```
pip install -r requirements.txt
```

3. Set up your Intasend API keys in `.environment` file:
```
INTASEND_PUBLISHABLE_KEY=your_publishable_key
INTASEND_SECRET_KEY=your_secret_key
INTASEND_TEST_MODE=True  # Set to False for production
```

4. Run migrations:
```
python manage.py makemigrations
python manage.py migrate
```

5. Create a superuser for the admin panel and reports access:
```
python manage.py createsuperuser
```

6. Run the development server:
```
python manage.py runserver
```

7. Access the application at http://127.0.0.1:8000/

## Deployment

This application is deployed on Render. See the detailed deployment guides:
- [RENDER_FREE_DEPLOY.md](RENDER_FREE_DEPLOY.md) - For deploying on Render's free tier
- [RENDER_DEPLOYMENT.md](RENDER_DEPLOYMENT.md) - For deploying with a PostgreSQL database
- [DEPLOYMENT.md](DEPLOYMENT.md) - General deployment instructions

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

## Reports Dashboard

To access the payment reports:
1. Log in using the account you created
2. Navigate to the Reports page from the navigation menu
3. View payment statistics and transaction history
4. Filter reports by date, status, and payment method
5. Export data to CSV for further analysis

## Admin Interface

Access the admin interface at http://127.0.0.1:8000/admin/ (or https://intasend.onrender.com/admin/ on the live site) to view and manage payment records.

## Testing

You can use Intasend's test mode to simulate payments without real money transactions:
- For M-Pesa test payments, use the PIN **0000** when prompted
- For card payments, use test cards like:
  - Card number: 4242 4242 4242 4242
  - Expiry date: Any future date
  - CVV: Any 3 digits

## Technologies Used

- Django 5.0+
- Bootstrap 5
- SQLite (development) / PostgreSQL (production option)
- Intasend Python SDK
- Gunicorn (WSGI server)
- Whitenoise (static files) 