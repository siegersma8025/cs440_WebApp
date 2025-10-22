from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.cache import never_cache
from .forms import *
from .models import *

# Helper function to reduce duplicate authentication code
def check_authentication_and_role(request, role_check, error_message):
    """Centralized authentication and role checking"""
    if not request.user.is_authenticated:
        messages.error(request, "Please log in to access this page.")
        return redirect('home')
    if not role_check(request.user):
        messages.error(request, error_message)
        return redirect('home')
    return None

# Custom decorators for role-based access control
def user_required(view_func):
    """Decorator to ensure only regular users can access this view"""
    def wrapper(request, *args, **kwargs):
        redirect_response = check_authentication_and_role(
            request, 
            lambda user: hasattr(user, 'userprofile'),
            "Access denied: This page is for registered users only."
        )
        return redirect_response or view_func(request, *args, **kwargs)
    return wrapper

def provider_required(view_func):
    """Decorator to ensure only service providers can access this view"""
    def wrapper(request, *args, **kwargs):
        redirect_response = check_authentication_and_role(
            request,
            lambda user: hasattr(user, 'serviceprovider'),
            "Access denied: This page is for service providers only."
        )
        return redirect_response or view_func(request, *args, **kwargs)
    return wrapper

def admin_required(view_func):
    """Decorator to ensure only admins can access this view"""
    def wrapper(request, *args, **kwargs):
        redirect_response = check_authentication_and_role(
            request,
            lambda user: user.is_superuser or user.is_staff or hasattr(user, 'adminprofile'),
            "Access denied: This page is for administrators only."
        )
        return redirect_response or view_func(request, *args, **kwargs)
    return wrapper

# Each view is essentially a function that takes in a request and returns a response
# The response is usually a rendered HTML template
# The request can be a GET or POST request
@never_cache
@csrf_protect
def home(request):
    # If user is already authenticated, redirect to appropriate dashboard
    if request.user.is_authenticated:
        if request.user.is_superuser or request.user.is_staff:
            return redirect('adminDashboard')
        elif hasattr(request.user, 'serviceprovider'):
            return redirect('providerDashboard')
        elif hasattr(request.user, 'userprofile'):
            return redirect('userDashboard')
        else:
            # User is authenticated but has no profile - force logout
            logout(request)
            messages.warning(request, "Your account is not properly configured. Please contact an administrator.")
    
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Basic input validation
        if not username or not password:
            messages.error(request, "Both username and password are required.")
            return redirect('home')
            
        user = authenticate(request, username=username, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                # Check for Django admin first
                if user.is_superuser or user.is_staff:
                    return redirect('adminDashboard')
                elif hasattr(user, 'serviceprovider'):
                    return redirect('providerDashboard')
                elif hasattr(user, 'userprofile'):
                    return redirect('userDashboard')
                else:
                    # Fallback: User exists but has no profile
                    logout(request)
                    messages.warning(request, "Your account is not properly set up. Please contact an administrator.")
                    return redirect('home')
            else:
                messages.error(request, "Your account has been disabled. Please contact an administrator.")
                return redirect('home')
        else:
            messages.error(request, "Invalid username or password. Please try again.")
            return redirect('home')
    
    return render(request, 'home.html', {})


def logoutUser(request):
    logout(request)
    messages.success(request, "Logged out successfully")
    return redirect('home')


@never_cache
@csrf_protect
def registerUser(request):
    if request.method == "POST":
        form = UserSignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Create UserProfile object
            UserProfile.objects.create(
                user=user,
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name']
            )
            messages.success(request, "Registration Successful! You can now log in.")
            return redirect('home')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = UserSignUpForm()
    return render(request, 'registerUser.html', {'form': form})

@never_cache
@csrf_protect
def registerProvider(request):
    if request.method == "POST":
        form = ProviderSignUpForm(request.POST)
        if form.is_valid():
            provider = form.save()  # This creates both User and ServiceProvider
            messages.success(request, "Registration Successful! You can now log in.")
            return redirect('home')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ProviderSignUpForm()
    return render(request, 'registerProvider.html', {'form': form})



@never_cache
@provider_required
def providerDashboard(request):
    provider = request.user.serviceprovider  # Direct access since decorator ensures it exists
    slots = AppointmentSlot.objects.filter(providerUsername=request.user.username)
    slot_form = AppointmentSlotForm()

    if request.method == "POST":
        slot_form = AppointmentSlotForm(request.POST)
        if slot_form.is_valid():
            AppointmentSlot.objects.create(
                appointmentName=slot_form.cleaned_data['appointmentName'],
                providerUsername=request.user.username,
                date=slot_form.cleaned_data['date'],
                start_time=slot_form.cleaned_data['start_time'],
                end_time=slot_form.cleaned_data['end_time']
            )
            messages.success(request, "Appointment slot added!")
            return redirect('providerDashboard')

    return render(request, 'providerDashboard.html', {
        'slots': slots,
        'slot_form': slot_form,
        'provider': provider
    })

@never_cache
@user_required
def userDashboard(request):
    slots = AppointmentSlot.objects.filter(is_booked=False)
    bookings = Booking.objects.filter(user=request.user)

    category_selected = None
    date_selected = None

    if request.method == "POST":
        form = AppointmentSearchForm(request.POST)
        if form.is_valid():
            category_selected = form.cleaned_data['category']
            date_selected = form.cleaned_data['date']

            if category_selected:
                # Get usernames of providers in this category
                provider_usernames = ServiceProvider.objects.filter(category=category_selected).values_list('user__username', flat=True)
                slots = slots.filter(provider_username__in=provider_usernames)
            if date_selected:
                slots = slots.filter(date=date_selected)
    else:
        form = AppointmentSearchForm()

    form = AppointmentSearchForm(request.POST or None)

    return render(request, 'userDashboard.html', {
        'form': form,
        'slots': slots,
        'bookings': bookings,
    })
    
@never_cache
@admin_required
def adminDashboard(request):
    return render(request, 'adminDashboard.html')
    
@user_required
@csrf_protect
def bookAppointment(request, slot_id):
    # Use get_object_or_404 for better error handling
    slot = get_object_or_404(AppointmentSlot, id=slot_id, is_booked=False)
    
    if request.method == "POST":
        # Double-check that slot is still available (race condition protection)
        if slot.is_booked:
            messages.error(request, "Sorry, this appointment has already been booked.")
            return redirect('userDashboard')
            
        slot.is_booked = True
        slot.save()
        Booking.objects.create(slot=slot, user=request.user)
        messages.success(request, "Appointment booked successfully!")
        return redirect('userDashboard')
    else:
        # Only allow POST requests for booking
        messages.error(request, "Invalid request method.")
        return redirect('userDashboard')