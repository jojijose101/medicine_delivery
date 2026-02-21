from django.contrib import messages

from .utils import admin_required
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from core.models import Order, Profile

@admin_required
def admin_dashboard(request):
    orders = Order.objects.all().order_by("-created_at")
    delivery_users = User.objects.filter(profile__role="delivery")

    total = orders.count()
    delivered = orders.filter(status="delivered").count()
    pending = orders.exclude(status="delivered").count()

    return render(request, "admin/admin_dashboard.html", {
        "orders": orders,
        "delivery_users": delivery_users,
        "total": total,
        "delivered": delivered,
        "pending": pending,
    })


@admin_required
def assign_delivery(request, order_id):
    order = Order.objects.get(id=order_id)

    if request.method == "POST":
        delivery_id = request.POST.get("delivery_id")
        delivery_user = User.objects.get(id=delivery_id)
        order.assigned_delivery = delivery_user
        order.save()
        return redirect("adminapp:admin_dashboard")

    return redirect("adminapp:admin_dashboard")


def admin_login(request):
    if request.user.is_authenticated:
        return redirect("adminapp:admin_dashboard")

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None and user.profile.role == "admin":
            login(request, user)
            return redirect("adminapp:admin_dashboard")
        else:
            messages.error(request, "Invalid credentials or not an admin account.")
            return render(request, "admin/admin_login.html")

    return render(request, "admin/admin_login.html")