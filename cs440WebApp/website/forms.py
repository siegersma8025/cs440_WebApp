from django import forms
from .models import ServiceProvider
from django.contrib.auth.models import User

# Form that will handle User Registration, on save() it will create a new User object
class UserSignUpForm(forms.Form):
    first_name = forms.CharField(label="", max_length=50, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}))
    last_name = forms.CharField(label="", max_length=50, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}))
    username = forms.CharField(label="", max_length=150, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}))
    password1 = forms.CharField(label="", widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}))
    password2 = forms.CharField(label="", widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm Password'}))

    # Validate that passwords match and username is unique
    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            self.add_error('password2', "Passwords do not match.")
        if User.objects.filter(username=cleaned_data.get("username")).exists():
            self.add_error('username', "Username already exists.")
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
    providerCategories = [('', '▼ Select A Provider Type'), ('medical', 'Medical'), ('beauty', 'Beauty'), ('fitness', 'Fitness')]
    providerName = forms.CharField(label="", max_length=50, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Provider Name'}))
    first_name = forms.CharField(label="", max_length=50, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}))
    last_name = forms.CharField(label="", max_length=50, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}))   
    category = forms.ChoiceField(choices=providerCategories, label="", widget=forms.Select(attrs={'class': 'form-control', 'id': 'categoryDropdown', 'placeholder': 'Category'}))
    username = forms.CharField(label="", max_length=150, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}))
    password1 = forms.CharField(label="", widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}))
    password2 = forms.CharField(label="", widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm Password'}))

    # Validate that passwords match, username is unique, and a category is selected
    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            self.add_error('password2', "Passwords do not match.")
        if User.objects.filter(username=cleaned_data.get("username")).exists():
            self.add_error('username', "Username already exists.")
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
            providerName=self.cleaned_data['providerName'],
            category=self.cleaned_data['category'],
            first_name=self.cleaned_data['first_name'],
            last_name=self.cleaned_data['last_name']
        )
        return provider

# Form for service providers to create appointment slots
class AppointmentSlotForm(forms.Form):
    date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}))
    start_time = forms.TimeField(widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}))
    end_time = forms.TimeField(widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}))

# Form for users to search for appointment slots
class AppointmentSearchForm(forms.Form):
    category = forms.ChoiceField(
        choices=[('', 'Select Category')] + ServiceProvider.categortyChoices,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    provider = forms.ModelChoiceField(
        queryset=ServiceProvider.objects.none(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )

    # Will dynamically set provider queryset based on selected category 
    # (Allows for filtering of appointments by provider)
    def __init__(self, *args, **kwargs):
        category_selected = kwargs.pop('category_selected', None)
        super().__init__(*args, **kwargs)
        if category_selected:
            self.fields['provider'].queryset = ServiceProvider.objects.filter(category=category_selected)
        else:
            self.fields['provider'].queryset = ServiceProvider.objects.all()