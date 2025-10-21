from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse
import logging

logger = logging.getLogger(__name__)

class SecurityMiddleware:
    """Custom security middleware to prevent unauthorized access"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        # Process the request first to get user information
        response = self.get_response(request)
        
        # Add additional security headers not covered in settings.py
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        return response
    
    def process_view(self, request, view_func, view_args, view_kwargs):
        """Process view to check authentication before view execution"""
        # Only check if user attribute is available (after AuthenticationMiddleware)
        if hasattr(request, 'user'):
            # Log suspicious access attempts
            if not request.user.is_authenticated and request.path.startswith('/dashboard/'):
                logger.warning(f"Unauthorized access attempt to {request.path} from IP: {self.get_client_ip(request)}")
                messages.error(request, "Please log in to access this page.")
                return redirect('home')
                
            # Prevent direct access to booking without proper referrer
            if request.path.startswith('/book/') and not request.user.is_authenticated:
                logger.warning(f"Unauthorized booking attempt from IP: {self.get_client_ip(request)}")
                messages.error(request, "Please log in to book appointments.")
                return redirect('home')
        
        return None
    
    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip