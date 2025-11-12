import json
from django.db import models
from django.contrib.auth.models import User


# Service provider object/model that will be used to push to database
class ServiceProvider(models.Model):
    categoryChoices = [ ('Medical', 'Medical'), ('Beauty', 'Beauty'), ('Fitness', 'Fitness'),]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    category = models.CharField(max_length=20, choices=categoryChoices)
    qualifications = models.TextField(max_length=200, default="Qualifications")
    first_name = models.CharField(max_length=50, default="Provider")
    last_name = models.CharField(max_length=50, default="Name")
    canceled_msgs = models.TextField(default="[]", blank=True)  # Store as JSON list

    def get_and_clear_canceled_msgs(self):
        msgs = json.loads(self.canceled_msgs)
        self.canceled_msgs = "[]"
        self.save()
        return msgs
    
# User object/model that will be used to push to database
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    canceled_msgs = models.TextField(default="[]", blank=True)  # Store as JSON list

    def get_and_clear_canceled_msgs(self):
        msgs = json.loads(self.canceled_msgs)
        self.canceled_msgs = "[]"
        self.save()
        return msgs

    
# Admin object/model that will be used to push to database
class AdminProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    
# AppointmentSlot: available slots created by service providers
class AppointmentSlot(models.Model):
    appointmentName = models.CharField(max_length=100, default="Appointment")
    appointmentType = models.CharField(max_length=100, default="General")
    providerUsername = models.CharField(max_length=150, default="provider")
    providerFirstName = models.CharField(max_length=50, default="FirstName")
    providerLastName = models.CharField(max_length=50, default="LastName")
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_booked = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        # Check if duplicate exists
        duplicate = AppointmentSlot.objects.filter(
            providerUsername=self.providerUsername,
            date=self.date,
            start_time=self.start_time,
            end_time=self.end_time
        ).exclude(pk=self.pk).exists()
        
        if duplicate:
            raise Exception("This time slot already exists!")
        
        super().save(*args, **kwargs)

# Booking: booked slots by users
class Booking(models.Model):
    slot = models.OneToOneField(AppointmentSlot, on_delete=models.CASCADE, related_name='booking')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    booked_at = models.DateTimeField(auto_now_add=True)


    cancel_message = models.TextField(blank=True)
    canceled_at = models.DateTimeField(null=True, blank=True)

