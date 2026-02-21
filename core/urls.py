from django.urls import path
from . import views

app_name = "core"

urlpatterns = [
    path("", views.home, name="home"),
    path("medicine/<int:pk>/", views.medicine_detail, name="medicine_detail"),
    # cart
    path("cart/", views.cart_view, name="cart"),
    path("cart/add/<int:pk>/", views.cart_add, name="cart_add"),
    path("cart/remove/<int:pk>/", views.cart_remove, name="cart_remove"),
    path("cart/inc/<int:pk>/", views.cart_inc, name="cart_inc"),
    path("cart/dec/<int:pk>/", views.cart_dec, name="cart_dec"),
    path("cart/update/<int:pk>/", views.cart_update, name="cart_update"),
    path("cart/clear/", views.cart_clear, name="cart_clear"),
    # checkout
    path("checkout/", views.checkout, name="checkout"),
    # user orders tracking
    path("my-orders/", views.my_orders, name="my_orders"),
    path("my-orders/<int:order_id>/", views.order_detail, name="order_detail"),
    # auth
    path("login/", views.login_view, name="login"),
    path("signup/", views.signup_view, name="signup"),
    path("logout/", views.logout_view, name="logout"),
    path("profile/", views.profile_view, name="profile"),
    path("pay/<int:order_id>/", views.start_razorpay_payment, name="start_payment"),
    path("razorpay/callback/", views.razorpay_callback, name="razorpay_callback"),
    path("payment/failed/<int:order_id>/", views.payment_failed, name="payment_failed"),
    path("order/cancel/<int:order_id>/", views.cancel_order, name="cancel_order"),
]
