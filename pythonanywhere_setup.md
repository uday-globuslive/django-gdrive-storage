# Deploying GDriveFTP to PythonAnywhere

This guide will help you deploy your GDriveFTP application to a free PythonAnywhere account.

## Prerequisites

1. Create a free account on [PythonAnywhere](https://www.pythonanywhere.com)
2. Set up Google Drive API and get your credentials.json file

## Step 1: Set up Google Drive API

1. Go to [Google Developer Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable the Google Drive API
4. Create a service account
5. Generate and download JSON credentials
6. Rename the downloaded file to `credentials.json`

## Step 2: Upload your project to PythonAnywhere

1. Log in to your PythonAnywhere account
2. Go to the Files tab
3. Create a new directory for your project (e.g., `gdriveftp`)
4. Upload all your project files to this directory or use Git:

```bash
cd ~
git clone https://github.com/yourusername/gdriveftp.git
```

## Step 3: Set up a virtual environment

1. Open a Bash console in PythonAnywhere
2. Create and activate a virtual environment:

```bash
cd ~/gdriveftp
python -m venv venv
source venv/bin/activate
```

3. Install dependencies:

```bash
pip install django google-auth-oauthlib google-api-python-client
```

## Step 4: Configure your project for PythonAnywhere

1. Upload your `credentials.json` file to the project root
2. Make sure your `settings.py` includes your PythonAnywhere domain in ALLOWED_HOSTS:

```python
ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'yourusername.pythonanywhere.com']
```

3. Configure the static files:

```python
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
```

## Step 5: Set up your web app

1. Go to the Web tab in PythonAnywhere
2. Click on "Add a new web app"
3. Choose "Manual configuration" (not Django)
4. Select your Python version (3.8 or newer)
5. Set the path to your project: `/home/yourusername/gdriveftp`

## Step 6: Configure WSGI file

1. Click on the WSGI configuration file link in the Web tab
2. Replace the content with:

```python
import os
import sys

# Add your project directory to the sys.path
path = '/home/yourusername/gdriveftp'
if path not in sys.path:
    sys.path.append(path)

# Set environment variables
os.environ['DJANGO_SETTINGS_MODULE'] = 'gdriveftp.settings'

# Activate your virtual environment
activate_this = os.path.join(path, 'venv/bin/activate_this.py')
with open(activate_this) as file_:
    exec(file_.read(), dict(__file__=activate_this))

# Import the Django WSGI application
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

## Step 7: Configure static files

1. Go to the Web tab
2. In the "Static files" section, add:
   - URL: `/static/`
   - Directory: `/home/yourusername/gdriveftp/staticfiles`
   - URL: `/media/`
   - Directory: `/home/yourusername/gdriveftp/media`

## Step 8: Run migrations and collect static files

1. Open a Bash console:

```bash
cd ~/gdriveftp
source venv/bin/activate
python manage.py migrate
python manage.py collectstatic
```

2. Create a superuser to access the admin panel:

```bash
python manage.py createsuperuser
```

## Step 9: Reload your web app

1. Go to the Web tab
2. Click the "Reload" button for your web app

## Step 10: Access your application

Your application should now be running at:
```
https://yourusername.pythonanywhere.com
```

You can access the admin panel at:
```
https://yourusername.pythonanywhere.com/admin/
```

## Troubleshooting

Check the error logs on the Web tab if you encounter any issues.