# File containing helper functions in filtering table views

def filterAppointments(appointmentSlots, search='', typeFilter='', dateFilter=''):
    filtered = []
    
    def convertFromMilitaryTime(timeStamp):
        return timeStamp.strftime('%I:%M %p').lstrip('0').replace(' 0', ' ')
    
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
        
        # Add relevant appointment details to the filtered list
        filtered.append({
            'user_name': user_name,
            'provider_name': provider_name,
            'appointment_name': slot.appointmentName,
            'appointment_type': slot.appointmentType,
            'date': formattedDate,
            'time': f"{convertFromMilitaryTime(slot.start_time)} - {convertFromMilitaryTime(slot.end_time)}",
        })
    # Return the filtered list of appointments
    return filtered