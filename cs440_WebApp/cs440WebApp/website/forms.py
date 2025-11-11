from django import forms
from .models import ServiceProvider
from django.contrib.auth.models import User
from django.db import connection
import re

# Form that will handle User Registration, on save() it will create a new User object
class UserSignUpForm(forms.Form):
    first_name = forms.CharField(label="", max_length=50, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name', 'autocomplete': 'given-name'}))
    last_name = forms.CharField(label="", max_length=50, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name', 'autocomplete': 'family-name'}))
    username = forms.CharField(label="", max_length=150, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username', 'autocomplete': 'username', 'spellcheck': 'false'}))
    password1 = forms.CharField(label="", widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password', 'autocomplete': 'new-password', 'spellcheck': 'false'}))
    password2 = forms.CharField(label="", widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm Password', 'autocomplete': 'new-password', 'spellcheck': 'false'}))

    def clean_username(self):
        """Validate username field specifically"""
        username = self.cleaned_data.get('username')
        
        if not username:
            raise forms.ValidationError("Username is required.")
        
        # Check username format (alphanumeric and underscores only, must start with letter)
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', username):
            raise forms.ValidationError("Username must start with a letter and contain only letters, numbers, and underscores.")
        
        # Check minimum length
        if len(username) < 3:
            raise forms.ValidationError("Username must be at least 3 characters long.")
        
        # Check against auth_user table for duplicates (both users and providers)
        with connection.cursor() as cursor:
            cursor.execute("SELECT username FROM auth_user WHERE LOWER(username) = LOWER(%s)", [username])
            if cursor.fetchone():
                raise forms.ValidationError("This username is already taken. Please choose a different username.")
        
        return username

    # Validate that passwords match and additional validation
    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")
        
        # Password matching validation
        if password1 and password2 and password1 != password2:
            self.add_error('password2', "Passwords do not match.")
        
        # Password strength validation
        if password1 and len(password1) < 8:
            self.add_error('password1', "Password must be at least 8 characters long.")
            
        return cleaned_data

    # Create and return the User object
    def save(self):
        user = User.objects.create_user(
            username=self.cleaned_data['username'],
            password=self.cleaned_data['password1'],
            first_name=self.cleaned_data['first_name'],
            last_name=self.cleaned_data['last_name']
        )
        return user

# Form that will handle Service Provider Registration, on save() it will create a new User and ServiceProvider object
class ProviderSignUpForm(forms.Form):
    providerCategories = [('', '▼ Select A Provider Type'), ('Medical', 'Medical'), ('Beauty', 'Beauty'), ('Fitness', 'Fitness')]
    qualifications = forms.CharField(label="", max_length=255, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Qualifications', 'autocomplete': 'off'}))
    first_name = forms.CharField(label="", max_length=50, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name', 'autocomplete': 'given-name'}))
    last_name = forms.CharField(label="", max_length=50, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name', 'autocomplete': 'family-name'}))   
    category = forms.ChoiceField(choices=providerCategories, label="", widget=forms.Select(attrs={'class': 'form-control', 'id': 'categoryDropdown', 'placeholder': 'Category'}))
    username = forms.CharField(label="", max_length=150, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username', 'autocomplete': 'username', 'spellcheck': 'false'}))
    password1 = forms.CharField(label="", widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password', 'autocomplete': 'new-password', 'spellcheck': 'false'}))
    password2 = forms.CharField(label="", widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm Password', 'autocomplete': 'new-password', 'spellcheck': 'false'}))

    def clean_username(self):
        """Validate username field specifically for providers"""
        username = self.cleaned_data.get('username')
        
        if not username:
            raise forms.ValidationError("Username is required.")
        
        # Check username format (alphanumeric and underscores only, must start with letter)
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', username):
            raise forms.ValidationError("Username must start with a letter and contain only letters, numbers, and underscores.")
        
        # Check minimum length
        if len(username) < 3:
            raise forms.ValidationError("Username must be at least 3 characters long.")
        
        # Check against auth_user table for duplicates (both users and providers)
        with connection.cursor() as cursor:
            cursor.execute("SELECT username FROM auth_user WHERE LOWER(username) = LOWER(%s)", [username])
            if cursor.fetchone():
                raise forms.ValidationError("This username is already taken. Please choose a different username.")
        
        return username

    # Validate that passwords match, username is unique, and a category is selected
    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")
        
        # Password matching validation
        if password1 and password2 and password1 != password2:
            self.add_error('password2', "Passwords do not match.")
        
        # Password strength validation
        if password1 and len(password1) < 8:
            self.add_error('password1', "Password must be at least 8 characters long.")
        
        # Category validation
        if cleaned_data.get("category") == "":
            self.add_error('category', "Please select a provider type.")
            
        return cleaned_data

    # Create and return the ServiceProvider object (and associated User object)
    def save(self):
        user = User.objects.create_user(
            username=self.cleaned_data['username'],
            password=self.cleaned_data['password1']
        )
        provider = ServiceProvider.objects.create(
            user=user,
            qualifications=self.cleaned_data['qualifications'],
            category=self.cleaned_data['category'],
            first_name=self.cleaned_data['first_name'],
            last_name=self.cleaned_data['last_name']
        )
        return provider

# Form for service providers to create appointment slots
class AppointmentSlotForm(forms.Form):
    appointmentName = forms.CharField(label="", max_length=100, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Appointment Name'}))
    date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}))
    start_time = forms.TimeField(widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}))
    end_time = forms.TimeField(widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}))

# Form for users to search for appointment slots
class AppointmentSearchForm(forms.Form):
    category = forms.ChoiceField(choices=[('', 'Select Category')] + ServiceProvider.categoryChoices, required=False, widget=forms.Select(attrs={'class': 'form-select'}))
    date = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}))