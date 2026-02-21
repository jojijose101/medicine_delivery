from django.shortcuts import redirect, render
from django.shortcuts import get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login
from .utils import delivery_required
from core.models import Order

@delivery_required
def delivery_dashboard(request):
    orders = Order.objects.filter(assigned_delivery=request.user).order_by("-created_at")
    return render(request, "delivery/delivery_dashboard.html", {"orders": orders})


@delivery_required
def delivery_order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, assigned_delivery=request.user)
    return render(request, "delivery/delivery_order_detail.html", {"order": order})


@delivery_required
def delivery_update_status(request, order_id):
    order = get_object_or_404(Order, id=order_id, assigned_delivery=request.user)

    if request.method != "POST":
        return redirect("core:delivery_order_detail", order_id=order.id)

    # Block updates on cancelled orders
    if order.status == "cancelled":
        messages.error(request, "Cancelled orders cannot be updated.")
        return redirect("core:delivery_order_detail", order_id=order.id)

    # Block updates if Razorpay order not paid
    if order.payment_method == "razorpay" and not order.is_paid:
        messages.error(request, "Cannot update status until payment is completed.")
        return redirect("core:delivery_order_detail", order_id=order.id)

    new_status = request.POST.get("status")

    allowed = ["packed", "shipped", "delivered"]
    if new_status not in allowed:
        messages.error(request, "Invalid status.")
        return redirect("core:delivery_order_detail", order_id=order.id)

    # Optional: prevent going backwards
    status_order = {"placed": 0, "packed": 1, "shipped": 2, "delivered": 3, "cancelled": -1}
    if status_order.get(new_status, -99) < status_order.get(order.status, -99):
        messages.error(request, "You cannot move order status backwards.")
        return redirect("core:delivery_order_detail", order_id=order.id)

    order.status = new_status
    order.save()

    messages.success(request, f"Order status updated to {new_status}.")
    return redirect("core:delivery_order_detail", order_id=order.id)

def delivery_login(request):
    if request.user.is_authenticated:
        return redirect("delivery:delivery_dashboard")

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None and user.profile.role == "delivery":
            login(request, user)
            return redirect("delivery:delivery_dashboard")
        else:
            messages.error(request, "Invalid credentials or not a delivery account.")

    return render(request, "delivery/delivery_login.html")
