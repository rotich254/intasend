# Deploying to Render

This guide covers the specific steps needed to deploy your Intasend Payment Integration on Render.

## Option 1: Using the Render Blueprint (Recommended)

The easiest way to deploy is using the Render Blueprint configuration (render.yaml) included in this repository.

1. **Create a Render account** if you don't have one at [render.com](https://render.com)

2. **Deploy using the Blueprint**:
   - From your Render dashboard, click "New" and select "Blueprint"
   - Connect your GitHub/GitLab repository that contains this code
   - Render will automatically detect the `render.yaml` file and set up:
     - A web service for your application
     - A PostgreSQL database
   
3. **Set the remaining environment variables**:
   After deployment, go to your web service in the Render dashboard and add these environment variables:
   - `INTASEND_PUBLISHABLE_KEY`: Your Intasend publishable key
   - `INTASEND_SECRET_KEY`: Your Intasend secret key
   - `INTASEND_TEST_MODE`: Set to "False" for production (use strings "True" or "False")

4. **Run database migrations**:
   Go to your web service in the Render dashboard and use the Shell option to run:
   ```
   python manage.py migrate
   ```

5. **Create a superuser** (optional):
   ```
   python manage.py createsuperuser
   ```

## Option 2: Manual Setup

If you prefer manual setup instead of using the Blueprint:

1. **Create a PostgreSQL database** on Render:
   - Go to the Render dashboard and select "New" > "PostgreSQL"
   - Set a name for your database
   - Note the Internal Database URL shown after creation

2. **Create a Web Service**:
   - In the Render dashboard, click "New" > "Web Service"
   - Connect to your repository
   - Set the following:
     - Environment: Python
     - Build Command: `pip install -r requirements.txt`
     - Start Command: `gunicorn intasend_payment.wsgi:application`
     - Select the appropriate Python version (3.11)

3. **Configure environment variables**:
   - In the Environment section, add the following variables:
     - `DATABASE_URL`: The Internal Database URL from step 1
     - `SECRET_KEY`: Generate a secure random key
     - `DEBUG`: "False"
     - `ALLOWED_HOSTS`: "yourdomain.onrender.com" (replace with your actual Render URL)
     - `INTASEND_PUBLISHABLE_KEY`: Your Intasend publishable key
     - `INTASEND_SECRET_KEY`: Your Intasend secret key
     - `INTASEND_TEST_MODE`: "False" for production

4. **Deploy your service** and wait for the build to complete

5. **Run database migrations** as described in Option 1

## Custom Domain (Optional)

To use a custom domain with your Render deployment:

1. Go to your web service in the Render dashboard
2. Select the "Settings" tab
3. In the "Custom Domain" section, click "Add Domain"
4. Follow Render's instructions to verify your domain
5. Make sure to add your custom domain to the `ALLOWED_HOSTS` environment variable

## Troubleshooting

### Database Connection Issues
- Ensure the DATABASE_URL is correctly set
- Check if the database service is running properly

### Application Errors
- Check the Render logs for your web service
- Make sure all required environment variables are set correctly

### Static Files Not Loading
- Verify that `STATIC_ROOT` and `STATICFILES_DIRS` are correctly configured in settings.py
- Ensure WhiteNoise middleware is in place as configured in settings.py
- Rebuild the application to collect static files during deployment

### Security
- Ensure DEBUG is set to False in production
- Use HTTPS for all requests (Render provides this by default)
- Keep your secret keys secure and never commit them to version control 