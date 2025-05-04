import os
import tempfile
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.contrib import messages
from django.http import HttpResponse, Http404
from django.utils.text import slugify
from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import User

from .forms import UserRegisterForm, FileUploadForm
from .models import UserProfile, FileEntry
from .gdrive import GoogleDriveService

def home(request):
    """Home page view."""
    return render(request, 'ftp/home.html')

def register(request):
    """User registration view."""
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            UserProfile.objects.create(user=user)
            messages.success(request, 'Your account has been created! Please wait for admin approval before you can log in.')
            return redirect('login')
    else:
        form = UserRegisterForm()
    
    return render(request, 'ftp/register.html', {'form': form})

@login_required
def dashboard(request):
    """User dashboard view."""
    user_profile = UserProfile.objects.get(user=request.user)
    
    if not user_profile.is_approved:
        messages.warning(request, 'Your account is pending approval by an administrator.')
        return render(request, 'ftp/pending_approval.html')
    
    files = FileEntry.objects.filter(user=request.user)
    
    return render(request, 'ftp/dashboard.html', {'files': files})

@login_required
def upload_file(request):
    """File upload view."""
    user_profile = UserProfile.objects.get(user=request.user)
    
    if not user_profile.is_approved:
        messages.warning(request, 'Your account is pending approval by an administrator.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = FileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = request.FILES['file']
            description = form.cleaned_data['description']
            
            # Save file temporarily
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                for chunk in uploaded_file.chunks():
                    temp_file.write(chunk)
                temp_file_path = temp_file.name
            
            try:
                # Initialize Google Drive service
                drive_service = GoogleDriveService()
                
                # Create user folder if it doesn't exist
                if not user_profile.drive_folder_id:
                    folder_id = drive_service.create_user_folder(f"gdriveftp_{request.user.username}")
                    if folder_id:
                        user_profile.drive_folder_id = folder_id
                        user_profile.save()
                    else:
                        messages.error(request, 'Error creating user folder in Google Drive.')
                        return redirect('dashboard')
                
                # Upload file to Google Drive
                file_id = drive_service.upload_file(
                    temp_file_path,
                    uploaded_file.name,
                    user_profile.drive_folder_id
                )
                
                if file_id:
                    # Save file entry to database
                    file_entry = FileEntry(
                        user=request.user,
                        file_name=uploaded_file.name,
                        file_size=uploaded_file.size,
                        file_type=uploaded_file.content_type,
                        drive_file_id=file_id,
                        description=description
                    )
                    file_entry.save()
                    
                    messages.success(request, f'File {uploaded_file.name} uploaded successfully!')
                else:
                    messages.error(request, 'Error uploading file to Google Drive.')
            finally:
                # Delete temporary file
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
            
            return redirect('dashboard')
    else:
        form = FileUploadForm()
    
    return render(request, 'ftp/upload_file.html', {'form': form})

@login_required
def download_file(request, file_id):
    """File download view."""
    file_entry = get_object_or_404(FileEntry, id=file_id, user=request.user)
    
    drive_service = GoogleDriveService()
    file_content = drive_service.download_file(file_entry.drive_file_id)
    
    if file_content:
        response = HttpResponse(
            file_content.getvalue(),
            content_type=file_entry.file_type or 'application/octet-stream'
        )
        response['Content-Disposition'] = f'attachment; filename="{file_entry.file_name}"'
        return response
    else:
        messages.error(request, 'Error downloading file from Google Drive.')
        return redirect('dashboard')

@login_required
def delete_file(request, file_id):
    """File deletion view."""
    file_entry = get_object_or_404(FileEntry, id=file_id, user=request.user)
    
    if request.method == 'POST':
        drive_service = GoogleDriveService()
        if drive_service.delete_file(file_entry.drive_file_id):
            file_entry.delete()
            messages.success(request, f'File {file_entry.file_name} deleted successfully!')
        else:
            messages.error(request, 'Error deleting file from Google Drive.')
        
        return redirect('dashboard')
    
    return render(request, 'ftp/delete_file.html', {'file': file_entry})

@staff_member_required
def admin_dashboard(request):
    """Admin dashboard for user approval."""
    pending_users = UserProfile.objects.filter(is_approved=False)
    approved_users = UserProfile.objects.filter(is_approved=True)
    
    return render(request, 'ftp/admin_dashboard.html', {
        'pending_users': pending_users,
        'approved_users': approved_users
    })

@staff_member_required
def approve_user(request, user_id):
    """Approve a user."""
    user_profile = get_object_or_404(UserProfile, user_id=user_id)
    
    if request.method == 'POST':
        user_profile.is_approved = True
        user_profile.save()
        
        # Create Google Drive folder for the user
        drive_service = GoogleDriveService()
        folder_id = drive_service.create_user_folder(f"gdriveftp_{user_profile.user.username}")
        
        if folder_id:
            user_profile.drive_folder_id = folder_id
            user_profile.save()
            messages.success(request, f'User {user_profile.user.username} approved successfully!')
        else:
            messages.error(request, f'User approved but error creating Google Drive folder.')
        
        return redirect('admin_dashboard')
    
    return render(request, 'ftp/approve_user.html', {'user_profile': user_profile})

@staff_member_required
def revoke_user(request, user_id):
    """Revoke user approval."""
    user_profile = get_object_or_404(UserProfile, user_id=user_id)
    
    if request.method == 'POST':
        user_profile.is_approved = False
        user_profile.save()
        messages.success(request, f'User {user_profile.user.username} approval revoked!')
        return redirect('admin_dashboard')
    
    return render(request, 'ftp/revoke_user.html', {'user_profile': user_profile})