# GDriveFTP

GDriveFTP is a Django-based web application that provides an FTP-like file storage service powered by Google Drive. It allows users to register, upload, download, and manage files, with all data synchronized to a configurable Google Drive account.

## Features

- User registration with admin approval workflow
- Secure file upload and download
- Google Drive integration for file storage
- User-specific folders for file organization
- Admin dashboard for user management
- Responsive Bootstrap UI

## Technology Stack

- Python 3.8+
- Django 5.2
- Google Drive API
- Bootstrap 5

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/gdriveftp.git
cd gdriveftp
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up Google Drive API:
   - Go to [Google Developer Console](https://console.cloud.google.com/)
   - Create a new project
   - Enable the Google Drive API
   - Create a service account
   - Generate and download JSON credentials
   - Rename the downloaded file to `credentials.json` and place it in the project root

5. Apply migrations:
```bash
python manage.py migrate
```

6. Create a superuser:
```bash
python manage.py createsuperuser
```

7. Run the development server:
```bash
python manage.py runserver
```

8. Access the application at http://127.0.0.1:8000/

## Deployment

For deployment to PythonAnywhere, see [pythonanywhere_setup.md](pythonanywhere_setup.md).

## Usage

1. Admin Setup:
   - Log in as the superuser
   - Navigate to the admin dashboard
   - Approve user registrations

2. User Registration:
   - Users register with email and password
   - Wait for admin approval
   - Log in after approval

3. File Management:
   - Upload files via the user dashboard
   - View, download, and delete files
   - Files are stored in user-specific folders on Google Drive

## Project Structure

```
gdriveftp/
├── ftp/                    # Main app
│   ├── models.py           # Data models
│   ├── views.py            # View functions
│   ├── urls.py             # URL routing
│   ├── forms.py            # Form definitions
│   ├── gdrive.py           # Google Drive integration
│   └── admin.py            # Admin panel configuration
├── templates/              # HTML templates
│   └── ftp/
├── static/                 # Static files (CSS, JS)
├── media/                  # User uploaded files (temporary)
├── gdriveftp/              # Project settings
├── manage.py               # Django management script
├── credentials.json        # Google Drive API credentials
└── requirements.txt        # Project dependencies
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.