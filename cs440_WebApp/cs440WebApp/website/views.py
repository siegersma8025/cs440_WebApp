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

#help page
def help_page(request):
    return render(request, "help.html")   
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
    try:
        provider_profile = ServiceProvider.objects.get(user=request.user)
    except ServiceProvider.DoesNotExist:
        messages.error(request, "Access denied: You are not registered as a provider.")
        return redirect('home')

    # Handle new slot form submission
    if request.method == "POST":
        slot_form = AppointmentSlotForm(request.POST)
        if slot_form.is_valid():
            cd = slot_form.cleaned_data
            new_slot = AppointmentSlot(
                providerUsername=request.user.username,
                providerFirstName=provider_profile.first_name,
                providerLastName=provider_profile.last_name,
                appointmentName=cd.get('appointmentName'),
                appointmentType=provider_profile.category,
                date=cd.get('date'),
                start_time=cd.get('start_time'),
                end_time=cd.get('end_time'),
                is_booked=False,
            )
            new_slot.save()
            messages.success(request, "Appointment slot added successfully.")
            return redirect('providerDashboard')
    else:
        slot_form = AppointmentSlotForm()

    # Filtering parameters
    search = request.GET.get('searchInput', '').strip().lower()
    typeFilter = request.GET.get('typeFilter', '')
    dateFilter = request.GET.get('dateFilter', '')

    # Get all slots for this provider
    slotsQuerySet = AppointmentSlot.objects.filter(providerUsername=request.user.username)
    slotsQuerySet = filterNonPastAppointments(slotsQuerySet)
    filteredSlots = filterAppointments(slotsQuerySet, search, typeFilter, dateFilter)

    # Collect unique types for the filter dropdown
    types = sorted(set(slot.appointmentType.strip() for slot in slotsQuerySet))

    return render(request, 'providerDashboard.html', {
        'provider': provider_profile,
        'slots': filteredSlots,
        'slot_form': slot_form,
        'types': types,
        'searchInput': search,
        'typeFilter': typeFilter,
        'dateFilter': dateFilter,
    })


@never_cache
@csrf_protect
def userDashboard(request):
    if not request.user.is_authenticated:
        return redirect('login')

    # Load cancellation messages
    user_profile = getattr(request.user, 'userprofile', None)
    canceled_msgs = user_profile.get_and_clear_canceled_msgs() if user_profile else []

    # Booked appointments for the user
    bookings = Booking.objects.filter(user=request.user).select_related("slot")

    # Handle filters
    search = request.GET.get('searchInput', '').strip().lower()
    typeFilter = request.GET.get('typeFilter', '')
    dateFilter = request.GET.get('dateFilter', '')
    bookedSearch = request.GET.get('bookedSearchInput', '').strip().lower()
    bookedTypeFilter = request.GET.get('bookedTypeFilter', '')

    # Booked appointments for the user
    bookingsQuerySet = Booking.objects.filter(user=request.user).select_related("slot")
    bookingsQuerySet  = filterNonPastBookings(bookingsQuerySet)
    bookings = filterBookings(bookingsQuerySet, bookedSearch, bookedTypeFilter)


    # Get all appointment slots
    slotsQuerySet = AppointmentSlot.objects.filter(is_booked=False)
    slotsQuerySet = filterNonPastAppointments(slotsQuerySet)
    slots = filterAppointments(slotsQuerySet, search, typeFilter, dateFilter)

    # Get all types for dropdown
    types = sorted(set(slot.appointmentType.strip() for slot in slotsQuerySet))

    # Render template
    return render(request, 'userDashboard.html', {
        'canceled_msgs': canceled_msgs,
        'bookings': bookings,
        'slots': slots,
        'types': types,
        'searchInput': search,
        'typeFilter': typeFilter,
        'dateFilter': dateFilter,
        'bookedSearchInput': bookedSearch,
        'bookedTypeFilter': bookedTypeFilter,
    })


@never_cache
@csrf_protect
def adminDashboard(request):
    # Only allow access for superusers or staff
    if not request.user.is_authenticated or not (request.user.is_superuser or request.user.is_staff):
        messages.error(request, "Access denied: This page is for administrators only.")
        return redirect('home')

    view_mode = request.GET.get('view', 'appointments')

    if request.method == "POST":
        # Handle appointment cancellation
        if view_mode == 'appointments':
            slot_id = request.POST.get("slot_id")
            slot = get_object_or_404(AppointmentSlot, id=slot_id)
            booking = Booking.objects.filter(slot=slot).first()
            start_time_str = convertFromMilitaryTime(slot.start_time)
            end_time_str = convertFromMilitaryTime(slot.end_time)
            date_str = slot.date.strftime('%m/%d/%Y')
            if booking:
                user_profile = getattr(booking.user, 'userprofile', None)
                if user_profile:
                    msg_user = (
                        f"Your appointment '{slot.appointmentName}' with {slot.providerFirstName} {slot.providerLastName} "
                        f"on {date_str} at {start_time_str}-{end_time_str} was canceled by an administrator."
                    )
                    append_cancel_message(user_profile, msg_user)
                provider_profile = ServiceProvider.objects.filter(user__username=slot.providerUsername).first()
                if provider_profile:
                    msg_provider = (
                        f"An administrator canceled '{slot.appointmentName}' with {booking.user.get_full_name()} "
                        f"on {date_str} at {start_time_str}-{end_time_str}."
                    )
                    append_cancel_message(provider_profile, msg_provider)
                booking.delete()
            slot.delete()
            messages.success(request, "Appointment canceled and removed.")
            return redirect(f'{request.path}?view=appointments')
        # Handle user/provider removal
        elif view_mode == 'users':
            username = request.POST.get("username")
            if deleteUserAndProfile(username):
                messages.success(request, "User/Provider account deleted.")
            else:
                messages.error(request, "User not found.")
            return redirect(f'{request.path}?view=users')

    if view_mode == 'appointments':
        search = request.GET.get('searchInput', '')
        typeFilter = request.GET.get('typeFilter', '')
        dateFilter = request.GET.get('dateFilter', '')
        slots = AppointmentSlot.objects.all()
        items = filterAppointments(slots, search, typeFilter, dateFilter)
        types = sorted(set(slot.appointmentType.strip() for slot in slots))
        context = {
            'view_mode': 'appointments',
            'items': items,
            'types': types,
            'searchInput': search,
            'typeFilter': typeFilter,
            'dateFilter': dateFilter,
        }
        return render(request, 'adminDashboard.html', context)
    else:
        userSearchInput = request.GET.get('userSearchInput', '')
        userTypeFilter = request.GET.get('userTypeFilter', '')
        user_profiles = UserProfile.objects.select_related('user').all()
        provider_profiles = ServiceProvider.objects.select_related('user').all()
        user_profiles, provider_profiles = filterUsers(
            user_profiles, provider_profiles,
            search=userSearchInput,
            typeFilter=userTypeFilter
        )
        slots = AppointmentSlot.objects.all()
        types = sorted(set(slot.appointmentType.strip() for slot in slots))
        context = {
            'view_mode': 'users',
            'user_profiles': user_profiles,
            'provider_profiles': provider_profiles,
            'userSearchInput': userSearchInput,
            'userTypeFilter': userTypeFilter,
            'types': types,
        }
        return render(request, 'adminDashboard.html', context)

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
    
@never_cache
@csrf_protect
def downloadUserReport(request):
    if request.method == "POST":
        username = request.POST.get("username")
        start_date = request.POST.get("start_date")
        end_date = request.POST.get("end_date")
        appointment_type = request.POST.get("appointment_type") or None
        response = generateUserAppointmentsCsv(username, start_date, end_date, appointment_type)
        if response:
            return response
        messages.error(request, "User not found or no data.")
        return redirect('adminDashboard')
    return redirect('adminDashboard')

@never_cache
@csrf_protect
def downloadAllUsersReport(request):
    if request.method == "POST":
        start_date = request.POST.get("start_date")
        end_date = request.POST.get("end_date")
        appointment_type = request.POST.get("appointment_type") or None
        response = generateAllUsersReport(start_date, end_date, appointment_type)
        return response
    return redirect('adminDashboard')

@never_cache
@csrf_protect
def downloadProviderReport(request):
    if request.method == "POST":
        username = request.POST.get("username")
        start_date = request.POST.get("start_date")
        end_date = request.POST.get("end_date")
        response = generateProviderAppointmentsCsv(username, start_date, end_date)
        if response:
            return response
        messages.error(request, "Provider not found or no data.")
        return redirect('adminDashboard')
    return redirect('adminDashboard')

@never_cache
@csrf_protect
def downloadAllProvidersReport(request):
    if request.method == "POST":
        start_date = request.POST.get("start_date")
        end_date = request.POST.get("end_date")
        appointment_type = request.POST.get("appointment_type") or None
        response = generateAllProvidersReport(start_date, end_date, appointment_type)
        return response
    return redirect('adminDashboard')
