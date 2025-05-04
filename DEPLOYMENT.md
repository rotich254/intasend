# Deployment Guide

This guide outlines the steps to deploy the Intasend Payment Gateway Integration to a production environment.

## Prerequisites

- Python 3.11 or higher
- PostgreSQL database (We're using Neon for this project)
- A web server (like Nginx or Apache)
- A domain name (optional but recommended)

## Environment Variables

Make sure to set the following environment variables on your production server:

```
SECRET_KEY=your_secret_key_here
INTASEND_PUBLISHABLE_KEY=your_intasend_publishable_key
INTASEND_SECRET_KEY=your_intasend_secret_key
INTASEND_TEST_MODE=False  # Set to False for production
DATABASE_URL=your_database_url
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
```

## Deployment Steps

### 1. Clone the repository

```bash
git clone [your-repository-url]
cd intasend-payment
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Setup for Production

Run the custom management command to set up for production:

```bash
python manage.py setup_production
```

This will:
- Collect static files
- Apply database migrations
- Check for potential deployment issues

### 4. Using a WSGI Server (Gunicorn)

Gunicorn is included in the requirements. You can start the server using:

```bash
gunicorn intasend_payment.wsgi:application
```

For production, we recommend using a process manager like Supervisor to keep the application running.

### 5. Setting up Nginx (recommended)

Here's a basic Nginx configuration:

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    location = /favicon.ico { access_log off; log_not_found off; }
    
    location /static/ {
        root /path/to/your/project;
    }

    location / {
        include proxy_params;
        proxy_pass http://127.0.0.1:8000;
    }
}
```

### 6. HTTPS Configuration (strongly recommended)

For payment systems, HTTPS is crucial. Use Let's Encrypt for free SSL certificates:

```bash
sudo apt-get install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

### 7. Security Considerations

- Make sure DEBUG is set to False in production
- Use strong, unique passwords for the database
- Regularly update your packages for security patches
- Consider using a web application firewall (WAF)

## Heroku Deployment

This project is Heroku-ready. To deploy to Heroku:

1. Create a new Heroku app
2. Add the PostgreSQL add-on
3. Set all required environment variables in Heroku
4. Deploy using Git:

```bash
heroku git:remote -a your-heroku-app-name
git push heroku master
```

## Neon Database

The project is configured to use Neon PostgreSQL. Make sure your DATABASE_URL environment variable is set correctly.

## Troubleshooting

If you encounter issues with database connections, check:
- If your database credentials are correct
- Network connectivity between your server and database
- Firewall settings that might block database connections

For any other issues, refer to the debug logs or contact the development team. 