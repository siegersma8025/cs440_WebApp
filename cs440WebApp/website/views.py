from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages

# Each view is essentially a function that takes in a request and returns a response
# The response is usually a rendered HTML template
# The request can be a GET or POST request
def home(request):
    # If logging in (posting)
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Authenticate the user
        user = authenticate(request, username=username, password=password)

        # If authenticated 
        if user is not None:
            login(request, user)
            messages.success(request, "Logged in successfully")
            return redirect('home')
        else:
            messages.error(request, "Error logging in. Please try again.")
            return redirect('home')
        
    else:
        return render(request, 'home.html', {})

# def loginUser(request):
#     pass

def logoutUser(request):
    logout(request)
    messages.success(request, "Logged out successfully")
    return redirect('home')