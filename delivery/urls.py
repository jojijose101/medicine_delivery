from django.urls import path
from . import views

app_name = "delivery"

urlpatterns = [
    path("", views.delivery_dashboard, name="delivery_dashboard"),
    path("order/<int:order_id>/", views.delivery_order_detail, name="delivery_order_detail"),
    path("order/<int:order_id>/status/", views.delivery_update_status, name="delivery_update_status"),
    path("login/", views.delivery_login, name="delivery_login"),
]