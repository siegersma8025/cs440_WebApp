# Import necessary Django modules (any functions with underscores are django built-in functions)
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
def checkAuthenticationAndRole(request, roleCheck, errorMessage):
    #Centralized authentication and role checking
    if not request.user.is_authenticated:
        messages.error(request, "Please log in to access this page.")
        return redirect('home')
    if not roleCheck(request.user):
        messages.error(request, errorMessage)
        return redirect('home')
    return None


# Custom decorators for role-based access control
def userRequired(viewFunction):
    #Decorator to ensure only regular users can access this view
    def wrapper(request, *args, **kwargs):
        redirect_response = checkAuthenticationAndRole(
            request, 
            lambda user: hasattr(user, 'userprofile'),
            "Access denied: This page is for registered users only."
        )
        return redirect_response or viewFunction(request, *args, **kwargs)
    return wrapper


def providerRequired(viewFunction):
    #Decorator to ensure only service providers can access this view
    def wrapper(request, *args, **kwargs):
        redirect_response = checkAuthenticationAndRole(
            request,
            lambda user: hasattr(user, 'serviceprovider'),
            "Access denied: This page is for service providers only."
        )
        return redirect_response or viewFunction(request, *args, **kwargs)
    return wrapper


def adminRequired(view_func):
    #Decorator to ensure only admins can access this view
    def wrapper(request, *args, **kwargs):
        redirect_response = checkAuthenticationAndRole(
            request,
            lambda user: user.is_superuser or user.is_staff or hasattr(user, 'adminprofile'),
            "Access denied: This page is for administrators only."
        )
        return redirect_response or view_func(request, *args, **kwargs)
    return wrapper


def helpView(request):
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
                    # User exists but has no profile
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
                firstName=form.cleaned_data['firstName'],
                lastName=form.cleaned_data['lastName']
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
            form.save()
            messages.success(request, "Registration Successful! You can now log in.")
            return redirect('home')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ProviderSignUpForm()
    return render(request, 'registerProvider.html', {'form': form})


@never_cache
@providerRequired
def providerDashboard(request):
    try:
        # Get provider profile from database via model
        providerProfile = ServiceProvider.objects.get(user=request.user)
    except ServiceProvider.DoesNotExist:
        messages.error(request, "Access denied: You are not registered as a provider.")
        return redirect('home')

    # Get and clear canceled messages for provider
    canceledMsgs = providerProfile.getAndClearCanceledMsgs()

    # Handle new slot form submission
    if request.method == "POST":
        slotForm = AppointmentSlotForm(request.POST)
        if slotForm.is_valid():
            slotForm.save(providerProfile)
            messages.success(request, "Appointment slot added successfully.")
            return redirect('providerDashboard')
    else:
        slotForm = AppointmentSlotForm()

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
        'provider': providerProfile,
        'slots': filteredSlots,
        'slotForm': slotForm,
        'types': types,
        'searchInput': search,
        'typeFilter': typeFilter,
        'dateFilter': dateFilter,
        'canceledMsgs': canceledMsgs,
    })


@never_cache
@csrf_protect
def userDashboard(request):
    try:
        # Get provider profile from database via model
        userProfile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        messages.error(request, "Access denied: You are not registered as a user.")
        return redirect('home')
    
    canceledMsgs = userProfile.getAndClearCanceledMsgs()

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
    slotsQuerySet = AppointmentSlot.objects.filter(isBooked=False)
    slotsQuerySet = filterNonPastAppointments(slotsQuerySet)
    slots = filterAppointments(slotsQuerySet, search, typeFilter, dateFilter)

    # Get all types for dropdown
    types = sorted(set(slot.appointmentType.strip() for slot in slotsQuerySet))

    # Render template
    return render(request, 'userDashboard.html', {
        'canceledMsgs': canceledMsgs,
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

    viewMode = request.GET.get('view', 'appointments')

    if request.method == "POST":
        # Handle appointment cancellation
        if viewMode == 'appointments':
            slotID = request.POST.get("slotId")
            slot = get_object_or_404(AppointmentSlot, id=slotID)
            booking = Booking.objects.filter(slot=slot).first()
            formattedStartTime = convertFromMilitaryTime(slot.startTime)
            formattedEndTime = convertFromMilitaryTime(slot.endTime)
            formattedDate = slot.date.strftime('%m/%d/%Y')
            providerProfile = ServiceProvider.objects.filter(user__username=slot.providerUsername).first()
            if booking:
                userProfile = UserProfile.objects.filter(user=booking.user).first()
                # User cancelation message
                if userProfile:
                    userCancelMsg = (f"Your appointment '{slot.appointmentName}' with {slot.providerFirstName} {slot.providerLastName} "f"on {formattedDate} at {formattedStartTime}-{formattedEndTime} was canceled by an administrator.")
                    appendCancelMessage(userProfile, userCancelMsg)
                # Provider cancelation message
                if providerProfile:
                    msg_provider = (f"Your appointment '{slot.appointmentName}' with {booking.user.get_full_name()} "f"on {formattedDate} at {formattedStartTime}-{formattedEndTime} was canceled by an administrator.")
                    appendCancelMessage(providerProfile, msg_provider)
                # Delete/remove booking
                booking.delete()
            else:
                # If slot was not booked and canceled, just notify provider
                if providerProfile:
                    msg_provider = (f"Your appointment '{slot.appointmentName}' "f"on {formattedDate} at {formattedStartTime}-{formattedEndTime} was canceled by an administrator.")
                    appendCancelMessage(providerProfile, msg_provider)
            # Delete/appointment slot
            slot.delete()
            messages.success(request, "Appointment canceled and removed.")
            return redirect(f'{request.path}?view=appointments')
       
        # Handle user/provider removal
        elif viewMode == 'users':
            username = request.POST.get("username")
            if deleteUserAndProfile(username):
                messages.success(request, "User/Provider account deleted.")
            else:
                messages.error(request, "User not found.")
            return redirect(f'{request.path}?view=users')

    if viewMode == 'appointments':
        search = request.GET.get('searchInput', '')
        typeFilter = request.GET.get('typeFilter', '')
        dateFilter = request.GET.get('dateFilter', '')
        slots = AppointmentSlot.objects.all()
        items = filterAppointments(slots, search, typeFilter, dateFilter)
        # Set creates a list of unique items no matter the number of times they appear
        types = sorted(set(slot.appointmentType.strip() for slot in slots))
        context = {
            'viewMode': 'appointments',
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
        allUserProfiles = UserProfile.objects.select_related('user').all()
        allProviderProfiles = ServiceProvider.objects.select_related('user').all()
        # utilize filter (will return filtered user and provider profiles based on results from search and filter bar in app)
        allUserProfiles, allProviderProfiles = filterUsers(
            allUserProfiles, allProviderProfiles,
            search=userSearchInput,
            typeFilter=userTypeFilter
        )
        slots = AppointmentSlot.objects.all()
        types = sorted(set(slot.appointmentType.strip() for slot in slots))
        context = {
            'viewMode': 'users',
            'allUserProfiles': allUserProfiles,
            'allProviderProfiles': allProviderProfiles,
            'userSearchInput': userSearchInput,
            'userTypeFilter': userTypeFilter,
            'types': types,
        }
        return render(request, 'adminDashboard.html', context)

@userRequired
@csrf_protect
def bookAppointment(request, slotId):
    slot = get_object_or_404(AppointmentSlot, id=slotId, isBooked=False)

    if request.method == "POST":
        # Check for conflicting appointments for this user
        userBookings = Booking.objects.filter(user=request.user, slot__date=slot.date)
        for booking in userBookings:
            bookedSlot = booking.slot
            # If times overlap, block booking
            if (slot.startTime < bookedSlot.endTime and slot.endTime > bookedSlot.startTime):
                messages.error(
                    request,
                    f"Conflicting appointment: You already have '{bookedSlot.appointmentName}' from "
                    f"{convertFromMilitaryTime(bookedSlot.startTime)} to {convertFromMilitaryTime(bookedSlot.endTime)} on {bookedSlot.date.strftime('%m/%d/%Y')}."
                )
                return redirect('userDashboard') 

        # Double-check that slot is still available
        if slot.isBooked:
            messages.error(request, "Sorry, this appointment has already been booked.")
            return redirect('userDashboard')

        slot.isBooked = True
        slot.save()
        Booking.objects.create(slot=slot, user=request.user)
        messages.success(request, "Appointment booked successfully!")
        return redirect('userDashboard')
    else:
        messages.error(request, "Invalid request method.")
        return redirect('userDashboard') 

def appendCancelMessage(profile, message):
    if profile:
        import json
        msgs = json.loads(profile.canceledMsgs)
        msgs.append(message)
        profile.canceledMsgs = json.dumps(msgs)
        profile.save()

@csrf_protect
def cancelAppointment(request, slotId):
    slot = get_object_or_404(AppointmentSlot, id=slotId)
    booking = Booking.objects.filter(slot=slot).first()

    isProvider = hasattr(request.user, 'serviceprovider') and slot.providerUsername == request.user.username
    isUser = booking and hasattr(request.user, 'userprofile') and booking.user == request.user

    if not (isUser or isProvider):
        messages.error(request, "Access denied: This page is for registered users or providers only.")
        return redirect('home')

    formattedStartTime = convertFromMilitaryTime(slot.startTime)
    formattedEndTime = convertFromMilitaryTime(slot.endTime)
    formattedDate = slot.date.strftime('%m/%d/%Y')  # Month/Day/Year format

    if isUser:
        # User cancels: add message for provider, remove booking
        providerProfile = ServiceProvider.objects.filter(user__username=slot.providerUsername).first()
        msg = f"{booking.user.get_full_name()} canceled '{slot.appointmentName}' with you on {formattedDate} at {formattedStartTime}-{formattedEndTime}."
        appendCancelMessage(providerProfile, msg)
        booking.delete()
        slot.isBooked = False
        slot.save()
        messages.success(request, "Appointment canceled.")
        return redirect("userDashboard")
    
    elif isProvider:
        # Provider cancels: add message for user if booked, remove booking if exists, always remove slot
        if booking:
            userProfile = UserProfile.objects.filter(user=booking.user).first()
            msg = f"Your appointment '{slot.appointmentName}' with {slot.providerFirstName} {slot.providerLastName} on {formattedDate} at {formattedStartTime}-{formattedEndTime} was canceled by {slot.providerFirstName}."
            appendCancelMessage(userProfile, msg)
            booking.delete()
        slot.delete()
        messages.success(request, "Appointment slot canceled and removed.")
        return redirect("providerDashboard")
    
@never_cache
@csrf_protect
def downloadUserReport(request):
    if request.method == "POST":
        username = request.POST.get("username")
        startDate = request.POST.get("startDate")
        endDate = request.POST.get("endDate")
        appointmentType = request.POST.get("appointmentType") or None
        response = generateUserAppointmentsCsv(username, startDate, endDate, appointmentType)
        if response:
            return response
        messages.error(request, "User not found or no data.")
        return redirect('adminDashboard')
    return redirect('adminDashboard')

@never_cache
@csrf_protect
def downloadAllUsersReport(request):
    if request.method == "POST":
        startDate = request.POST.get("startDate")
        endDate = request.POST.get("endDate")
        appointmentType = request.POST.get("appointmentType") or None
        response = generateAllUsersReport(startDate, endDate, appointmentType)
        return response
    return redirect('adminDashboard')

@never_cache
@csrf_protect
def downloadProviderReport(request):
    if request.method == "POST":
        username = request.POST.get("username")
        startDate = request.POST.get("startDate")
        endDate = request.POST.get("endDate")
        response = generateProviderAppointmentsCsv(username, startDate, endDate)
        if response:
            return response
        messages.error(request, "Provider not found or no data.")
        return redirect('adminDashboard')
    return redirect('adminDashboard')

@never_cache
@csrf_protect
def downloadAllProvidersReport(request):
    if request.method == "POST":
        startDate = request.POST.get("startDate")
        endDate = request.POST.get("endDate")
        appointmentType = request.POST.get("appointmentType") or None
        response = generateAllProvidersReport(startDate, endDate, appointmentType)
        return response
    return redirect('adminDashboard')
