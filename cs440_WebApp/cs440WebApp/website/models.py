from django.db import models
from django.contrib.auth.models import User

# Service provider object/model that will be used to push to database
class ServiceProvider(models.Model):
    categoryChoices = [ ('medical', 'Medical'), ('beauty', 'Beauty'), ('fitness', 'Fitness'),]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    category = models.CharField(max_length=20, choices=categoryChoices)
    qualifications = models.TextField(max_length=200, default="Qualifications")
    first_name = models.CharField(max_length=50, default="Provider")
    last_name = models.CharField(max_length=50, default="Name")

    # String representation of a "ServiceProvider" object
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.get_category_display()})"
    
# User object/model that will be used to push to database
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)

    # String representation of a "User" object
    def __str__(self):
        return f"UserProfile: {self.user.username}"
    
# Admin object/model that will be used to push to database
class AdminProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    # String representation of an "Admin" object
    def __str__(self):
        return f"AdminProfile: {self.user.username}"
    
# AppointmentSlot: available slots created by service providers
class AppointmentSlot(models.Model):
    appointmentName = models.CharField(max_length=100, default="Appointment")
    providerUsername = models.CharField(max_length=150, default="provider")
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_booked = models.BooleanField(default=False)

    # String representation of an "AppointmentSlot" object
    def __str__(self):
        return f"{self.appointmentName}: {self.date} {self.start_time}-{self.end_time}"

# Booking: booked slots by users
class Booking(models.Model):
    slot = models.OneToOneField(AppointmentSlot, on_delete=models.CASCADE, related_name='booking')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    booked_at = models.DateTimeField(auto_now_add=True)

    # String representation of a "Booking" object
    def __str__(self):
        return f"{self.user.username} booked {self.slot}"