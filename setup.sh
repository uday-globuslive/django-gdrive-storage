#!/bin/bash

echo "Setting up GDrive FTP application..."

# Check if credentials.json exists
if [ ! -f "credentials.json" ]; then
    echo "Error: credentials.json not found!"
    echo "Please create a service account in Google Cloud Console and download the credentials.json file."
    echo "See the README.md file for detailed instructions."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Run migrations
echo "Running database migrations..."
python manage.py migrate

# Create superuser if not exists
echo "Checking for superuser..."
if ! python -c "import django; django.setup(); from django.contrib.auth.models import User; exit(0) if User.objects.filter(is_superuser=True).exists() else exit(1)"; then
    echo "Creating superuser..."
    python -c "import django; django.setup(); from django.contrib.auth.models import User; User.objects.create_superuser('admin', 'admin@example.com', 'adminpassword') if not User.objects.filter(is_superuser=True).exists() else None"
    echo "Superuser created with username: 'admin' and password: 'adminpassword'"
    echo "Please change the password immediately after first login!"
fi

# Create media and static directories if they don't exist
if [ ! -d "media" ]; then
    echo "Creating media directory..."
    mkdir -p media
fi

if [ ! -d "static" ]; then
    echo "Creating static directory..."
    mkdir -p static
fi

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Setup complete! Start the application with: python manage.py runserver"
echo "Then visit http://127.0.0.1:8000/ in your web browser."
echo "Login with username 'admin' and password 'adminpassword'"