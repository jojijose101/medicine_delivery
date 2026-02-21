from django.conf import settings
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponseBadRequest
from django.db import transaction
from .models import Medicine, Order, OrderItem
from .models import Profile
from django.contrib import messages
import razorpay
import hashlib
import hmac


from django.db.models import Q

def home(request):
    q = (request.GET.get("q") or "").strip()
    in_stock = request.GET.get("in_stock") == "1"

    medicines = Medicine.objects.filter(is_active=True)

    if q:
        medicines = medicines.filter(
            Q(name__icontains=q)
            # add more fields if you have them:
            # | Q(brand__icontains=q)
            # | Q(description__icontains=q)
        )

    if in_stock:
        medicines = medicines.filter(stock__gt=0)

    medicines = medicines.order_by("name")

    return render(
        request,
        "core/home.html",
        {"medicines": medicines, "q": q, "in_stock": in_stock},
    )

def medicine_detail(request, pk):
    med = get_object_or_404(Medicine, pk=pk, is_active=True)
    return render(request, "core/medicine_detail.html", {"med": med})

from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.views.decorators.http import require_POST
from .models import Medicine


def _get_cart(session):
    return session.get("cart", {})


def _save_cart(session, cart):
    session["cart"] = cart
    session.modified = True


def cart_add(request, pk):
    med = get_object_or_404(Medicine, pk=pk, is_active=True)
    cart = _get_cart(request.session)

    if med.stock <= 0:
        messages.error(request, f"{med.name} is out of stock.")
        return redirect("core:medicine_detail", pk=med.id)

    key = str(med.id)
    current_qty = cart.get(key, {}).get("qty", 0)

    if current_qty + 1 > med.stock:
        messages.warning(request, f"Only {med.stock} items available for {med.name}.")
        return redirect("core:cart")

    cart[key] = {"qty": current_qty + 1}
    _save_cart(request.session, cart)
    messages.success(request, f"Added {med.name} to cart.")
    return redirect("core:cart")


def cart_remove(request, pk):
    cart = _get_cart(request.session)
    key = str(pk)

    if key in cart:
        del cart[key]
        _save_cart(request.session, cart)
        messages.info(request, "Item removed from cart.")

    return redirect("core:cart")


def cart_inc(request, pk):
    med = get_object_or_404(Medicine, pk=pk, is_active=True)
    cart = _get_cart(request.session)

    if med.stock <= 0:
        messages.error(request, f"{med.name} is out of stock.")
        return redirect("core:cart")

    key = str(med.id)
    current_qty = cart.get(key, {}).get("qty", 0)

    if current_qty + 1 > med.stock:
        messages.warning(request, f"Only {med.stock} items available for {med.name}.")
        return redirect("core:cart")

    cart[key] = {"qty": current_qty + 1}
    _save_cart(request.session, cart)
    return redirect("core:cart")


def cart_dec(request, pk):
    med = get_object_or_404(Medicine, pk=pk, is_active=True)
    cart = _get_cart(request.session)
    key = str(med.id)

    if key not in cart:
        return redirect("core:cart")

    current_qty = cart[key].get("qty", 1)
    new_qty = current_qty - 1

    if new_qty <= 0:
        del cart[key]
        messages.info(request, f"{med.name} removed from cart.")
    else:
        cart[key] = {"qty": new_qty}

    _save_cart(request.session, cart)
    return redirect("core:cart")


@require_POST
def cart_update(request, pk):
    med = get_object_or_404(Medicine, pk=pk, is_active=True)
    cart = _get_cart(request.session)
    key = str(med.id)

    try:
        qty = int(request.POST.get("qty", "1"))
    except ValueError:
        qty = 1

    if qty <= 0:
        cart.pop(key, None)
        _save_cart(request.session, cart)
        messages.info(request, f"{med.name} removed from cart.")
        return redirect("core:cart")

    if med.stock <= 0:
        cart.pop(key, None)
        _save_cart(request.session, cart)
        messages.error(request, f"{med.name} is out of stock now.")
        return redirect("core:cart")

    if qty > med.stock:
        qty = med.stock
        messages.warning(request, f"Only {med.stock} items available for {med.name}. Quantity adjusted.")

    cart[key] = {"qty": qty}
    _save_cart(request.session, cart)
    messages.success(request, f"Updated {med.name} quantity.")
    return redirect("core:cart")


@require_POST
def cart_clear(request):
    _save_cart(request.session, {})
    messages.success(request, "Cart cleared.")
    return redirect("core:cart")


def cart_view(request):
    cart = _get_cart(request.session)
    ids = [int(k) for k in cart.keys()] if cart else []
    meds = Medicine.objects.filter(id__in=ids)

    items = []
    total = 0

    # keep original cart order (nice UX)
    meds_map = {m.id: m for m in meds}
    for key in cart.keys():
        mid = int(key)
        m = meds_map.get(mid)
        if not m:
            continue
        qty = cart[str(m.id)]["qty"]
        subtotal = float(m.price) * qty
        total += subtotal
        items.append({"medicine": m, "qty": qty, "subtotal": subtotal})

    return render(request, "core/cart.html", {"items": items, "total": total})

@login_required
def checkout(request):
    cart = _get_cart(request.session)
    if not cart:
        return redirect("core:cart")

    ids = [int(k) for k in cart.keys()]
    meds = Medicine.objects.filter(id__in=ids)

    # build totals
    items = []
    grand_total = 0
    for m in meds:
        qty = cart[str(m.id)]["qty"]
        subtotal = float(m.price) * qty
        grand_total += subtotal
        items.append((m, qty, subtotal))

    profile = Profile.objects.get(user=request.user)
    initial_full_name = request.user.get_full_name() or request.user.username
    initial_phone = profile.phone
    initial_address = profile.address

    if request.method == "POST":
        full_name = request.POST.get("full_name", "").strip()
        phone = request.POST.get("phone", "").strip()
        address = request.POST.get("address", "").strip()
        payment_method = request.POST.get("payment_method", "cod")

        if not full_name or not phone or not address:
            return render(
                request,
                "core/checkout.html",
                {
                    "items": items,
                    "grand_total": grand_total,
                    "error": "All fields are required.",
                },
            )
        if payment_method not in ["cod", "razorpay"]:
            payment_method = "cod"

        order = Order.objects.create(
            user=request.user,
            full_name=full_name,
            phone=phone,
            address=address,
            status="placed",
            payment_method=payment_method,
            is_paid=(payment_method == "cod")
            and False,  # COD is unpaid until delivered
        )

        for m, qty, subtotal in items:
            OrderItem.objects.create(order=order, medicine=m, qty=qty, price=m.price)
            # reduce stock (basic)
            if m.stock >= qty:
                m.stock -= qty
                m.save()

        if payment_method == "razorpay":
            return redirect("core:start_payment", order_id=order.id)

        # clear cart
        _save_cart(request.session, {})

        return render(request, "core/order_success.html", {"order": order})

    return render(
        request,
        "core/checkout.html",
        {
            "items": items,
            "grand_total": grand_total,
            "initial_full_name": initial_full_name,
            "initial_phone": initial_phone,
            "initial_address": initial_address,
        },
    )


@login_required
def my_orders(request):
    orders = Order.objects.filter(user=request.user).order_by("-created_at")
    return render(request, "core/my_orders.html", {"orders": orders})


@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    order_total = sum(float(item.price) * item.qty for item in order.items.all())
    return render(request, "core/order_detail.html", {"order": order, "order_total": order_total})


def signup_view(request):
    if request.user.is_authenticated:
        return redirect("core:home")

    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect("core:signup")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return redirect("core:signup")

        user = User.objects.create_user(
            username=username, email=email, password=password
        )

        login(request, user)
        return redirect("core:home")

    return render(request, "core/signup.html")


def login_view(request):
    if request.user.is_authenticated:
        return redirect("core:home")

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect("core:home")
        else:
            messages.error(request, "Invalid username or password.")

    return render(request, "core/login.html")


def logout_view(request):
    logout(request)
    return redirect("core:home")


@login_required
def profile_view(request):
    profile = Profile.objects.get(user=request.user)

    if request.method == "POST":
        profile.phone = request.POST.get("phone", "").strip()
        profile.address = request.POST.get("address", "").strip()
        profile.save()
        return redirect("core:profile")

    return render(request, "core/profile.html", {"profile": profile})


@login_required
def start_razorpay_payment(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    # Don’t recreate if already paid
    if order.is_paid:
        return redirect("core:order_detail", order_id=order.id)

    client = razorpay.Client(
        auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
    )

    # Razorpay amount is in paise
    # You should compute total from OrderItems; here we assume you can calculate it
    total_rupees = sum([item.qty * float(item.price) for item in order.items.all()])
    amount = int(total_rupees)

    rp_order = client.order.create(
        {
            "amount": amount,
            "currency": "INR",
            "payment_capture": 1,  # auto-capture (recommended)
            "receipt": f"app_order_{order.id}",
            "notes": {"app_order_id": str(order.id)},
        }
    )  # create Order on server :contentReference[oaicite:3]{index=3}

    order.razorpay_order_id = rp_order["id"]
    order.payment_method = "razorpay"
    order.save()

    return render(
        request,
        "core/razorpay_checkout.html",
        {
            "order": order,
            "razorpay_key_id": settings.RAZORPAY_KEY_ID,
            "amount": amount,
            "customer_name": order.full_name,
            "customer_phone": order.phone,
        },
    )


@login_required
@csrf_exempt  # If you use CSRF token in form you can remove this; keep for simplicity during testing
def razorpay_callback(request):
    if request.method != "POST":
        return HttpResponseBadRequest("Invalid request")

    razorpay_payment_id = request.POST.get("razorpay_payment_id")
    razorpay_order_id = request.POST.get("razorpay_order_id")
    razorpay_signature = request.POST.get("razorpay_signature")

    # Find your order by razorpay_order_id
    order = get_object_or_404(
        Order, razorpay_order_id=razorpay_order_id, user=request.user
    )

    # Verify signature
    generated_signature = hmac.new(
        settings.RAZORPAY_KEY_SECRET.encode(),
        f"{razorpay_order_id}|{razorpay_payment_id}".encode(),
        hashlib.sha256,
    ).hexdigest()

    if generated_signature != razorpay_signature:
        messages.error(request, "Payment verification failed.")
        return redirect("core:order_detail", order_id=order.id)

    # Mark paid
    order.razorpay_payment_id = razorpay_payment_id
    order.razorpay_signature = razorpay_signature
    order.is_paid = True
    order.save()

    messages.success(request, "Payment successful!")
    return redirect("core:order_detail", order_id=order.id)

@login_required
def payment_failed(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, "core/payment_failed.html", {"order": order})


@login_required
def cancel_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    if request.method != "POST":
        return redirect("core:order_detail", order_id=order.id)

    if order.status in ["shipped", "delivered", "cancelled"]:
        messages.error(request, "Order cannot be cancelled at this stage.")
        return redirect("core:order_detail", order_id=order.id)

    with transaction.atomic():
        # Restore stock
        for item in order.items.all():
            item.medicine.stock += item.qty
            item.medicine.save()

        order.status = "cancelled"
        order.save()

    messages.success(request, "Order cancelled successfully.")
    return redirect("core:order_detail", order_id=order.id)

