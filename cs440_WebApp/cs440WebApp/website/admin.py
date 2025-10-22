from django.contrib import admin
from .models import ServiceProvider, UserProfile, AdminProfile, AppointmentSlot, Booking

# Register models for Django admin interface
admin.site.register(ServiceProvider)
admin.site.register(UserProfile)
admin.site.register(AdminProfile)
admin.site.register(AppointmentSlot)
admin.site.register(Booking)
