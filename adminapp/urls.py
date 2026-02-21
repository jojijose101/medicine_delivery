from django.urls import path
from . import views

app_name = "adminapp"

urlpatterns = [
   path("admin-dashboard/", views.admin_dashboard, name="admin_dashboard"),
   path("assign-delivery/<int:order_id>/", views.assign_delivery, name="assign_delivery"),
   path("admin-login/", views.admin_login, name="admin_login"),

]