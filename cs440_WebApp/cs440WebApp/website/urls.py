from django.urls import path
from website import views

urlpatterns = [
    path('', views.home, name = 'home'),
    path('logout/', views.logoutUser, name = 'logout'),
    path('register/user/', views.registerUser, name = 'registerUser'),
    path('register/provider/', views.registerProvider, name = 'registerProvider'),
    path('dashboard/user/', views.userDashboard, name='userDashboard'),
    path('dashboard/provider/', views.providerDashboard, name='providerDashboard'),
    path('dashboard/admin/', views.adminDashboard, name='adminDashboard'),
    path('book/<int:slot_id>/', views.bookAppointment, name='bookAppointment'),
    path('cancel/<int:booking_id>/', views.cancelAppointment, name='cancelAppointment'),
]