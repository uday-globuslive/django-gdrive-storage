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
from .models import UserProfile, FileEntry, FolderEntry
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
def dashboard(request, folder_id=None):
    """User dashboard view."""
    user_profile = UserProfile.objects.get(user=request.user)
    
    if not user_profile.is_approved:
        messages.warning(request, 'Your account is pending approval by an administrator.')
        return render(request, 'ftp/pending_approval.html')
    
    current_folder = None
    breadcrumbs = []
    
    if folder_id:
        try:
            current_folder = FolderEntry.objects.get(id=folder_id, user=request.user)
            
            # Build breadcrumbs
            temp_folder = current_folder
            while temp_folder:
                breadcrumbs.insert(0, temp_folder)
                temp_folder = temp_folder.parent_folder
                
            # Get files and folders in the current folder
            files = FileEntry.objects.filter(user=request.user, folder=current_folder)
            folders = FolderEntry.objects.filter(user=request.user, parent_folder=current_folder)
        except FolderEntry.DoesNotExist:
            messages.error(request, 'Folder not found.')
            return redirect('dashboard')
    else:
        # Root level - show files and folders with no parent
        files = FileEntry.objects.filter(user=request.user, folder=None)
        folders = FolderEntry.objects.filter(user=request.user, parent_folder=None)
    
    return render(request, 'ftp/dashboard.html', {
        'files': files,
        'folders': folders,
        'current_folder': current_folder,
        'breadcrumbs': breadcrumbs
    })

@login_required
def upload_file(request):
    """File upload view."""
    user_profile = UserProfile.objects.get(user=request.user)
    
    if not user_profile.is_approved:
        messages.warning(request, 'Your account is pending approval by an administrator.')
        return redirect('dashboard')
    
    # Get all folders for the user to populate the dropdown
    user_folders = []
    try:
        folders = FolderEntry.objects.filter(user=request.user)
        for folder in folders:
            user_folders.append((folder.id, folder.get_path()))
    except Exception as e:
        print(f"Error fetching folders: {e}")
    
    if request.method == 'POST':
        form = FileUploadForm(request.POST, request.FILES, user_folders=user_folders)
        if form.is_valid():
            # Initialize Google Drive service
            drive_service = GoogleDriveService()
            
            # Create user folder if it doesn't exist
            if not user_profile.drive_folder_id:
                folder_id = drive_service.create_user_folder(
                    f"gdriveftp_{request.user.username}",
                    share_with_email=user_profile.share_email if user_profile.share_email else None
                )
                if folder_id:
                    user_profile.drive_folder_id = folder_id
                    user_profile.save()
                else:
                    messages.error(request, 'Error creating user folder in Google Drive.')
                    return redirect('dashboard')
            
            # Handle folder creation
            folder_name = form.cleaned_data.get('folder_name')
            parent_folder_id = form.cleaned_data.get('parent_folder')
            
            if folder_name:
                # Determine parent folder in Drive
                drive_parent_id = user_profile.drive_folder_id
                db_parent = None
                
                if parent_folder_id:
                    try:
                        db_parent = FolderEntry.objects.get(id=parent_folder_id, user=request.user)
                        drive_parent_id = db_parent.drive_folder_id
                    except FolderEntry.DoesNotExist:
                        messages.warning(request, 'Selected parent folder does not exist. Creating in root folder.')
                
                # Create folder in Drive
                drive_folder_id = drive_service.create_subfolder(
                    folder_name, 
                    drive_parent_id,
                    share_with_email=user_profile.share_email if user_profile.share_email else None
                )
                
                if drive_folder_id:
                    # Save folder entry to database
                    folder_entry = FolderEntry(
                        user=request.user,
                        folder_name=folder_name,
                        drive_folder_id=drive_folder_id,
                        parent_folder=db_parent
                    )
                    folder_entry.save()
                    messages.success(request, f'Folder {folder_name} created successfully!')
                else:
                    messages.error(request, 'Error creating folder in Google Drive.')
            
            # Handle file uploads
            files = request.FILES.getlist('file')
            
            if files:
                success_count = 0
                error_count = 0
                
                # Determine target folder in Drive
                upload_folder_id = user_profile.drive_folder_id
                db_folder = None
                
                if parent_folder_id:
                    try:
                        db_folder = FolderEntry.objects.get(id=parent_folder_id, user=request.user)
                        upload_folder_id = db_folder.drive_folder_id
                    except FolderEntry.DoesNotExist:
                        messages.warning(request, 'Selected folder does not exist. Uploading to root folder.')
                
                description = form.cleaned_data.get('description', '')
                
                for uploaded_file in files:
                    # Save file temporarily
                    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                        for chunk in uploaded_file.chunks():
                            temp_file.write(chunk)
                        temp_file_path = temp_file.name
                    
                    try:
                        # Upload file to Google Drive
                        file_id = drive_service.upload_file(
                            temp_file_path,
                            uploaded_file.name,
                            upload_folder_id,
                            share_with_email=user_profile.share_email if user_profile.share_email else None
                        )
                        
                        if file_id:
                            # Save file entry to database
                            file_entry = FileEntry(
                                user=request.user,
                                file_name=uploaded_file.name,
                                file_size=uploaded_file.size,
                                file_type=uploaded_file.content_type,
                                drive_file_id=file_id,
                                description=description,
                                folder=db_folder
                            )
                            file_entry.save()
                            success_count += 1
                        else:
                            error_count += 1
                    finally:
                        # Delete temporary file
                        if os.path.exists(temp_file_path):
                            os.unlink(temp_file_path)
                
                if success_count > 0:
                    messages.success(request, f'Successfully uploaded {success_count} file(s).')
                if error_count > 0:
                    messages.error(request, f'Failed to upload {error_count} file(s).')
            
            return redirect('dashboard')
    else:
        form = FileUploadForm(user_folders=user_folders)
    
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

@login_required
def delete_folder(request, folder_id):
    """Delete folder and its contents."""
    folder = get_object_or_404(FolderEntry, id=folder_id, user=request.user)
    parent_id = folder.parent_folder.id if folder.parent_folder else None
    
    if request.method == 'POST':
        drive_service = GoogleDriveService()
        
        # Delete folder in Google Drive
        if drive_service.delete_folder(folder.drive_folder_id):
            # Delete all files and subfolders in database
            folder.delete()
            messages.success(request, f'Folder {folder.folder_name} deleted successfully!')
        else:
            messages.error(request, 'Error deleting folder from Google Drive.')
        
        if parent_id:
            return redirect('folder_view', folder_id=parent_id)
        return redirect('dashboard')
    
    return render(request, 'ftp/delete_folder.html', {'folder': folder})

@login_required
def user_settings(request):
    """User settings view."""
    user_profile = UserProfile.objects.get(user=request.user)
    
    if request.method == 'POST':
        form = SettingsForm(request.POST, instance=user_profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your settings have been updated successfully!')
            return redirect('dashboard')
    else:
        form = SettingsForm(instance=user_profile)
    
    return render(request, 'ftp/settings.html', {'form': form})