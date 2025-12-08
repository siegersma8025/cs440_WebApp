from django.db import connection
from .models import UserProfile, ServiceProvider

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