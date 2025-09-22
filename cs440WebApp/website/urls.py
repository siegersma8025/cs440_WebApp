from django.urls import path
from website import views

urlpatterns = [
    path('', views.home, name = 'home'),
    #path('login/', views.loginUser, name = 'login'),
    path('logout/', views.logoutUser, name = 'logout'),
]