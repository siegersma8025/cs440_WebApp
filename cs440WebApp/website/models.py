from django.db import models
from django.contrib.auth.models import User
# Create your models here.

class ServiceProvider(models.Model):
    categortyChoices = [ ('medical', 'Medical'), ('beauty', 'Beauty'), ('fitness', 'Fitness'),]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    providerName = models.CharField(max_length=50)
    category = models.CharField(max_length=20, choices=categortyChoices)

    def __str__(self):
        return f"{self.providerName} ({self.get_category_display()})"
    
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    # Add any custom fields you want for users
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)

    def __str__(self):
        return f"UserProfile: {self.user.username}"
    
class AdminProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    # Add any admin-specific fields here

    def __str__(self):
        return f"AdminProfile: {self.user.username}"
    
# Appointment slots created by providers
class AppointmentSlot(models.Model):
    provider = models.ForeignKey(ServiceProvider, on_delete=models.CASCADE, related_name='slots')
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_booked = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.provider.provider_name}: {self.date} {self.start_time}-{self.end_time}"

# Booking: user books an available slot
class Booking(models.Model):
    slot = models.OneToOneField(AppointmentSlot, on_delete=models.CASCADE, related_name='booking')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    booked_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} booked {self.slot}"