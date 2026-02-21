from django.shortcuts import redirect
from django.contrib import messages

def delivery_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("delivery:delivery_login")
        if not hasattr(request.user, "profile") or request.user.profile.role != "delivery":
            messages.error(request, "Delivery access only.")
            return redirect("core:home")
        return view_func(request, *args, **kwargs)
    return wrapper
