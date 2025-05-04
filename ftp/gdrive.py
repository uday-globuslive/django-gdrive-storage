import os
import io
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from google.oauth2 import service_account
from django.conf import settings
import mimetypes

class GoogleDriveService:
    def __init__(self):
        self.credentials = None
        self.service = None
        self.initialize_service()
    
    def initialize_service(self):
        """Initialize the Google Drive API service."""
        try:
            credentials_path = settings.GOOGLE_DRIVE_STORAGE_JSON_KEY_FILE
            if os.path.exists(credentials_path):
                self.credentials = service_account.Credentials.from_service_account_file(
                    credentials_path,
                    scopes=['https://www.googleapis.com/auth/drive']
                )
                self.service = build('drive', 'v3', credentials=self.credentials)
            else:
                raise FileNotFoundError(f"Credentials file not found at {credentials_path}")
        except Exception as e:
            print(f"Error initializing Google Drive service: {e}")
            self.service = None
    
    def create_user_folder(self, folder_name):
        """Create a folder in Google Drive for a user and return its ID."""
        if not self.service:
            return None
        
        try:
            file_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            
            folder = self.service.files().create(
                body=file_metadata,
                fields='id'
            ).execute()
            
            return folder.get('id')
        except Exception as e:
            print(f"Error creating folder: {e}")
            return None
    
    def upload_file(self, file_path, file_name, parent_folder_id):
        """Upload a file to Google Drive and return its ID."""
        if not self.service:
            return None
        
        try:
            mime_type, _ = mimetypes.guess_type(file_path)
            
            if mime_type is None:
                mime_type = 'application/octet-stream'
            
            file_metadata = {
                'name': file_name,
                'parents': [parent_folder_id]
            }
            
            media = MediaFileUpload(
                file_path,
                mimetype=mime_type,
                resumable=True
            )
            
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()
            
            return file.get('id')
        except Exception as e:
            print(f"Error uploading file: {e}")
            return None
    
    def download_file(self, file_id):
        """Download a file from Google Drive."""
        if not self.service:
            return None
        
        try:
            request = self.service.files().get_media(fileId=file_id)
            file_content = io.BytesIO()
            downloader = MediaIoBaseDownload(file_content, request)
            
            done = False
            while not done:
                status, done = downloader.next_chunk()
            
            file_content.seek(0)
            return file_content
        except Exception as e:
            print(f"Error downloading file: {e}")
            return None
    
    def delete_file(self, file_id):
        """Delete a file from Google Drive."""
        if not self.service:
            return False
        
        try:
            self.service.files().delete(fileId=file_id).execute()
            return True
        except Exception as e:
            print(f"Error deleting file: {e}")
            return False
    
    def list_files(self, folder_id):
        """List all files in a folder."""
        if not self.service:
            return []
        
        try:
            results = self.service.files().list(
                q=f"'{folder_id}' in parents",
                fields="files(id, name, mimeType, size, createdTime)"
            ).execute()
            
            return results.get('files', [])
        except Exception as e:
            print(f"Error listing files: {e}")
            return []