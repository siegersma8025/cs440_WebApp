import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.cache import never_cache
# Import forms models, and helper utilities
from .forms import *
from .models import *
from .utils import *


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
            form.save()  # This creates both User and ServiceProvider
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
    from datetime import datetime, date, time
    provider = request.user.serviceprovider  # Direct access since decorator ensures it exists
    
    # Filter out past appointments for providers
    all_slots = AppointmentSlot.objects.filter(providerUsername=request.user.username)
    slots = [slot for slot in all_slots if not slot.is_past()]
    
    slot_form = AppointmentSlotForm()
    canceled_msgs = provider.get_and_clear_canceled_msgs()

    if request.method == "POST":
        slot_form = AppointmentSlotForm(request.POST)
        if slot_form.is_valid():
            try:
                AppointmentSlot.objects.create(
                    appointmentName=slot_form.cleaned_data['appointmentName'],
                    appointmentType = provider.category,
                    providerUsername=request.user.username,
                    providerFirstName=provider.first_name,
                    providerLastName=provider.last_name,
                    date=slot_form.cleaned_data['date'],
                    start_time=slot_form.cleaned_data['start_time'],
                    end_time=slot_form.cleaned_data['end_time']
                )
                messages.success(request, "Appointment slot added!")
            except:
                messages.error(request, "No duplicate time slots allowed!")
            return redirect('providerDashboard')

    return render(request, 'providerDashboard.html', {
        'slots': slots,
        'slot_form': slot_form,
        'provider': provider,
        'canceled_msgs': canceled_msgs,
    })

@never_cache
def userDashboard(request):
    from datetime import datetime, date, time
    
    # Filter out past appointments for users - only show future available slots
    all_slots = AppointmentSlot.objects.filter(is_booked=False)
    slots = [slot for slot in all_slots if not slot.is_past()]
    
    # Filter out past bookings for users
    all_bookings = Booking.objects.filter(user=request.user)
    bookings = [booking for booking in all_bookings if not booking.slot.is_past()]
    
    user_profile = request.user.userprofile
    canceled_msgs = user_profile.get_and_clear_canceled_msgs()

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
                # Filter by category from the list of non-past slots
                slots = [slot for slot in slots if slot.providerUsername in provider_usernames]
            if date_selected:
                # Filter by date from the list of non-past slots
                slots = [slot for slot in slots if slot.date == date_selected]
    else:
        form = AppointmentSearchForm()

    form = AppointmentSearchForm(request.POST or None)

    return render(request, 'userDashboard.html', {
        'form': form,
        'slots': slots,
        'bookings': bookings,
        'canceled_msgs': canceled_msgs,
    })
    
@never_cache
@admin_required
def adminDashboard(request):
    # Get populated filter parameters from GET request
    search = request.GET.get('searchInput', '').lower()
    typeFilter = request.GET.get('typeFilter', '')
    dateFilter = request.GET.get('dateFilter', '')

    # Get appointment slots and filter them
    slots = AppointmentSlot.objects.all()
    items = filterAppointments(slots, search, typeFilter, dateFilter)
    types = set()
    for slot in slots:
        type = slot.appointmentType.strip()
        types.add(type)
    types = sorted(types)

    # Render the admin dashboard with filtered items and available types
    return render(request, 'adminDashboard.html', {
        'items': items,
        'types': types,
        'searchInput': request.GET.get('searchInput', ''),
        'typeFilter': request.GET.get('typeFilter', ''),
        'dateFilter': request.GET.get('dateFilter', ''),
    })


@user_required
@csrf_protect
def bookAppointment(request, slot_id):
    slot = get_object_or_404(AppointmentSlot, id=slot_id, is_booked=False)

    if request.method == "POST":
        # Check for conflicting appointments for this user
        user_bookings = Booking.objects.filter(user=request.user, slot__date=slot.date)
        for booking in user_bookings:
            booked_slot = booking.slot
            # If times overlap, block booking
            if (slot.start_time < booked_slot.end_time and slot.end_time > booked_slot.start_time):
                messages.error(
                    request,
                    f"Conflicting appointment: You already have '{booked_slot.appointmentName}' from "
                    f"{convertFromMilitaryTime(booked_slot.start_time)} to {convertFromMilitaryTime(booked_slot.end_time)} on {booked_slot.date.strftime('%m/%d/%Y')}."
                )
                return redirect('userDashboard')  # Only error message, no success

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
        messages.error(request, "Invalid request method.")
        return redirect('userDashboard')
    

def append_cancel_message(profile, message):
    if profile:
        import json
        msgs = json.loads(profile.canceled_msgs)
        msgs.append(message)
        profile.canceled_msgs = json.dumps(msgs)
        profile.save()

@csrf_protect
def cancelAppointment(request, slot_id):
    slot = get_object_or_404(AppointmentSlot, id=slot_id)
    booking = Booking.objects.filter(slot=slot).first()

    is_provider = hasattr(request.user, 'serviceprovider') and slot.providerUsername == request.user.username
    is_user = booking and hasattr(request.user, 'userprofile') and booking.user == request.user

    if not (is_user or is_provider):
        messages.error(request, "Access denied: This page is for registered users or providers only.")
        return redirect('home')

    start_time_str = convertFromMilitaryTime(slot.start_time)
    end_time_str = convertFromMilitaryTime(slot.end_time)
    date_str = slot.date.strftime('%m/%d/%Y')  # Month/Day/Year format

    if is_user:
        # User cancels: add message for provider, remove booking
        provider_profile = ServiceProvider.objects.filter(user__username=slot.providerUsername).first()
        msg = f"{booking.user.get_full_name()} canceled '{slot.appointmentName}' with you on {date_str} at {start_time_str}-{end_time_str}."
        append_cancel_message(provider_profile, msg)
        booking.delete()
        slot.is_booked = False
        slot.save()
        messages.success(request, "Appointment canceled.")
        return redirect("userDashboard")
    elif is_provider:
        # Provider cancels: add message for user if booked, remove booking if exists, always remove slot
        if booking:
            user_profile = booking.user.userprofile
            msg = f"Your appointment '{slot.appointmentName}' with {slot.providerFirstName} {slot.providerLastName} on {date_str} at {start_time_str}-{end_time_str} was canceled by {slot.providerFirstName}."
            append_cancel_message(user_profile, msg)
            booking.delete()
        slot.delete()
        messages.success(request, "Appointment slot canceled and removed.")
        return redirect("providerDashboard")