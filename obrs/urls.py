"""
URL configuration for obrs project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from obrs_app import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    #Administrator URL
    path('admin/', admin.site.urls),
    
    #Logout Page
    path('logout/', views.logout_view, name='logout'),
    
    #Index Pages
    path('', views.index,  name='index'),
    path('owner-register/', views.owner_register, name='owner_register'),
    path('employee-register/', views.employee_register, name='employee_register'),
    path('passenger_register/', views.passenger_register, name='passenger_register'),
    path('forgot_password/', views.forgot_password, name='forgot_password'),
    
    #Dashboard Pages
    path('passenger-dashboard/', views.passenger_dashboard, name='passenger_dashboard'),
    path('busowner-dashboard/', views.busowner_dashboard, name='busowner_dashboard'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('driver-dashboard/', views.driver_dashboard, name='driver_dashboard'),
    path('staff-dashboard/', views.staff_dashboard, name='staff_dashboard'),
    
    #Admin Pages
    path('admin-add-owner/', views.admin_add_owner, name='admin_add_owner'),
    path('admin-view-bus-owners/', views.admin_view_bus_owners, name='admin_view_bus_owners'),
    path('admin-view-buses/', views.admin_view_buses, name='admin_view_buses'),
    path('admin-view-route/', views.admin_view_route, name='admin_view_route'),
    path('admin-view-schedules/', views.admin_view_schedules, name='admin_view_schedules'),
    path('admin-view-bookings/', views.admin_view_bookings, name='admin_view_bookings'),
    path('admin-view-payments/', views.admin_view_payments, name='admin_view_payments'),
    path('admin-view-cancellations/', views.admin_view_cancellations, name='admin_view_cancellations'),
    path('admin-view-passenger/', views.admin_view_passenger, name='admin_view_passenger'),
    path('admin-delete-passenger/delete/<int:id>/', views.admin_delete_passenger, name='admin_delete_passenger'),
    path('admin-view-employees/', views.admin_view_employees, name='admin_view_employees'),
    path('admin-manage-bus-owner/', views.admin_manage_bus_owner, name='admin_manage_bus_owner'),
    path('admin-edit-bus-owner/<int:id>/', views.admin_edit_bus_owner, name='admin_edit_bus_owner'), 
    path('admin-delete-bus-owner/<int:id>/', views.admin_delete_bus_owner, name='admin_delete_bus_owner'),
    path('admin-profile/', views.admin_profile, name='admin_profile'),
    path('admin-view-assigned-employees/', views.admin_view_assigned_employees, name='admin_view_assigned_employees'),
    path('admin-travel-details/', views.admin_travel_details_view, name='admin_travel_details'),
    
    #Bus Owner Pages
    path('owner-add-bus/', views.owner_add_bus, name='owner_add_bus'),
    path('owner-manage-bus/', views.owner_manage_bus, name='owner_manage_bus'),
    path('owner-edit-bus/<int:bus_id>/', views.owner_edit_bus, name='owner_edit_bus'),    
    path('owner-delete-bus/<int:bus_id>/', views.owner_manage_bus, name='owner_delete_bus'),   
    path('owner-view-passenger/', views.owner_view_passenger, name='owner_view_passenger'),
    path('owner-view-bookings/', views.owner_view_bookings, name='owner_view_bookings'),
    path('owner-view-payments/', views.owner_view_payments, name='owner_view_payments'),
    path('owner-view-cancellations/', views.owner_view_cancellations, name='owner_view_cancellations'),
    path('owner-view-buses/', views.owner_view_buses, name='owner_view_buses'),
    path('owner-view-route/', views.owner_view_route, name='owner_view_route'),
    path('owner-view-schedules/', views.owner_view_schedules, name='owner_view_schedules'),
    path('owner-view-employees/', views.owner_view_employees, name='owner_view_employees'),
    path('owner-add-employee/', views.owner_add_employee, name='owner_add_employee'),
    path('owner-manage-employee/', views.owner_manage_employee, name='owner_manage_employee'),
    path('owner-edit-employees/<int:employee_id>/', views.owner_edit_employees, name='owner_edit_employees'),
    path('owner-delete-employee/<int:employee_id>/', views.owner_manage_employee, name='owner_delete_employee'),  
    path('owner-add-route/', views.owner_add_route, name='owner_add_route'),
    path('owner-add-schdeule/', views.owner_add_schedule, name='owner_add_schedule'),
    path('owner-manage-schedule/', views.owner_manage_schedule, name='owner_manage_schedule'),
    path('owner-delete-schedule/<int:schedule_id>/', views.owner_delete_schedule, name='owner_delete_schedule'),
    path('owner-manage-schedule/<int:schedule_id>/', views.owner_edit_schedule, name='owner_edit_schedule'),
    path('owner-manage-route/', views.owner_manage_route, name='owner_manage_route'),
    path('owner-edit-route/<int:route_id>/', views.owner_edit_route, name='owner_edit_route'),
    path('owner-delete-route/<int:route_id>/', views.owner_manage_route, name='owner_delete_route'),
    path('owner-assign-employee/', views.owner_assign_employee, name='owner_assign_employee'),
    path('get-schedules/<int:bus_id>/', views.get_schedules, name='get_schedules'),
    path('owner-assign-employee/<int:employee_id>/', views.owner_assign_employee, name='owner_assign_employee_with_id'),
    path('owner-assign-employee-to-bus/<int:employee_id>/', views.owner_assign_employee_to_bus, name='owner_assign_employee_to_bus'),
    path('process-employee-bus-assignment/<int:employee_id>/', views.process_employee_bus_assignment, name='process_employee_bus_assignment'),
    path('view-assigned-employees/', views.view_assigned_employees, name='view_assigned_employees'),
    path('owner/delete-assigned-employee/<int:assignment_id>/', views.delete_assigned_employee, name='delete_assigned_employee'),
    path('owner-view-attendance/', views.owner_view_attendance, name='owner_view_attendance'),
    path('toggle-attendance/<int:attendance_id>/', views.toggle_attendance_status, name='toggle_attendance_status'),
    path('busowner-view-journey-dates/', views.owner_view_journey_dates, name='owner_view_journey_dates'),
    path('bus-owner/travel-details/', views.bus_owner_travel_details_view, name='bus_owner_travel_details'),
    path('busowner-profile/', views.busowner_profile, name='busowner_profile'),
    path('mark-attendance/', views.owner_mark_attendance, name='owner_mark_attendance'),
    
    #Passenger Pages
    path('passenger-about/', views.passenger_about, name='passenger_about'),
    path('logout-and-redirect/', views.logout_and_redirect, name='logout_and_redirect'),
    path('passenger-blog/', views.passenger_blog, name='passenger_blog'),
    path('passenger-contact/', views.passenger_contact, name='passenger_contact'),
    path('passenger-offers/', views.passenger_offers, name='passenger_offers'),
    
    #Passenger Booking Associated Pages
    path('passenger-view-bus/', views.passenger_view_bus, name='passenger_view_bus'),
    path('passenger-view-route/', views.passenger_view_route, name='passenger_view_route'),
    path('passenger-view-cancel/', views.passenger_view_cancel, name='passenger_view_cancel'),
    path('passenger-view-booking/', views.passenger_view_booking, name='passenger_view_booking'),
    path('passenger-view-schedules/', views.passenger_view_schedules, name='passenger_view_schedules'),
    path('search-buses/', views.search_buses, name='search_buses'),
    path('select-seats/<int:schedule_id>/<int:bus_id>/', views.select_seats, name='select_seats'),
    path('payment/', views.payment, name='payment'),
    path('details/', views.details, name='details'),
    path('process-booking-payment/', views.process_booking_payment, name='process_booking_payment'),
    path('traveller-details/', views.traveller_details, name='traveller_details'),
    path('payee-details/', views.payee_details, name='payee_details'),
    path('booking-success/', views.booking_success, name='booking_success'), 
    path('cancel-booking/<int:booking_id>/', views.cancel_booking, name='cancel_booking'),
    path('booking-details/<int:booking_id>/', views.booking_details_view, name='passenger_booking_details'),
    path('payment_success/', views.payment_success, name='payment_success'),
    path('download-booking/<int:booking_id>/', views.generate_booking_pdf, name='download_booking_pdf'), 
    path('booking-confirmation/<int:booking_id>/', views.booking_confirmation, name='booking_confirmation'),
    path('passenger-profile/', views.passenger_profile, name='passenger_profile'),
    
    #Staff Pages
    path('staff-view-passenger/', views.staff_view_passenger, name='staff_view_passenger'),
    path('staff-view-bookings/', views.staff_view_bookings, name='staff_view_bookings'),
    path('staff-view-payments/', views.staff_view_payments, name='staff_view_payments'),
    path('staff-view-cancellations/', views.staff_view_cancellations, name='staff_view_cancellations'),   
    path('staff-assigned-buses/', views.staff_assigned_buses_view, name='staff_assigned_buses'),
    path('staff-assigned-routes/', views.staff_assigned_routes_view, name='staff_assigned_routes'),
    path('staff-assigned-schedules/', views.staff_assigned_schedules_view, name='staff_assigned_schedules'),
    path('staff-journey-form/', views.staff_journey_form, name='staff_journey_form'),
    path('staff-mark-attendance/<int:employee_id>/', views.staff_mark_attendance, name='staff_mark_attendance'),
    path('mark-trip/<int:schedule_id>/', views.mark_trip_status, name='mark_trip_status'),
    path('staff-journey-dates/', views.staff_view_journey_dates, name='staff_view_journey_dates'),
    path('staff/attendance/', views.staff_view_attendance, name='staff_view_attendance'),
    path('staff-/travel-details/', views.staff_travel_details_view, name='staff_travel_details'),
    path('staff/profile/', views.staff_profile, name='staff_profile'),
    
    #Driver Pages
    path('driver-view-passenger/', views.driver_view_passenger, name='driver_view_passenger'),
    path('driver-view-bookings/', views.driver_view_bookings, name='driver_view_bookings'),
    path('driver-view-payments/', views.driver_view_payments, name='driver_view_payments'),
    path('driver-view-cancellations/', views.driver_view_cancellations, name='driver_view_cancellations'), 
    path('driver-assigned-buses/', views.driver_assigned_buses_view, name='driver_assigned_buses'),
    path('driver-assigned-routes/', views.driver_assigned_routes_view, name='driver_assigned_routes'),
    path('driver-assigned-schedules/', views.driver_assigned_schedules_view, name='driver_assigned_schedules'),
    path('driver-mark-attendance/<int:employee_id>/', views.driver_mark_attendance, name='driver_mark_attendance'),
    path('driver-view-attendance/', views.driver_view_attendance, name='driver_view_attendance'),
    path('driver-profile/', views.driver_profile, name='driver_profile'),
    
    #Snack Pages
    path('order-snacks/<int:booking_id>/', views.order_snacks, name='order_snacks'),
    path('add-to-cart/<int:snack_id>/<int:booking_id>/', views.add_to_cart, name='add_to_cart'),
    path('checkout/', views.checkout_view, name='checkout_view'),
    path('add_snack/', views.add_snack, name='add_snack'),  
    path('orders/', views.view_orders, name='snack_list'),
    path('delete_snack/<int:snack_id>/', views.delete_snack, name='delete_snack'),
    path('edit_snack/<int:snack_id>/', views.edit_snack, name='edit_snack'),
    path('snack-orders/', views.view_snack_orders, name='view_snack_orders'),
    path('bus_owner/snacks/', views.bus_owner_snacks, name='bus_owner_snacks'),
    path('bus_owner/snack_orders/', views.bus_owner_snack_orders, name='bus_owner_snack_orders'),
    path('view-snacks/<int:booking_id>/', views.passenger_view_snack_details, name='view_snack_details'),
    path('cancel-snack/<int:order_id>/', views.cancel_snack_order, name='cancel_snack_order'),

    #Update booking status
    path('update-completed-bookings/', views.update_completed_bookings, name='update_completed_bookings'),
    path('update-snack-orders/', views.update_completed_orders, name='update_completed_orders'),
    
    #Bus Image Upload
    path('bus-images/<int:schedule_id>/', views.view_bus_images, name='view_bus_images'),
    path('add_bus_image/', views.add_bus_image, name='add_bus_image'),



]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    