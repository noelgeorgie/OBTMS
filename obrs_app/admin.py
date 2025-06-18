from django.contrib import admin
from django.utils.safestring import mark_safe
from .models import (
    Admin, BusOwner, Bus, Route, Schedule, Passenger,
    Booking, Payment, Cancellation, Employee, Attendance, PassengerTravelDetails, PayeeDetails, EmployeeBusAssignment, JourneyDate, Snack, SnackOrder, BusImage
)

# Register your models here.

admin.site.register(Admin)
admin.site.register(BusOwner)
admin.site.register(Bus)
admin.site.register(Route)
admin.site.register(Schedule)
admin.site.register(Passenger)
admin.site.register(Booking)
admin.site.register(Payment)
admin.site.register(Cancellation)
admin.site.register(Employee)
admin.site.register(Attendance)
admin.site.register(PassengerTravelDetails)
admin.site.register(PayeeDetails)
admin.site.register(EmployeeBusAssignment)
admin.site.register(JourneyDate)
admin.site.register(SnackOrder)

class SnackAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'added_by', 'image_preview')
    readonly_fields = ('image_preview',)

    def image_preview(self, obj):
        if obj.image:
            return mark_safe(f'<img src="{obj.image.url}" width="100" height="100" style="border-radius:10px;" />')
        return "No Image"

    image_preview.short_description = "Image Preview"

admin.site.register(Snack, SnackAdmin)

class BusImageAdmin(admin.ModelAdmin):
    list_display = ('bus', 'image_preview', 'uploaded_at')
    readonly_fields = ('image_preview',)

    def image_preview(self, obj):
        if obj.image:
            return mark_safe(f'<img src="{obj.image.url}" width="100" height="100" style="border-radius:10px;" />')
        return "No Image"

    image_preview.short_description = "Image Preview"

admin.site.register(BusImage, BusImageAdmin)