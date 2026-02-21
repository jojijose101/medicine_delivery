from django.shortcuts import redirect

def admin_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("adminapp:admin_login")
        if request.user.profile.role != "admin":
            return redirect("core:home")
        return view_func(request, *args, **kwargs)
    return wrapper
