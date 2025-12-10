import json
from django.db import models
from django.contrib.auth.models import User
from datetime import datetime


# Service provider object/model that will be used to push to database
class ServiceProvider(models.Model):
    categoryChoices = [ ('Medical', 'Medical'), ('Beauty', 'Beauty'), ('Fitness', 'Fitness'),]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    category = models.CharField(max_length=20, choices=categoryChoices)
    qualifications = models.TextField(max_length=200, default="Qualifications")
    firstName = models.CharField(max_length=50, default="Provider")
    lastName = models.CharField(max_length=50, default="Name")
    canceledMsgs = models.TextField(default="[]", blank=True)

    def getAndClearCanceledMsgs(self):
        msgs = json.loads(self.canceledMsgs)
        self.canceledMsgs = "[]"
        self.save()
        return msgs
    
# User object/model that will be used to push to database
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    firstName = models.CharField(max_length=50)
    lastName = models.CharField(max_length=50)
    canceledMsgs = models.TextField(default="[]", blank=True)

    def getAndClearCanceledMsgs(self):
        msgs = json.loads(self.canceledMsgs)
        self.canceledMsgs = "[]"
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
    startTime = models.TimeField()
    endTime = models.TimeField()
    isBooked = models.BooleanField(default=False)

    def isPast(self):
        #Check if this appointment slot is in the past
        now = datetime.now()
        
        # If appointment date is before today, it's past
        if self.date < now.date():
            return True
        
        # If appointment date is today, check if end time has passed
        if self.date == now.date() and self.endTime < now.time():
            return True
        
        return False

    def save(self, *args, **kwargs):
        # Check if any overlapping appointment exists for this provider on this date
        overlapping = AppointmentSlot.objects.filter(providerUsername=self.providerUsername,date=self.date).exclude(pk=self.pk)
        
        # Check for time overlap: two time slots overlap if one starts before the other ends
        for existing_slot in overlapping:
            if (self.startTime < existing_slot.endTime and self.endTime > existing_slot.startTime):
                raise Exception(f"Time conflict: You already have an appointment from {existing_slot.startTime.strftime('%H:%M')} to {existing_slot.endTime.strftime('%H:%M')} on this date.")
        
        super().save(*args, **kwargs)

# Booking: booked slots by users
class Booking(models.Model):
    slot = models.OneToOneField(AppointmentSlot, on_delete=models.CASCADE, related_name='booking')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    bookedAt = models.DateTimeField(auto_now_add=True)


