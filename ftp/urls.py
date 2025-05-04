from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .forms import UserLoginForm

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(
        template_name='ftp/login.html',
        authentication_form=UserLoginForm
    ), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    # User dashboard and file management
    path('dashboard/', views.dashboard, name='dashboard'),
    path('folder/<int:folder_id>/', views.dashboard, name='folder_view'),
    path('upload/', views.upload_file, name='upload_file'),
    path('download/<int:file_id>/', views.download_file, name='download_file'),
    path('delete/file/<int:file_id>/', views.delete_file, name='delete_file'),
    path('delete/folder/<int:folder_id>/', views.delete_folder, name='delete_folder'),
    path('settings/', views.user_settings, name='user_settings'),
    
    # Admin views
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('approve-user/<int:user_id>/', views.approve_user, name='approve_user'),
    path('revoke-user/<int:user_id>/', views.revoke_user, name='revoke_user'),
]