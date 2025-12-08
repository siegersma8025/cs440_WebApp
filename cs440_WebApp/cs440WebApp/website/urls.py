from django.urls import path
from website import views
from . import views

urlpatterns = [
    path('', views.home, name = 'home'),
    path('logout/', views.logoutUser, name = 'logout'),
    path('register/user/', views.registerUser, name = 'registerUser'),
    path('register/provider/', views.registerProvider, name = 'registerProvider'),
    path('dashboard/user/', views.userDashboard, name='userDashboard'),
    path('dashboard/provider/', views.providerDashboard, name='providerDashboard'),
    path('dashboard/admin/', views.adminDashboard, name='adminDashboard'),
    path('book/<int:slot_id>/', views.bookAppointment, name='bookAppointment'),
    path('cancel/<int:slot_id>/', views.cancelAppointment, name='cancelAppointment'),
    path("help/", views.help_page, name="help"),
    path('dashboard/admin/downloadUserReport/', views.downloadUserReport, name='downloadUserReport'),
    path('dashboard/admin/downloadAllUsersReport/', views.downloadAllUsersReport, name='downloadAllUsersReport'),
    path('dashboard/admin/downloadProviderReport/', views.downloadProviderReport, name='downloadProviderReport'),
]