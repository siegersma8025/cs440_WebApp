from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import *
from .models import *

# Each view is essentially a function that takes in a request and returns a response
# The response is usually a rendered HTML template
# The request can be a GET or POST request
def home(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            # Check for Django admin first
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
        form = UserSignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Create UserProfile object
            UserProfile.objects.create(
                user=user,
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name']
            )
            messages.success(request, "Registration Successful!")
            return redirect('home')
    else:
        form = UserSignUpForm()
    return render(request, 'registerUser.html', {'form': form})

def registerProvider(request):
    if request.method == "POST":
        form = ProviderSignUpForm(request.POST)
        if form.is_valid():
            user = form.save()  # This already creates both User and ServiceProvider
            messages.success(request, "Registration Successful!")
            return redirect('home')
    else:
        form = ProviderSignUpForm()
    return render(request, 'registerProvider.html', {'form': form})




@login_required
def providerDashboard(request):
    provider = ServiceProvider.objects.filter(user=request.user).first()
    slots = AppointmentSlot.objects.filter(providerUsername=request.user.username) if provider else []
    slot_form = AppointmentSlotForm()

    if request.method == "POST":
        slot_form = AppointmentSlotForm(request.POST)
        if slot_form.is_valid() and provider:
            AppointmentSlot.objects.create(
                appointmentName=slot_form.cleaned_data['appointmentName'],
                providerUsername=request.user.username,  # Save provider's username
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

@login_required
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

    form = AppointmentSearchForm(request.POST or None, category_selected=category_selected)

    return render(request, 'userDashboard.html', {
        'form': form,
        'slots': slots,
        'bookings': bookings,
    })
    
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