# Deploying to Render Free Tier

This guide shows how to deploy your Intasend Payment Integration on Render's free tier without using Blueprints.

## Manual Deployment to Render Free Tier

1. **Create a Render account** at [render.com](https://render.com) if you don't have one

2. **Create a Web Service**:
   - From your Render dashboard, click "New" and select "Web Service"
   - Connect your GitHub/GitLab repository
   - Configure your service:
     - **Name**: intasend-payment (or your preferred name)
     - **Environment**: Python
     - **Region**: Choose the closest to your users
     - **Branch**: main (or your default branch)
     - **Build Command**: `chmod +x build.sh && ./build.sh`
     - **Start Command**: `gunicorn intasend_payment.wsgi:application`
     - **Plan**: Free

3. **Set Environment Variables**:
   - In the "Environment" tab, add these key-value pairs:
   ```
   DATABASE_URL=sqlite:///db.sqlite3
   SECRET_KEY=your-secure-secret-key
   DEBUG=False
   ALLOWED_HOSTS=.onrender.com,localhost,127.0.0.1
   INTASEND_PUBLISHABLE_KEY=your-intasend-publishable-key
   INTASEND_SECRET_KEY=your-intasend-secret-key
   INTASEND_TEST_MODE=True
   ```
   
   Note: Free tier uses SQLite instead of PostgreSQL. For production, consider upgrading to a paid plan with PostgreSQL.

4. **Create a Persistent Disk**:
   - In the "Disks" tab, add a disk:
     - **Mount Path**: `/opt/render/project/src/db`
     - **Size**: 1 GB (the minimum)
   - This will store your SQLite database and prevent it from being lost during deployments

5. **Deploy the Service**:
   - Click "Create Web Service"
   - Render will start building and deploying your application

## After Deployment

1. **Access your app**:
   - Once deployment is complete, your app will be available at the URL provided by Render
   - It will be something like: https://intasend-payment.onrender.com

2. **Create a superuser** (optional):
   - Go to your web service in the Render dashboard
   - Click on "Shell"
   - Run: `cd /opt/render/project/src && python manage.py createsuperuser`

## Free Tier Limitations

- **Sleep Mode**: Your service will go to sleep after 15 minutes of inactivity
- **Startup Delay**: First request after sleep will take 30-60 seconds to wake the service
- **Resources**: Limited CPU and memory
- **No PostgreSQL**: Using SQLite instead (but data is preserved with persistent disk)

## Updating Your Application

When you push changes to your repository:

1. Go to your web service in the Render dashboard
2. Click "Manual Deploy" > "Clear build cache & deploy"

## Converting to SQLite for Free Tier

To modify your app to work with SQLite for the free tier:

1. Update your application settings to check for SQLite database URL:

```python
DATABASES = {
    'default': dj_database_url.config(
        default='sqlite:///db/db.sqlite3',
        conn_max_age=600
    )
}
```

2. In settings.py, adjust the media and static file paths to work with Render's persistent disk:

```python
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
```

## Troubleshooting Free Tier Issues

- **App going to sleep**: This is normal for free tier; the first request after inactivity will be slow
- **Database errors**: Ensure the persistent disk is correctly mounted
- **Static files not loading**: Verify WhiteNoise is correctly configured
- **Deployment failures**: Check the build logs for specific errors 