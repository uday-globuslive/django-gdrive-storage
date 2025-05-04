from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .models import UserProfile

class UserLoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}))

class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}))
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}))
    password1 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}))
    password2 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm Password'}))
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = single_file_clean(data, initial)
        return result

class FileUploadForm(forms.Form):
    file = MultipleFileField(
        widget=MultipleFileInput(attrs={'class': 'form-control'}),
        required=False
    )
    description = forms.CharField(
        required=False, 
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Description (optional)'})
    )
    folder_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter folder name (optional)'})
    )
    parent_folder = forms.ChoiceField(
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    def __init__(self, *args, **kwargs):
        user_folders = kwargs.pop('user_folders', [])
        super(FileUploadForm, self).__init__(*args, **kwargs)
        
        # Dynamically set folder choices
        folder_choices = [('', 'Root Folder')]
        if user_folders:
            folder_choices.extend(user_folders)
        self.fields['parent_folder'].choices = folder_choices
        
    def clean(self):
        cleaned_data = super().clean()
        file = cleaned_data.get('file')
        folder_name = cleaned_data.get('folder_name')
        
        if not file and not folder_name:
            raise forms.ValidationError("You must either upload files or create a folder.")
            
class SettingsForm(forms.ModelForm):
    share_email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Your personal Google email'}),
        help_text="Enter your personal Google email to share files with (so you can see them in your Drive)"
    )
    
    class Meta:
        model = UserProfile
        fields = ['share_email']