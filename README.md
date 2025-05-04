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
git clone https://github.com/uday-globuslive/django-gdrive-storage.git
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

4. Set up Google Drive API (detailed instructions):

   ### Step 1: Create a Google Cloud Project

   1. Go to [Google Cloud Console](https://console.cloud.google.com/)
   2. If you don't have a Google Cloud account, sign up for one (it's free to start)
   3. Click on the project dropdown at the top of the page and then click "New Project"
   4. Enter a project name (e.g., "Django GDrive Storage")
   5. Click "Create"
   6. Wait for the project to be created, then select it from the dropdown

   ### Step 2: Enable the Google Drive API

   1. In the left sidebar, navigate to "APIs & Services" > "Library"
   2. In the search bar, type "Google Drive API"
   3. Click on "Google Drive API" in the results
   4. Click the "Enable" button
   5. Wait for the API to be enabled for your project

   ### Step 3: Create Service Account Credentials

   1. In the left sidebar, navigate to "APIs & Services" > "Credentials"
   2. Click on "Create Credentials" at the top, then select "Service account"
   3. Fill in the service account details:
      - Name: "django-gdrive-storage"
      - Service account ID: This will auto-generate based on the name
      - Description: "Service account for Django GDrive Storage app"
   4. Click "Create and Continue"
   5. In the "Grant this service account access to project" section:
      - Click the "Role" dropdown
      - Search for and select "Storage Admin" (this gives full access to Drive)
   6. Click "Continue"
   7. In the "Grant users access to this service account" section, you can leave it empty unless you want to add specific users
   8. Click "Done"

   ### Step 4: Generate and Download Service Account Key

   1. On the Credentials page, find your newly created service account in the list
   2. Click on the service account email address
   3. Go to the "Keys" tab
   4. Click "Add Key" and select "Create new key"
   5. Choose "JSON" as the key type
   6. Click "Create"
   7. The JSON key file will automatically download to your computer
   8. Rename this file to `credentials.json`
   9. Move this file to the root directory of your django-gdrive-storage project

   ### Step 5: Configure Google Drive Permissions (Optional but Recommended)

   If you want to restrict the service account to access only specific folders:

   1. Go to [Google Drive](https://drive.google.com/)
   2. Create a new folder that will be used for your application
   3. Right-click on the folder and select "Share"
   4. Add the service account email address (it looks like `service-account-name@project-id.iam.gserviceaccount.com`)
   5. Give it "Editor" permission
   6. Click "Send" (no notification will be sent)

   ### Security Notes:

   1. **Keep your credentials.json file secure** - it contains private keys that grant access to your Google Drive.
   2. **Add credentials.json to your .gitignore file** - never commit it to a public repository.
   3. **Consider using environment variables** for sensitive settings in production.
   4. **Set up proper scopes and permissions** - only grant the minimum necessary access to your service account.

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

## Troubleshooting Google Drive API

### Common Issues:

1. **Authentication errors**: 
   - Ensure your credentials.json file is correctly formatted and placed in the right location
   - Verify that your service account has not been disabled
   - Check that your project has billing enabled if you're exceeding free tier limits

2. **Permission errors**: 
   - Make sure your service account has the correct permissions for the folders you're trying to access
   - Verify that you've properly shared folders with the service account email address
   - Check that you've granted the right role (Editor or higher) to the service account

3. **API quota errors**: 
   - The free tier has usage limits (currently 1 billion requests per day)
   - For a production app, consider setting up billing
   - Implement caching strategies to reduce API calls

4. **File not showing in Drive**: 
   - Check if the files are being uploaded to a different folder than expected
   - Verify that the file upload is not silently failing
   - Look at the folder sharing settings to ensure visibility

5. **Wrong MIME types**:
   - If files are uploaded but with incorrect types, check the MIME type detection in your code
   - For certain file types, you might need to explicitly specify the MIME type

### Debugging Tips:

1. Enable verbose logging in your application to see detailed API interactions
2. Use the [Google APIs Explorer](https://developers.google.com/apis-explorer) to test API calls directly
3. Check the Google Cloud Console's "API & Services" > "Dashboard" for API usage metrics and errors
4. For service account issues, review the IAM permissions in Google Cloud Console

## License

This project is licensed under the MIT License - see the LICENSE file for details.
