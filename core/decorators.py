from django.shortcuts import redirect
from functools import wraps
from django.contrib import messages

def role_required(role):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if request.user.is_authenticated and request.user.role == role:
                return view_func(request, *args, **kwargs)
            messages.error(request, "You're not authorized to view this page.")
            return redirect('login')  # or 'customer_dashboard' for logged-in users
        return _wrapped_view
    return decorator

# Predefined decorators
customer_required = role_required('customer')
provider_required = role_required('provider')
admin_required = role_required('admin')
