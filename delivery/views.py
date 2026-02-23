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
        return redirect("delivery:delivery_order_detail", order_id=order.id)

    if order.status == "cancelled":
        messages.error(request, "Cancelled orders cannot be updated.")
        return redirect("delivery:delivery_order_detail", order_id=order.id)

    if order.status == "delivered":
        messages.info(request, "This order is already delivered.")
        return redirect("delivery:delivery_order_detail", order_id=order.id)

    # Prevent delivery updates if Razorpay payment not completed
    if order.payment_method == "razorpay" and not order.is_paid:
        messages.error(request, "Cannot update status until payment is completed.")
        return redirect("delivery:delivery_order_detail", order_id=order.id)

    new_status = request.POST.get("status")

    # Strict next-step progression
    next_status_map = {
        "placed": "packed",
        "packed": "shipped",
        "shipped": "delivered",
    }

    expected_next = next_status_map.get(order.status)

    if not expected_next:
        messages.error(request, "Invalid current order status.")
        return redirect("delivery:delivery_order_detail", order_id=order.id)

    if new_status != expected_next:
        messages.error(
            request,
            f"Invalid update. From '{order.status}' you can only move to '{expected_next}'."
        )
        return redirect("delivery:delivery_order_detail", order_id=order.id)

    order.status = new_status

    # Optional: mark COD paid automatically when delivered
    if order.status == "delivered" and order.payment_method == "cod":
        order.is_paid = True

    order.save()

    messages.success(request, f"Order status updated to {order.status}.")
    return redirect("delivery:delivery_order_detail", order_id=order.id)

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
