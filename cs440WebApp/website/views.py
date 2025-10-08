from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import *
from .models import *

# Each view is essentially a function that takes in a request and returns a response
# The response is one of the html files in the templates folder to display the page
# The request can be a GET or POST request
def home(request):
    # On login form submission
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        # If user authentication is successful login the user and redirect to their respective dashboard
        if user is not None:
            # Login the user
            login(request, user)
            if user.is_superuser or user.is_staff:
                return redirect('adminDashboard')
            elif hasattr(user, 'serviceprovider'):
                return redirect('providerDashboard')
            elif hasattr(user, 'userprofile'):
                return redirect('userDashboard')
        else:
            messages.error(request, "Error logging in. Please try again.")
            return redirect('home')
    else:
        return render(request, 'home.html', {})


def logoutUser(request):
    logout(request)
    messages.success(request, "Logged out successfully")
    return redirect('home')


def registerUser(request):
    if request.method == "POST":
        # Create the "User" form instance
        form = UserSignUpForm(request.POST)
        if form.is_valid():
            # Create User object within the form's save() method
            user = form.save()
            # Create UserProfile object that will get sent to database through the models.py file
            UserProfile.objects.create(user = user, first_name = form.cleaned_data['first_name'], last_name = form.cleaned_data['last_name'])
            messages.success(request, "Registration Successful!")
            return redirect('home')
    else:
        form = UserSignUpForm()
    return render(request, 'registerUser.html', {'form': form})

def registerProvider(request):
    if request.method == "POST":
        # Create the "ServiceProvider" form instance
        form = ProviderSignUpForm(request.POST)
        if form.is_valid():
            # Create User and ServiceProvider objects within the form's save() method
            form.save()
            messages.success(request, "Registration Successful!")
            return redirect('home')
    else:
        form = ProviderSignUpForm()
    return render(request, 'registerProvider.html', {'form': form})


@login_required
def providerDashboard(request):
    provider = ServiceProvider.objects.filter(user=request.user).first()
    if provider:
        slots = AppointmentSlot.objects.filter(providerUsername=request.user.username)
    else: 
        slots = []

    slotForm = AppointmentSlotForm()

    if request.method == "POST":
        # Create Appointment Slot form 
        slotForm = AppointmentSlotForm(request.POST)
        # If form is valid and provider exists, create the AppointmentSlot object in the database
        if slotForm.is_valid() and provider:
            AppointmentSlot.objects.create(
                appointmentName=slotForm.cleaned_data['appointmentName'],
                providerUsername=request.user.username,
                providerFirstName=request.user.first_name,
                providerLastName=request.user.last_name,
                appointmentType=provider.category, 
                date=slotForm.cleaned_data['date'],
                start_time=slotForm.cleaned_data['start_time'],
                end_time=slotForm.cleaned_data['end_time']
            )
            messages.success(request, "Appointment slot added!")
            return redirect('providerDashboard')

    return render(request, 'providerDashboard.html', {'slots': slots,'slot_form': slotForm,'provider': provider})

@login_required
def userDashboard(request):
    slots = AppointmentSlot.objects.filter(is_booked=False)
    bookings = Booking.objects.filter(user=request.user)

    categorySelected = None
    dateSelected = None

    if request.method == "POST":
        form = AppointmentSearchForm(request.POST)
        if form.is_valid():
            categorySelected = form.cleaned_data['category']
            dateSelected = form.cleaned_data['date']

            if categorySelected:
                # Get usernames of providers in this category
                provider_usernames = ServiceProvider.objects.filter(category=categorySelected).values_list('user__username', flat=True)
                slots = slots.filter(provider_username__in=provider_usernames)
            if dateSelected:
                slots = slots.filter(date=dateSelected)
    else:
        form = AppointmentSearchForm()

    form = AppointmentSearchForm(request.POST or None, category_selected=categorySelected)

    return render(request, 'userDashboard.html', {'form': form,'slots': slots,'bookings': bookings,})
    
@login_required
def adminDashboard(request):
    # Allow access if the user is a Django superuser or staff
    if request.user.is_superuser or request.user.is_staff or hasattr(request.user, 'adminprofile'):
        return render(request, 'adminDashboard.html')
    else:
        messages.error(request, "Access denied: Admins only.")
        return redirect('home')
    
@login_required
def bookAppointment(request, slot_id):
    slot = AppointmentSlot.objects.get(id=slot_id, is_booked=False)
    if request.method == "POST":
        slot.is_booked = True
        slot.save()
        Booking.objects.create(slot=slot, user=request.user)
        messages.success(request, "Appointment booked successfully!")
        return redirect('userDashboard')
    return redirect('userDashboard')