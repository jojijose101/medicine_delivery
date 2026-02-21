from django.contrib import admin
from .models import Medicine, Order, OrderItem
from .models import Profile
 

@admin.register(Medicine)
class MedicineAdmin(admin.ModelAdmin):
    list_display = ("name", "brand", "price", "stock", "is_active")
    search_fields = ("name", "brand")
    list_filter = ("is_active",)

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "status", "assigned_delivery", "created_at")
    list_filter = ("status",)
    inlines = [OrderItemInline]

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "phone")
    list_filter = ("role",)
    search_fields = ("user__username", "phone")

