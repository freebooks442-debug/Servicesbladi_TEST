from django import forms
from django.contrib.auth.forms import PasswordChangeForm
from .models import Utilisateur

class UserEditForm(forms.ModelForm):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control'}),
        required=True
    )
    name = forms.CharField(
        max_length=100, 
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        required=True
    )
    first_name = forms.CharField(
        max_length=100, 
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        required=True
    )
    phone = forms.CharField(
        max_length=20, 
        required=False, 
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    birth_date = forms.DateField(
        required=False, 
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    residence_country = forms.CharField(
        max_length=100, 
        required=False, 
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    profile_picture = forms.ImageField(
        required=False, 
        widget=forms.FileInput(attrs={
            'class': 'form-control', 
            'accept': 'image/*',
            'id': 'id_profile_picture'
        })
    )
    preferred_languages = forms.CharField(
        max_length=10,
        required=False,
        widget=forms.Select(choices=[
            ('fr', 'Français'),
            ('ar', 'العربية'),
            ('en', 'English'),
            ('es', 'Español'),
        ], attrs={'class': 'form-control'})
    )

    class Meta:
        model = Utilisateur
        fields = ('name', 'first_name', 'email', 'phone', 'birth_date', 'residence_country', 'profile_picture', 'preferred_languages')
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set initial values for existing users
        if self.instance and self.instance.pk:
            for field_name, field in self.fields.items():
                if hasattr(self.instance, field_name):
                    field.initial = getattr(self.instance, field_name)

class CustomPasswordChangeForm(PasswordChangeForm):
    old_password = forms.CharField(
        label="Ancien mot de passe",
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'current-password', 'autofocus': True, 'class': 'form-control'}),
    )
    new_password1 = forms.CharField(
        label="Nouveau mot de passe",
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password', 'class': 'form-control'}),
    )
    new_password2 = forms.CharField(
        label="Confirmation du nouveau mot de passe",
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password', 'class': 'form-control'}),
    )
