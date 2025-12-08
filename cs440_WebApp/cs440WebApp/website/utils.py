import csv
from django.db import connection
from .models import UserProfile, ServiceProvider, Booking, AppointmentSlot, User
from django.http import HttpResponse

# File containing helper functions in filtering table views
def convertFromMilitaryTime(timeStamp):
    return timeStamp.strftime('%I:%M %p').lstrip('0').replace(' 0', ' ')

def filter_non_past_appointments(queryset):
    """
    Filter out past appointments from a queryset or list.
    Returns a list of appointments that are not in the past.
    """
    return [item for item in queryset if not item.is_past()]

def filter_non_past_bookings(bookings):
    """
    Filter out past bookings from a queryset or list.
    Returns a list of bookings whose appointment slots are not in the past.
    """
    return [booking for booking in bookings if not booking.slot.is_past()]

def filterAppointments(appointmentSlots, search='', typeFilter='', dateFilter=''):
    filtered = []
    
    # Grab string from search box and convert to lowercase for case-insensitive comparison
    search = search.strip().lower()
    
    for slot in appointmentSlots:
        # Display date as M:D:Y
        formattedDate = slot.date.strftime('%m-%d-%Y')
        booking = getattr(slot, 'booking', None)
        user_name = booking.user.get_full_name() if booking else "Unbooked"
        provider_name = f"{slot.providerFirstName} {slot.providerLastName}"
        
        # Partial, case-insensitive search for appointment name, user, or provider
        if search:
            # Check if string entered is in appointment name, user name, or provider name
            combined = f"{slot.appointmentName} {user_name} {provider_name}".lower()
            
            if search not in combined:
                continue

        if typeFilter and slot.appointmentType != typeFilter:
            continue

        if dateFilter and slot.date.strftime('%Y-%m-%d') != dateFilter:
            continue
        
        # Add relevant appointment details to the filtered list, including slot_id
        filtered.append({
            'slot_id': slot.id,
            'user_name': user_name,
            'provider_name': provider_name,
            'appointment_name': slot.appointmentName,
            'appointment_type': slot.appointmentType,
            'date': formattedDate,
            'time': f"{convertFromMilitaryTime(slot.start_time)} - {convertFromMilitaryTime(slot.end_time)}",
        })
    # Return the filtered list of appointments
    return filtered


def filterUsers(user_profiles, provider_profiles, search='', typeFilter=''):
    """
    Filters user_profiles and provider_profiles by type and search string.
    - typeFilter: 'User', 'Provider', or '' (all)
    - search: partial, case-insensitive match on username or full name
    Returns: (filtered_user_profiles, filtered_provider_profiles)
    """
    search = search.strip().lower()

    # Filter by type
    if typeFilter == "User":
        provider_profiles = []
    elif typeFilter == "Provider":
        user_profiles = []

    # Filter by search
    def matches(profile):
        username = profile.user.username.lower()
        full_name = f"{profile.first_name} {profile.last_name}".lower()
        return search in username or search in full_name

    if search:
        user_profiles = [p for p in user_profiles if matches(p)]
        provider_profiles = [p for p in provider_profiles if matches(p)]

    return user_profiles, provider_profiles

# Based on username, delete user and associated profile/provider entries from the database
def delete_user_and_profile(username):
    """
    Deletes a user and their associated profile/provider entries from the database.
    - Looks up the user id from auth_user by username.
    - Deletes from UserProfile or ServiceProvider by user id.
    - Deletes from auth_user by username.
    """
    # Get user id from auth_user
    with connection.cursor() as cursor:
        cursor.execute("SELECT id FROM auth_user WHERE username = %s", [username])
        row = cursor.fetchone()
        if not row:
            return False  # User not found
        user_id = row[0]

    # Delete from UserProfile if exists
    UserProfile.objects.filter(user_id=user_id).delete()
    # Delete from ServiceProvider if exists
    ServiceProvider.objects.filter(user_id=user_id).delete()
    # Delete from auth_user using raw SQL to avoid Django's cascades
    with connection.cursor() as cursor:
        cursor.execute("DELETE FROM auth_user WHERE username = %s", [username])
    return True

def generateUserAppointmentsCsv(username, startDate, endDate, appointmentType=None):
    user = User.objects.filter(username=username).first()
    if not user:
        return None
    bookings = Booking.objects.filter(
        user=user,
        slot__date__gte=startDate,
        slot__date__lte=endDate
    )
    if appointmentType:
        bookings = bookings.filter(slot__appointmentType=appointmentType)
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{username}_appointment_report.csv"'
    writer = csv.writer(response)
    writer.writerow([
        'Appointment Name', 'Appointment Type', 'Provider', 'Date', 'Start Time', 'End Time', 'Booked At'
    ])
    for booking in bookings.select_related('slot'):
        slot = booking.slot
        if booking.booked_at:
            bookedAtDate = booking.booked_at.strftime('%m-%d-%Y')
            bookedAtTime = convertFromMilitaryTime(booking.booked_at)
            formattedBookedAt = f"{bookedAtDate} {bookedAtTime}"
        else:
            formattedBookedAt = ''
        writer.writerow([
            slot.appointmentName,
            slot.appointmentType,
            f"{slot.providerFirstName} {slot.providerLastName}",
            slot.date,
            slot.start_time,
            slot.end_time,
            formattedBookedAt
        ])
    return response

def generateAllUsersReport(startDate, endDate, appointmentType=None):
    bookings = Booking.objects.filter(
        slot__date__gte=startDate,
        slot__date__lte=endDate
    )
    if appointmentType:
        bookings = bookings.filter(slot__appointmentType=appointmentType)
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="All_Appointments_Report.csv"'
    writer = csv.writer(response)
    writer.writerow([
        'Username', 'Full Name', 'Appointment Name', 'Appointment Type', 'Provider', 'Date', 'Start Time', 'End Time', 'Booked At'
    ])
    for booking in bookings.select_related('slot', 'user'):
        slot = booking.slot
        user = booking.user
        if booking.booked_at:
            bookedAtDate = booking.booked_at.strftime('%m-%d-%Y')
            bookedAtTime = convertFromMilitaryTime(booking.booked_at)
            formattedBookedAt = f"{bookedAtDate} {bookedAtTime}"
        else:
            formattedBookedAt = ''
        writer.writerow([
            user.username,
            f"{user.first_name} {user.last_name}",
            slot.appointmentName,
            slot.appointmentType,
            f"{slot.providerFirstName} {slot.providerLastName}",
            slot.date,
            slot.start_time,
            slot.end_time,
            formattedBookedAt
        ])
    return response

def generateProviderAppointmentsCsv(username, startDate, endDate):
    provider = ServiceProvider.objects.filter(user__username=username).first()
    if not provider:
        return None
    slots = AppointmentSlot.objects.filter(
        providerUsername=username,
        date__gte=startDate,
        date__lte=endDate
    ).select_related('booking')
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{username}_provider_appointment_report.csv"'
    writer = csv.writer(response)
    writer.writerow([
        'Appointment Name', 'Date', 'User Booked', 'Start Time', 'End Time', 'Booked At', 'Booked'
    ])
    for slot in slots:
        booking = Booking.objects.filter(slot=slot).first()
        userBooked = booking.user.get_full_name() if booking else ''
        bookedAt = (f"{booking.booked_at.strftime('%m-%d-%Y')} {convertFromMilitaryTime(booking.booked_at)}"
                    if booking and booking.booked_at else '')
        bookedFlag = 'Yes' if booking else 'No'
        writer.writerow([
            slot.appointmentName,
            slot.date.strftime('%m-%d-%Y'),
            userBooked,
            convertFromMilitaryTime(slot.start_time),
            convertFromMilitaryTime(slot.end_time),
            bookedAt,
            bookedFlag
        ])
    return response