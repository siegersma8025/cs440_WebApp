import csv
from django.db import connection
from .models import UserProfile, ServiceProvider, Booking, AppointmentSlot, User
from django.http import HttpResponse

# File containing helper functions in filtering table views
def convertFromMilitaryTime(timeStamp):
    return timeStamp.strftime('%I:%M %p').lstrip('0').replace(' 0', ' ')

def filterNonPastAppointments(queryset):
    nonPastAppointments = []
    for item in queryset:
        if not item.isPast():
            nonPastAppointments.append(item)
    return nonPastAppointments

def filterNonPastBookings(bookings):
    nonPastBookings = []
    for booking in bookings:
        if not booking.slot.isPast():
            nonPastBookings.append(booking)
    return nonPastBookings

def filterAppointments(appointmentSlots, search='', typeFilter='', dateFilter=''):
    filtered = []
    
    # Grab string from search box and convert to lowercase for case-insensitive comparison
    search = search.strip().lower()
    
    for slot in appointmentSlots:
        # Display date as M:D:Y
        formattedDate = slot.date.strftime('%m-%d-%Y')
        booking = getattr(slot, 'booking', None)
        user_name = booking.user.get_full_name() if booking else "Unbooked"
        providerName = f"{slot.providerFirstName} {slot.providerLastName}"
        
        # Partial, case-insensitive search for appointment name, user, or provider
        if search:
            # Check if string entered is in appointment name, user name, or provider name
            combined = f"{slot.appointmentName} {user_name} {providerName}".lower()
            
            if search not in combined:
                continue

        if typeFilter and slot.appointmentType != typeFilter:
            continue

        if dateFilter and slot.date.strftime('%Y-%m-%d') != dateFilter:
            continue
        
        # Add relevant appointment details to the filtered list, including slotId
        filtered.append({
            'slotId': slot.id,
            'userName': user_name,
            'providerName': providerName,
            'appointmentName': slot.appointmentName,
            'appointmentType': slot.appointmentType,
            'date': formattedDate,
            'time': f"{convertFromMilitaryTime(slot.startTime)} - {convertFromMilitaryTime(slot.endTime)}",
            'startTime': slot.startTime,
            'endTime': slot.endTime,
            'isPast': slot.isPast(),
        })
        # Sort so non-past appointments come first
    filtered.sort(key=lambda x: x['isPast'])
    # Return the filtered list of appointments
    return filtered


def filterUsers(userProfiles, providerProfiles, search='', typeFilter=''):
    search = search.strip().lower()

    # Filter by type
    if typeFilter == "User":
        providerProfiles = []
    elif typeFilter == "Provider":
        userProfiles = []

    # Filter by search
    def matches(profile):
        username = profile.user.username.lower()
        fullName = f"{getattr(profile, 'firstName', '')} {getattr(profile, 'lastName', '')}".strip().lower()
        return search in username or search in fullName

    # Generate filtered lists of users/providers matching the search criteria
    filteredUserProfiles = []
    for p in userProfiles:
        if matches(p):
            filteredUserProfiles.append(p)

    filteredProviderProfiles = []
    for p in providerProfiles:
        if matches(p):
            filteredProviderProfiles.append(p)

    return filteredUserProfiles, filteredProviderProfiles


def filterBookings(bookings, search='', typeFilter=''):
    search = search.strip().lower()
    filtered = []
    for booking in bookings:
        slot = booking.slot
        provider_name = f"{slot.providerFirstName} {slot.providerLastName}"
        if search:
            combined = f"{slot.appointmentName} {slot.providerUsername} {provider_name}".lower()
            if search not in combined:
                continue
        if typeFilter and slot.appointmentType != typeFilter:
            continue
        filtered.append(booking)
    return filtered

# Based on username, delete user and associated profile/provider entries from the database
def deleteUserAndProfile(username):
    # Get user id from auth_user
    with connection.cursor() as cursor:
        cursor.execute("SELECT id FROM auth_user WHERE username = %s", [username])
        row = cursor.fetchone()
        if not row:
            return False  # User not found
        userId = row[0]

    # Delete related bookings first
    Booking.objects.filter(user_id=userId).delete()
    # Delete from UserProfile if exists
    UserProfile.objects.filter(user_id=userId).delete()
    # Delete from ServiceProvider if exists
    ServiceProvider.objects.filter(user_id=userId).delete()
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
        if booking.bookedAt:
            bookedAtDate = booking.bookedAt.strftime('%m-%d-%Y')
            bookedAtTime = convertFromMilitaryTime(booking.bookedAt)
            formattedBookedAt = f"{bookedAtDate} {bookedAtTime}"
        else:
            formattedBookedAt = ''
        writer.writerow([
            slot.appointmentName,
            slot.appointmentType,
            f"{slot.providerFirstName} {slot.providerLastName}",
            slot.date,
            slot.startTime,
            slot.endTime,
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
        if booking.bookedAt:
            bookedAtDate = booking.bookedAt.strftime('%m-%d-%Y')
            bookedAtTime = convertFromMilitaryTime(booking.bookedAt)
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
            slot.startTime,
            slot.endTime,
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
        bookedAt = (f"{booking.bookedAt.strftime('%m-%d-%Y')} {convertFromMilitaryTime(booking.bookedAt)}"
                    if booking and booking.bookedAt else '')
        bookedFlag = 'Yes' if booking else 'No'
        writer.writerow([
            slot.appointmentName,
            slot.date.strftime('%m-%d-%Y'),
            userBooked,
            convertFromMilitaryTime(slot.startTime),
            convertFromMilitaryTime(slot.endTime),
            bookedAt,
            bookedFlag
        ])
    return response

def generateAllProvidersReport(startDate, endDate, appointmentType=None):
    slots = AppointmentSlot.objects.filter(
        date__gte=startDate,
        date__lte=endDate
    )
    if appointmentType:
        slots = slots.filter(appointmentType=appointmentType)
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="All_Providers_Appointments_Report.csv"'
    writer = csv.writer(response)
    writer.writerow([
        'Provider Username', 'Provider Name', 'Appointment Name', 'Appointment Type', 'Date', 'Start Time', 'End Time', 'Booked', 'Booked By'
    ])
    for slot in slots:
        booking = Booking.objects.filter(slot=slot).first()
        bookedFlag = 'Yes' if booking else 'No'
        bookedBy = booking.user.get_full_name() if booking else ''
        writer.writerow([
            slot.providerUsername,
            f"{slot.providerFirstName} {slot.providerLastName}",
            slot.appointmentName,
            slot.appointmentType,
            slot.date,
            slot.startTime,
            slot.endTime,
            bookedFlag,
            bookedBy
        ])
    return response

