import datetime
from itertools import zip_longest
from multiprocessing import context
import traceback
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
from django.core.mail import send_mail
from obrs_app.models import BusOwner, Passenger, Admin, Employee, Bus, Route, Schedule, Booking, Cancellation, Payment, Attendance, PassengerTravelDetails, PayeeDetails, EmployeeBusAssignment, JourneyDate, Snack, SnackOrder, BusImage
from django.db.models import ObjectDoesNotExist
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.db import IntegrityError
from django.db.models import Q
from decimal import Decimal
from django.utils import timezone
from django.http import JsonResponse
from django.db import transaction 
from django.utils.timezone import now
from datetime import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.timezone import now
from collections import defaultdict
import json
from django.shortcuts import render
from datetime import datetime


# Create your views here.

# Line 25 to 41 is the code for the Index pages
# Line 42 to 54 is the code for the Logout Function
# Line 56 to 84 is the code to send a dummy password reset link for passenger login 
# Line 86 to 162 is the code for the Login Function to different dashboards
# Line 165 to 224 is the code for Admin Dashboard
# Line 94 to 453 is the code for the Admin page views

  
  
                                                                                                             

#-----------------------------------------------Index Page Views---------------------------------------------

def index(request):
    return render(request, 'index.html')

def owner_register(request):
    return render(request, 'busowner/owner_register.html')

def employee_register(request):
    return render(request, 'employee/employee_register.html')

def passenger_register(request):
    return render(request, 'passenger/passenger_register.html')

def forgot_password(request):
    return render(request, 'forgot_password.html')

#------------------------------------------this is the Logout function---------------------------------------

def logout_view(request):
    # Clear the session
    request.session.flush()  # This clears all session data

    # Optionally, display a message for the user
    messages.success(request, 'You have been logged out.')

    # Redirect the user back to the login page
    return redirect('index')  # Redirect to the index page (login page)

#------------------------------------------------------------------------------------------------------------

#--------------------this will send an email to the user with a link to reset the password-------------------

def forgot_password(request):
    if request.method == 'POST':
        # Get the email address from the form input
        email = request.POST.get('email')

        # Check if email is provided
        if email:
            # Send the password reset email to the entered email
            send_mail(
                subject='Password Reset Request',
                message='Click the link below to reset your password:\nhttp://example.com/reset-password',
                from_email='your-email@gmail.com',  # The sender email (can be your Gmail)
                recipient_list=[email],  # Send the email to the entered email address
                fail_silently=False,
            )

            # Add a success message
            messages.success(request, 'Password reset link has been sent to your email.')

            # Redirect to the index page or login page
            return redirect('index')  # Replace 'index' with the actual URL name for your homepage
        else:
            messages.error(request, 'Please enter a valid email address.')

    return render(request, 'forgot_password.html')

#------------------------------------------------------------------------------------------------------------

#---------------------------------------this is the login function-------------------------------------------

def index(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user_type = request.POST.get('user_type')

        print(f"Email: {email}, Password: {password}, User Type: {user_type}")

        # Handle Passenger Login
        if user_type == 'pass':
            try:
                passenger = Passenger.objects.get(email=email)
                if passenger.password == password:
                    request.session['passenger_id'] = passenger.passenger_id
                    request.session.modified = True  # Force session save
                    return redirect('passenger_dashboard')
                else:
                    messages.error(request, 'Invalid email or password.')
                    return redirect('index')
            except Passenger.DoesNotExist:
                messages.error(request, 'Invalid email or password.')
                return redirect('index')

        # Handle Bus Owner Login
        elif user_type == 'busowner':
            try:
                bus_owner = BusOwner.objects.get(email=email)
                if bus_owner.password == password:
                    request.session['owner_id'] = bus_owner.owner_id
                    return redirect('busowner_dashboard')
                else:
                    messages.error(request, 'Invalid email or password.')
                    return redirect('index')
            except BusOwner.DoesNotExist:
                messages.error(request, 'Invalid email or password.')
                return redirect('index')

        # Handle Admin Login (Separate block for admin)
        elif user_type == 'admin':
            try:
                admin = Admin.objects.get(email=email)
                if admin.password == password:
                    request.session['admin_id'] = admin.admin_id
                    return redirect('admin_dashboard')
                else:
                    messages.error(request, 'Invalid email or password.')
                    return redirect('index')
            except Admin.DoesNotExist:
                messages.error(request, 'Invalid email or password.')
                return redirect('index')

        # Handle Employee Login (Driver or Staff, Separate block for employees)
        elif user_type in ['driver', 'staff']:
            try:
                employee = Employee.objects.get(email=email)
                if employee.password == password:
                    if employee.role == 'Driver':
                        request.session['driver_id'] = employee.employee_id
                        return redirect('driver_dashboard')
                    elif employee.role == 'Staff':
                        request.session['staff_id'] = employee.employee_id
                        return redirect('staff_dashboard')
                else:
                    messages.error(request, 'Invalid email or password.')
                    return redirect('index')
            except Employee.DoesNotExist:
                messages.error(request, 'Invalid email or password.')
                return redirect('index')

        else:
            messages.error(request, 'Invalid user type.')
            return redirect('index')

    return render(request, 'index.html')  # Render the login page for GET requests

#------------------------------------------------------------------------------------------------------------

#-----------------------------------View for login redirect to Admin dashboard function----------------------

def admin_dashboard(request):
    # Check if the user is logged in by verifying the session
    admin_id = request.session.get('admin_id')

    if not admin_id:
        messages.error(request, 'You need to log in first.')
        return redirect('index')

    try:
        admin = Admin.objects.get(admin_id=admin_id)
        admin_name = admin.name
    except Admin.DoesNotExist:
        messages.error(request, 'Invalid session. Please log in again.')
        return redirect('index')

    # Fetch counts from the database
    busowner_count = BusOwner.objects.count()
    bus_count = Bus.objects.count()
    route_count = Route.objects.count()
    schedule_count = Schedule.objects.count()
    driver_count = Employee.objects.filter(role='Driver').count()
    staff_count = Employee.objects.filter(role='Staff').count()
    passenger_count = Passenger.objects.count()

    # Search functionality
    search_results = []
    query = request.POST.get('keywords', '')

    if query and admin_id:
        # Filter Bus Owners added by this Admin
        bus_owners = BusOwner.objects.filter(
            Q(name__icontains=query) | Q(email__icontains=query) | Q(phone_number__icontains=query),
            admin__admin_id=admin_id
        )

        # Filter Employees added by those Bus Owners
        employees = Employee.objects.filter(
            Q(name__icontains=query) | Q(email__icontains=query) | Q(phone_number__icontains=query)
        )

        # You can include passengers normally (optional)
        passengers = Passenger.objects.filter(
            Q(name__icontains=query) | Q(email__icontains=query) | Q(phone_number__icontains=query)
        )

        # Combine results
        search_results = {
            'bus_owners': bus_owners,
            'passengers': passengers,
            'employees': employees,
        }

    context = {
        'admin_name': admin_name,  
        'admin': admin,
        'busowner_count': busowner_count,
        'bus_count': bus_count,
        'route_count': route_count,
        'schedule_count': schedule_count,
        'driver_count': driver_count,
        'staff_count': staff_count,
        'passenger_count': passenger_count,
        'search_results': search_results,
        'query': query,
    }

    return render(request, 'admin/admin_dashboard.html', context)

#-----------------------------------------------Admin Page Views---------------------------------------------

def admin_add_owner(request):
    # Check if the user is logged in as admin
    admin_id = request.session.get('admin_id')  # Fetch admin_id from session
    if not admin_id:
        messages.error(request, 'You need to log in as an admin to access this page.')
        return redirect('index')  # Redirect to login page or dashboard

    try:
        # Get the logged-in admin object
        admin = Admin.objects.get(admin_id=admin_id)
    except Admin.DoesNotExist:
        messages.error(request, 'Invalid admin session. Please log in again.')
        return redirect('index')  # Redirect to login page or dashboard

    if request.method == 'POST':
        # Get data from the form
        name = request.POST.get('name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        phone_number = request.POST.get('phone_number')

        # Validate the form fields (basic validation)
        if not name or not email or not password or not phone_number:
            messages.error(request, 'All fields are required.')
            return redirect('admin_add_owner')

        # Check if an owner with the same email already exists
        if BusOwner.objects.filter(email=email).exists():
            messages.error(request, 'A bus owner with this email already exists.')
            return redirect('admin_add_owner')

        try:
            # Save the new owner to the database
            BusOwner.objects.create(
                name=name,
                email=email,
                password=password,
                phone_number=phone_number,
                admin=admin  # Use the logged-in admin
            )
            messages.success(request, 'Bus owner added successfully.')
            return redirect('admin_add_owner')

        except IntegrityError as e:
            # If a duplicate phone number exists, handle the error
            if 'duplicate entry' in str(e).lower():
                messages.error(request, 'This phone number is already associated with another bus owner.')
            else:
                messages.error(request, 'An error occurred while adding the bus owner. Please try again.')
            return redirect('admin_add_owner')

    # Render the add_owner page for GET requests
    return render(request, 'admin/add_owner.html')

#---------------------------------------------------------

def admin_view_bus_owners(request):
    # Fetch the admin_id from the session
    admin_id = request.session.get('admin_id')

    if not admin_id:
        messages.error(request, 'You need to log in as an admin to view this page.')
        return redirect('index')  # Redirect to login page or dashboard

    # Get the logged-in admin object
    try:
        admin = Admin.objects.get(admin_id=admin_id)
    except Admin.DoesNotExist:
        messages.error(request, 'Invalid admin session. Please log in again.')
        return redirect('index')  # Redirect to login page or dashboard

    # Get bus owners associated with the logged-in admin
    bus_owners = BusOwner.objects.filter(admin=admin).order_by('owner_id')

    # Pass the bus owners to the template
    return render(request, 'admin/view_busowner.html', {'bus_owners': bus_owners})

#---------------------------------------------------------

def admin_view_bookings(request):
    # Check if admin is logged in
    admin_id = request.session.get('admin_id')
    if not admin_id:
        return render(request, 'error.html', {'message': 'You must be logged in as an admin.'})

    # Fetch all bus owners managed by this admin
    bus_owners = BusOwner.objects.filter(admin_id=admin_id)

    # Fetch all buses owned by these bus owners
    buses = Bus.objects.filter(owner__in=bus_owners)

    # Fetch all schedules associated with these buses
    schedules = Schedule.objects.filter(bus__in=buses)

    # Fetch all bookings related to these schedules
    bookings = Booking.objects.filter(schedule__in=schedules).order_by('booking_id')

    # Render the bookings to the template
    return render(request, 'admin/view_bookings.html', {'bookings': bookings})


#---------------------------------------------------------

def admin_view_assigned_employees(request):
    # Check if admin is logged in
    admin_id = request.session.get('admin_id')

    if not admin_id:
        return render(request, 'error.html', {'message': 'You must be logged in as an admin.'})

    # Get all bus owners under this admin
    bus_owners = BusOwner.objects.filter(admin_id=admin_id)

    # Get all buses owned by these bus owners
    buses = Bus.objects.filter(owner__in=bus_owners)

    # Fetch all employee assignments related to those buses, including bus and schedule details
    assignments = EmployeeBusAssignment.objects.filter(bus__in=buses).select_related('employee', 'bus', 'bus__owner', 'schedule').order_by('id')

    return render(request, 'admin/view_assign_employee.html', {'assignments': assignments})


#---------------------------------------------------------

def admin_travel_details_view(request):
    admin_id = request.session.get('admin_id')  # Get logged-in admin ID

    if not admin_id:
        messages.error(request, "You need to log in first.")
        return redirect('index')

    # Get all bus owners under this admin
    bus_owners = BusOwner.objects.filter(admin_id=admin_id)

    # Get all buses owned by these bus owners
    buses = Bus.objects.filter(owner__in=bus_owners)

    # Get all schedules related to these buses
    admin_schedules = Schedule.objects.filter(bus__in=buses)

    # Get all bookings related to these schedules
    admin_bookings = Booking.objects.filter(schedule__in=admin_schedules)

    # Get PayeeDetails related to these bookings
    payee_list = PayeeDetails.objects.filter(booking__in=admin_bookings).prefetch_related('passengertraveldetails_set')

    # Prepare structured data for the template
    travel_data = []
    for payee in payee_list:
        passenger_details = list(payee.passengertraveldetails_set.all())
        travel_data.append({
            "mobile_number": payee.mobile_number,
            "email": payee.email,
            "passengers": passenger_details
        })

    return render(request, 'admin/travel_details.html', {'travel_data': travel_data})
    
#---------------------------------------------------------

def admin_view_payments(request):
    # Check if admin is logged in
    admin_id = request.session.get('admin_id')
    if not admin_id:
        return render(request, 'error.html', {'message': 'You must be logged in as an admin.'})

    # Fetch all bus owners managed by this admin
    bus_owners = BusOwner.objects.filter(admin_id=admin_id)

    # Fetch all buses owned by these bus owners
    buses = Bus.objects.filter(owner__in=bus_owners)

    # Fetch all schedules associated with these buses
    schedules = Schedule.objects.filter(bus__in=buses)

    # Fetch all bookings related to these schedules
    bookings = Booking.objects.filter(schedule__in=schedules)

    # Fetch all payments related to these bookings
    payments = Payment.objects.filter(booking__in=bookings).order_by('payment_id')

    # Render the payments to the template
    return render(request, 'admin/view_payment.html', {'payments': payments})


#---------------------------------------------------------

def admin_view_cancellations(request):
    # Check if admin is logged in
    admin_id = request.session.get('admin_id')
    if not admin_id:
        return render(request, 'error.html', {'message': 'You must be logged in as an admin.'})

    # Fetch all bus owners managed by this admin
    bus_owners = BusOwner.objects.filter(admin_id=admin_id)

    # Fetch all buses owned by these bus owners
    buses = Bus.objects.filter(owner__in=bus_owners)

    # Fetch all schedules associated with these buses
    schedules = Schedule.objects.filter(bus__in=buses)

    # Fetch all bookings related to these schedules
    bookings = Booking.objects.filter(schedule__in=schedules)

    # Fetch all cancellations related to these bookings
    cancellations = Cancellation.objects.filter(booking__in=bookings).order_by('cancellation_id')

    # Render the cancellations to the template
    return render(request, 'admin/view_cancel.html', {'cancellations': cancellations})


#---------------------------------------------------------

def admin_view_passenger(request):
    passengers = Passenger.objects.all()
    return render(request, 'admin/view_passengers.html', {'passengers': passengers})

def admin_delete_passenger(request, id):
    try:
        passenger = Passenger.objects.get(passenger_id=id)
        passenger.delete()
        messages.success(request, 'Passenger deleted successfully.')
    except Passenger.DoesNotExist:
        messages.error(request, 'Passenger not found.')
    return redirect('admin_view_passenger') 

#---------------------------------------------------------

def admin_view_employees(request):
    # Fetch the admin_id from the session
    admin_id = request.session.get('admin_id')

    if not admin_id:
        messages.error(request, 'You need to log in as an admin to view this page.')
        return redirect('index')  # Redirect to login page or dashboard

    # Get the admin object
    try:
        admin = Admin.objects.get(admin_id=admin_id)
    except Admin.DoesNotExist:
        messages.error(request, 'Invalid admin session. Please log in again.')
        return redirect('index')  # Redirect to login page or dashboard

    # Get bus owners associated with the admin
    bus_owners = BusOwner.objects.filter(admin=admin)

    # Get employees (drivers and staff) associated with the bus owners
    employees = Employee.objects.filter(owner__in=bus_owners).order_by('employee_id')

    # Render the employees to the template
    return render(request, 'admin/view_employees.html', {'employees': employees})

#---------------------------------------------------------

def admin_view_buses(request):
    # Fetch the admin_id from the session
    admin_id = request.session.get('admin_id')

    if not admin_id:
        messages.error(request, 'You need to log in as an admin to view this page.')
        return redirect('index')  # Redirect to login page or dashboard

    # Get the logged-in admin object
    try:
        admin = Admin.objects.get(admin_id=admin_id)
    except Admin.DoesNotExist:
        messages.error(request, 'Invalid admin session. Please log in again.')
        return redirect('index')  # Redirect to login page or dashboard

    # Get bus owners associated with the logged-in admin
    bus_owners = BusOwner.objects.filter(admin=admin)

    # Get all buses associated with these bus owners
    buses = Bus.objects.filter(owner__in=bus_owners).order_by('bus_id')

    # Pass the buses to the template
    return render(request, 'admin/view_bus.html', {'buses': buses})

#---------------------------------------------------------

def admin_view_route(request):
    # Fetch the admin_id from the session
    admin_id = request.session.get('admin_id')

    if not admin_id:
        messages.error(request, 'You need to log in as an admin to view this page.')
        return redirect('index')  # Redirect to login page or dashboard

    # Get the admin object
    try:
        admin = Admin.objects.get(admin_id=admin_id)
    except Admin.DoesNotExist:
        messages.error(request, 'Invalid admin session. Please log in again.')
        return redirect('index')  # Redirect to login page or dashboard

    # Get bus owners associated with the admin
    bus_owners = BusOwner.objects.filter(admin=admin)

    # Get the routes of buses added by the bus owners
    routes = Route.objects.filter(owner__in=bus_owners).order_by('route_id')

    # Render the routes to the template
    return render(request, 'admin/view_route.html', {'routes': routes})

#---------------------------------------------------------

def admin_manage_bus_owner(request, owner_id=None):
    # Fetch the admin_id from the session
    admin_id = request.session.get('admin_id')

    if not admin_id:
        messages.error(request, 'You need to log in as an admin to view this page.')
        return redirect('index')  # Redirect to login page or dashboard

    # Get the logged-in admin object
    try:
        admin = Admin.objects.get(admin_id=admin_id)
    except Admin.DoesNotExist:
        messages.error(request, 'Invalid admin session. Please log in again.')
        return redirect('index')  # Redirect to login page or dashboard

    # Get bus owners associated with the logged-in admin
    bus_owners = BusOwner.objects.filter(admin=admin)

    # Pass the bus owners to the template
    return render(request, 'admin/edit_busowner.html', {'bus_owners': bus_owners})

#---------------------------------------------------------

def admin_view_schedules(request):
    # Fetch the admin_id from the session
    admin_id = request.session.get('admin_id')

    if not admin_id:
        messages.error(request, 'You need to log in as an admin to view this page.')
        return redirect('index')  # Redirect to login page or dashboard

    # Get the admin object
    try:
        admin = Admin.objects.get(admin_id=admin_id)
    except Admin.DoesNotExist:
        messages.error(request, 'Invalid admin session. Please log in again.')
        return redirect('index')  # Redirect to login page or dashboard

    # Get bus owners associated with the admin
    bus_owners = BusOwner.objects.filter(admin=admin)

    # Get schedules added by the bus owners
    schedules = Schedule.objects.filter(owner__in=bus_owners).order_by('schedule_id')

    # Render the schedules to the template
    return render(request, 'admin/view_schedule.html', {'schedules': schedules})

#---------------------------------------------------------

def admin_edit_bus_owner(request, id):
    try:
        # Get the bus owner by owner_id (using the 'id' parameter from the URL)
        bus_owner = BusOwner.objects.get(owner_id=id)
    except BusOwner.DoesNotExist:
        messages.error(request, 'Bus owner not found.')
        return redirect('admin_manage_bus_owner')  # Redirect if not found

    if request.method == 'POST':
        # Get the updated data from the form
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone_number = request.POST.get('phone_number')

        # Check if the email has changed and if it's already associated with another bus owner
        if email != bus_owner.email and BusOwner.objects.exclude(owner_id=id).filter(email=email).exists():
            messages.error(request, 'This email is already associated with another bus owner.')
            return redirect('admin_edit_bus_owner', id=id)  # Stay on the edit page
        
        # Check if the phone number has changed and if it's already associated with another bus owner
        if phone_number != bus_owner.phone_number and BusOwner.objects.exclude(owner_id=id).filter(phone_number=phone_number).exists():
            messages.error(request, 'This phone number is already associated with another bus owner.')
            return redirect('admin_edit_bus_owner', id=id)  # Stay on the edit page

        # Update the bus owner's details
        bus_owner.name = name
        bus_owner.email = email
        bus_owner.phone_number = phone_number

        # Save the updated bus owner details
        bus_owner.save()
        messages.success(request, 'Bus owner updated successfully.')
        return redirect('admin_manage_bus_owner')  # Redirect to the list of bus owners

    # Render the edit page and pass the bus owner to the template
    return render(request, 'admin/edit_busowners.html', {'bus_owner': bus_owner})

#---------------------------------------------------------

def admin_profile(request):
    admin = Admin.objects.first()  # Assuming a single admin exists

    if request.method == 'POST':
        email = request.POST.get('email')
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        # Check if old password matches
        if old_password != admin.password:
            messages.error(request, "Old password is incorrect.")
            return redirect('admin_profile')

        # Ensure new password is different from the old password
        if new_password == old_password:
            messages.error(request, "New password cannot be the same as the old password.")
            return redirect('admin_profile')

        # Ensure new password and confirm password match
        if new_password != confirm_password:
            messages.error(request, "New password and confirm password do not match.")
            return redirect('admin_profile')

        # Update email and password
        admin.email = email
        admin.password = new_password  # Ideally, use hashing here
        admin.save()

        messages.success(request, "Profile updated successfully!")
        return redirect('admin_profile')

    return render(request, 'admin/profile.html', {'admin': admin})

#---------------------------------------------------------

def admin_delete_bus_owner(request, id):
    try:
        # Get the bus owner by owner_id (using the 'id' parameter from the URL)
        bus_owner = BusOwner.objects.get(owner_id=id)
        bus_owner.delete()  # Delete the bus owner
        messages.success(request, 'Bus owner deleted successfully.')
    except BusOwner.DoesNotExist:
        messages.error(request, 'Bus owner not found.')

    return redirect('admin_manage_bus_owner')  # Redirect back to the list of bus owners

#-----------------------------------------------------------------------------------------------------------

#----------------------------------View for login redirect to Bus Owner dashboard function-------------------

from django.db.models.functions import ExtractMonth
from django.db.models import Count
import json

def busowner_dashboard(request):
    owner_id = request.session.get('owner_id')
    if not owner_id:
        messages.error(request, 'You need to log in first.')
        return redirect('index')

    try:
        bus_owner = BusOwner.objects.get(owner_id=owner_id)
        owner_name = bus_owner.name
    except BusOwner.DoesNotExist:
        messages.error(request, 'Invalid session. Please log in again.')
        return redirect('index')

    # Fetch counts related to the bus owner
    bus_count = Bus.objects.filter(owner=bus_owner).count()
    route_count = Route.objects.filter(bus__owner=bus_owner).count()
    booking_count = Booking.objects.count()
    schedule_count = Schedule.objects.filter(owner=bus_owner).count()
    passenger_count = Passenger.objects.count()

    # Fetch booking statistics based on payment_date from Payment table
    booking_stats = Payment.objects.filter(booking__schedule__owner=bus_owner) \
        .annotate(month=ExtractMonth('payment_date')) \
        .values('month') \
        .annotate(count=Count('payment_id')) \
        .order_by('month')

    # Fetch cancellation statistics based on cancellation_date
    cancellation_stats = Cancellation.objects.annotate(month=ExtractMonth('cancellation_date')) \
        .values('month') \
        .annotate(count=Count('cancellation_id')) \
        .order_by('month')

    # Convert data into a dictionary with months
    months_map = {1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun",
                  7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"}

    booking_data = {months_map[stat['month']]: stat['count'] for stat in booking_stats}
    cancellation_data = {months_map[stat['month']]: stat['count'] for stat in cancellation_stats}
    # **Fix: Initialize passengers and employees as empty lists**
    passengers = []
    employees = []

    # Search functionality
    query = request.POST.get('keywords', '')

    if query:
        passengers = Passenger.objects.filter(
            Q(name__icontains=query) | Q(email__icontains=query) | Q(phone_number__icontains=query)
        )

        employees = Employee.objects.filter(
            Q(name__icontains=query) | Q(email__icontains=query) | Q(phone_number__icontains=query),
            owner=bus_owner  # Use bus_owner fetched from session
        )

    # Combine results
    search_results = {
        'passengers': passengers,
        'employees': employees,
    }

    context = {
        'owner_name': owner_name,
        'bus_owner': bus_owner,
        'bus_count': bus_count,
        'route_count': route_count,
        'booking_count': booking_count,
        'schedule_count': schedule_count,
        'passenger_count': passenger_count,
        'booking_data': json.dumps(booking_data),
        'cancellation_data': json.dumps(cancellation_data),
        'search_results': search_results,
    }

    driver_count = Employee.objects.filter(role='Driver', owner=bus_owner).count()
    staff_count = Employee.objects.filter(role='Staff', owner=bus_owner).count()
    context['driver_count'] = driver_count
    context['staff_count'] = staff_count

    return render(request, 'busowner/busowner_dashboard.html', context)

#---------------------------------------Views for the Bus Owner----------------------------------------------

from django.db import IntegrityError
from django.contrib import messages
from django.shortcuts import render, redirect
from .models import Bus, BusOwner

def owner_add_bus(request):
    # Fetch the owner_id from the session
    owner_id = request.session.get('owner_id')

    if not owner_id:
        messages.error(request, 'You need to log in as a bus owner to access this page.')
        return redirect('index')  # Redirect to login page or dashboard

    try:
        # Get the logged-in bus owner object
        bus_owner = BusOwner.objects.get(owner_id=owner_id)
    except BusOwner.DoesNotExist:
        messages.error(request, 'Invalid bus owner session. Please log in again.')
        return redirect('index')  # Redirect to login page or dashboard

    if request.method == 'POST':
        # Get data from the form
        bus_name = request.POST.get('bus_name')
        capacity = request.POST.get('capacity')
        registration_number = request.POST.get('registration_number')
        bus_type = request.POST.get('bus_type')
        fare_rate = request.POST.get('fare_rate')
        base_fare = request.POST.get('base_fare')  # Don't forget base fare if needed
        travel_company_name = request.POST.get('travel_company_name')
        status = request.POST.get('status')
        

        # Validate the form fields (basic validation)
        if not bus_name or not capacity or not registration_number or not fare_rate or not base_fare or not travel_company_name:
            messages.error(request, 'All fields are required.')
            return redirect('owner_add_bus')

        # Check if a bus with the same registration number already exists
        if Bus.objects.filter(registration_number=registration_number).exists():
            messages.error(request, 'A bus with this registration number already exists.')
            return redirect('owner_add_bus')

        try:
            # Save the new bus to the database
            Bus.objects.create(
                bus_name=bus_name,
                capacity=capacity,
                registration_number=registration_number,
                bus_type=bus_type,
                base_fare=base_fare,
                fare_rate=fare_rate,
                travel_company_name=travel_company_name,
                status=status,
                owner=bus_owner
            )
            messages.success(request, 'Bus added successfully.')
            return redirect('owner_add_bus')

        except IntegrityError:
            messages.error(request, 'An error occurred while adding the bus. Please try again.')
            return redirect('owner_add_bus')

    # Render the add_bus page for GET requests
    return render(request, 'busowner/add_bus.html')

#---------------------------------------------------------

def owner_add_employee(request):
    # Fetch the owner_id from the session
    owner_id = request.session.get('owner_id')

    if not owner_id:
        messages.error(request, 'You need to log in as a bus owner to access this page.')
        return redirect('index')  # Redirect to login page

    try:
        # Get the logged-in bus owner object
        bus_owner = BusOwner.objects.get(owner_id=owner_id)
    except BusOwner.DoesNotExist:
        messages.error(request, 'Invalid bus owner session. Please log in again.')
        return redirect('index')  # Redirect to login page

    if request.method == 'POST':
        # Get data from the form
        name = request.POST.get('name')
        email = request.POST.get('email')
        role = request.POST.get('role')
        phone_number = request.POST.get('phone_number')
        license_number = request.POST.get('license_number')  # Accepts license number for both roles
        password = request.POST.get('password')

        # Validate required fields
        if not name or not email or not role or not phone_number or not password or not license_number:
            messages.error(request, 'All fields are required, including license number.')
            return redirect('owner_add_employee')

        # Check if an employee with the same email, phone number, or license number already exists
        if Employee.objects.filter(email=email).exists():
            messages.error(request, 'An employee with this email already exists.')
            return redirect('owner_add_employee')

        if Employee.objects.filter(phone_number=phone_number).exists():
            messages.error(request, 'An employee with this phone number already exists.')
            return redirect('owner_add_employee')

        if Employee.objects.filter(license_number=license_number).exists():
            messages.error(request, 'An employee with this license number already exists.')
            return redirect('owner_add_employee')

        try:
            # Create and save the new employee (password stored as plain text)
            Employee.objects.create(
                name=name,
                email=email,
                role=role,
                phone_number=phone_number,
                license_number=license_number,
                password=password,  # Password is stored as plain text
                owner=bus_owner
            )
            messages.success(request, 'Employee added successfully.')
            return redirect('owner_add_employee')  # Redirect after success

        except IntegrityError:
            messages.error(request, 'An error occurred while adding the employee. Please try again.')
            return redirect('owner_add_employee')

    # Render the add_employee page for GET requests
    return render(request, 'busowner/add_employee.html')

#---------------------------------------------------------

def owner_add_route(request):
    owner_id = request.session.get('owner_id')  # Fetch owner ID from session

    if request.method == 'POST':
        source = request.POST.get('source')
        destination = request.POST.get('destination')
        distance = request.POST.get('distance')
        bus_id = request.POST.get('bus_id')

        if source and destination and bus_id:
            try:
                bus = Bus.objects.get(bus_id=bus_id)
                
                owner = None
                if owner_id:  # Check if owner_id exists in the session
                    try:
                        owner = BusOwner.objects.get(owner_id=owner_id)
                    except BusOwner.DoesNotExist:
                        messages.error(request, "Invalid owner. Please log in again.")

                # Create the Route and associate the owner
                route = Route.objects.create(
                    source=source,
                    destination=destination,
                    distance=distance if distance else None,
                    owner=owner,
                    bus=bus
                )
                messages.success(request, "Route added successfully!")

            except Bus.DoesNotExist:
                messages.error(request, "Invalid bus selection.")
        else:
            messages.error(request, "Please fill in all required fields.")

    buses = Bus.objects.filter(owner_id=owner_id)
    return render(request, 'busowner/add_route.html', {'buses': buses})

#---------------------------------------------------------

def owner_manage_route(request, route_id=None):
    # Fetch the owner_id from the session
    owner_id = request.session.get('owner_id')

    if not owner_id:
        messages.error(request, 'You need to log in as a bus owner to view this page.')
        return render(request, 'index.html')  # Render login page or dashboard

    # Get the logged-in bus owner object
    try:
        bus_owner = BusOwner.objects.get(owner_id=owner_id)
    except BusOwner.DoesNotExist:
        messages.error(request, 'Invalid owner session. Please log in again.')
        return render(request, 'index.html')  # Render login page or dashboard

    # Handle route deletion if route_id is provided
    if route_id:
        try:
            route = Route.objects.get(route_id=route_id, owner=bus_owner)
            route.delete()
            messages.success(request, 'Route deleted successfully.')
        except Route.DoesNotExist:
            messages.error(request, 'Route not found or does not belong to you.')

    # Get all routes associated with this bus owner
    routes = Route.objects.filter(owner=bus_owner).order_by('route_id')

    return render(request, 'busowner/edit_route.html', {'routes': routes})

#---------------------------------------------------------

def owner_delete_schedule(request, schedule_id):
    owner_id = request.session.get("owner_id")

    if not owner_id:
        messages.error(request, "You need to log in as a bus owner to perform this action.")
        return redirect("index")

    try:
        schedule = Schedule.objects.get(schedule_id=schedule_id, owner__owner_id=owner_id)
        schedule.delete()
        messages.success(request, "Schedule deleted successfully.")
    except Schedule.DoesNotExist:
        messages.error(request, "Schedule not found or does not belong to you.")

    return redirect("owner_manage_schedule")

#---------------------------------------------------------

def owner_edit_route(request, route_id):
    try:
        route = Route.objects.get(route_id=route_id)
    except Route.DoesNotExist:
        messages.error(request, "Route not found.")
        return render(request, 'busowner/manage_routes.html')  # Render the route management page

    if request.method == "POST":
        source = request.POST.get("source")
        destination = request.POST.get("destination")
        distance = request.POST.get("distance")
        bus_id = request.POST.get("bus")

        # Validate input data
        if not source or not destination or not distance or not bus_id:
            messages.error(request, "All fields are required.")
            return render(request, 'busowner/edit_route.html', {'route': route})

        # Validate distance (must be a positive number)
        try:
            distance = float(distance)
            if distance <= 0:
                messages.error(request, "Distance must be a positive number.")
                return render(request, 'busowner/edit_route.html', {'route': route})
        except ValueError:
            messages.error(request, "Invalid distance value.")
            return render(request, 'busowner/edit_route.html', {'route': route})

        # Update and save the route details
        route.source = source
        route.destination = destination
        route.distance = distance
        route.bus_id = bus_id  # Assuming bus_id is passed as a valid bus instance
        route.save()

        # Refresh the updated data
        route.refresh_from_db()

        messages.success(request, "Route details updated successfully.")

    return render(request, 'busowner/edit_route.html', {'route': route})

#---------------------------------------------------------
from datetime import datetime

def owner_add_schedule(request):
    owner_id = request.session.get('owner_id')

    if request.method == 'POST':
        bus_id = request.POST.get('bus_id')
        route_id = request.POST.get('route_id')
        
        start_date = request.POST.get('start_date')
        start_time = request.POST.get('start_time')
        end_date = request.POST.get('end_date')
        end_time = request.POST.get('end_time')

        if bus_id and route_id and start_date and start_time and end_date and end_time:
            try:
                departure_time = datetime.strptime(f"{start_date} {start_time}", "%Y-%m-%d %H:%M")
                arrival_time = datetime.strptime(f"{end_date} {end_time}", "%Y-%m-%d %H:%M")

                bus = Bus.objects.get(bus_id=bus_id)
                route = Route.objects.get(route_id=route_id)
                
                owner = None
                if owner_id:
                    try:
                        owner = BusOwner.objects.get(owner_id=owner_id)
                    except BusOwner.DoesNotExist:
                        messages.error(request, "Invalid owner. Please log in again.")

                Schedule.objects.create(
                    bus=bus,
                    route=route,
                    departure_time=departure_time,
                    arrival_time=arrival_time,
                    owner=owner
                )
                messages.success(request, "Schedule added successfully!")

            except (Bus.DoesNotExist, Route.DoesNotExist):
                messages.error(request, "Invalid bus or route selection.")
            except ValueError:
                messages.error(request, "Invalid date or time format.")
        else:
            messages.error(request, "Please fill in all required fields.")

    buses = Bus.objects.filter(owner_id=owner_id)
    routes = Route.objects.filter(owner_id=owner_id)
    return render(request, 'busowner/add_schedule.html', {'buses': buses, 'routes': routes})

#---------------------------------------------------------

def owner_edit_schedule(request, schedule_id):
    try:
        schedule = Schedule.objects.get(schedule_id=schedule_id)
    except Schedule.DoesNotExist:
        messages.error(request, "Schedule not found.")
        return render(request, 'busowner/manage_schedules.html')  # Render the schedule management page

    if request.method == "POST":
        departure_time = request.POST.get("departure_time")
        arrival_time = request.POST.get("arrival_time")

        # Validate input data
        if not departure_time or not arrival_time:
            messages.error(request, "All fields are required.")
            return render(request, 'busowner/edit_schedule.html', {'schedule': schedule})

        # Update schedule details
        schedule.departure_time = departure_time
        schedule.arrival_time = arrival_time
        schedule.save()

        # After updating, fetch the latest schedule and show the updated values
        schedule.refresh_from_db()  # Ensure the latest data is fetched

        messages.success(request, "Schedule details updated successfully.")
        return render(request, 'busowner/edit_schedules.html')  # Render the schedule management page
    
        #return redirect('owner_manage_schedule') 
    
    return render(request, 'busowner/edit_schedules.html', {'schedule': schedule})

#---------------------------------------------------------

def owner_edit_route(request, route_id):
    try:
        route = Route.objects.get(route_id=route_id)
    except Route.DoesNotExist:
        messages.error(request, "Route not found.")
        return redirect('owner_manage_routes')

    if request.method == "POST":
        source = request.POST.get("source")
        destination = request.POST.get("destination")
        distance = request.POST.get("distance")
        bus_id = request.POST.get("bus")

        # Validate input data
        if not source or not destination or not distance or not bus_id:
            messages.error(request, "All fields are required.")
            return redirect(request.path)

        # Check if the distance is valid (positive number)
        try:
            distance = float(distance)
            if distance <= 0:
                messages.error(request, "Distance must be a positive number.")
                return redirect(request.path)
        except ValueError:
            messages.error(request, "Invalid distance value.")
            return redirect(request.path)

        # Update and save the route details
        route.source = source
        route.destination = destination
        route.distance = distance
        route.bus_id = bus_id  # Assuming bus_id is passed as a valid bus instance
        route.save()

        messages.success(request, "Route details updated successfully.")
        return redirect(request.path)  # Stay on the same page after updating

    return render(request, 'busowner/edit_routes.html', {'route': route})

#---------------------------------------------------------

def owner_edit_employees(request, employee_id):
    try:
        employee = Employee.objects.get(employee_id=employee_id)
    except Employee.DoesNotExist:
        messages.error(request, "Employee not found.")
        return redirect('owner_manage_employee')

    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")
        role = request.POST.get("role")
        phone_number = request.POST.get("phone_number")
        license_number = request.POST.get("license_number")
        password = request.POST.get("password")

        # Check if email is already used by another employee
        if Employee.objects.filter(email=email).exclude(employee_id=employee_id).exists():
            messages.error(request, "This email is already in use by another employee. Please use a unique email.")
            return redirect(request.path)

        # Check if phone number is already used by another employee
        if Employee.objects.filter(phone_number=phone_number).exclude(employee_id=employee_id).exists():
            messages.error(request, "This phone number is already in use by another employee. Please use a unique phone number.")
            return redirect(request.path)

        # Check if license number is already used by another employee
        if Employee.objects.filter(license_number=license_number).exclude(employee_id=employee_id).exists():
            messages.error(request, "This license number is already in use by another employee. Please use a unique license number.")
            return redirect(request.path)

        # Update and save the employee details
        employee.name = name
        employee.email = email
        employee.role = role
        employee.phone_number = phone_number
        employee.license_number = license_number
        employee.password = password  # Stored as plain text, as per your request
        employee.save()

        messages.success(request, "Employee details updated successfully.")
        return redirect('owner_manage_employee')  # Redirect to employee management page

    return render(request, 'busowner/edit_employees.html', {'employee': employee})

#---------------------------------------------------------

def owner_manage_employee(request, employee_id=None):
    # Fetch the owner_id from the session
    owner_id = request.session.get('owner_id')

    if not owner_id:
        messages.error(request, 'You need to log in as a bus owner to view this page.')
        return redirect('index')  # Redirect to login page or dashboard

    # Get the logged-in bus owner object
    try:
        bus_owner = BusOwner.objects.get(owner_id=owner_id)
    except BusOwner.DoesNotExist:
        messages.error(request, 'Invalid owner session. Please log in again.')
        return redirect('index')  # Redirect to login page or dashboard

    # Handle employee deletion if employee_id is provided in GET
    if employee_id:
        try:
            employee = Employee.objects.get(employee_id=employee_id)
            employee.delete()
            messages.success(request, 'Employee deleted successfully.')
        except Employee.DoesNotExist:
            messages.error(request, 'Employee not found.')

        return redirect('owner_manage_employee').order_by('schedule_id')  # Redirect back to employee management page

    # Get all employees associated with this bus owner
    employees = Employee.objects.filter(owner=bus_owner).order_by('employee_id')

    # Pass the employees to the template
    return render(request, 'busowner/edit_employee.html', {'employees': employees})

#---------------------------------------------------------

def owner_manage_bus(request, bus_id=None):
    # Fetch the owner_id from the session
    owner_id = request.session.get('owner_id')

    if not owner_id:
        messages.error(request, 'You need to log in as a bus owner to view this page.')
        return redirect('index')  # Redirect to login page or dashboard

    # Get the logged-in bus owner object
    try:
        bus_owner = BusOwner.objects.get(owner_id=owner_id)
    except BusOwner.DoesNotExist:
        messages.error(request, 'Invalid owner session. Please log in again.')
        return redirect('index')  # Redirect to login page or dashboard

    # Handle bus deletion if bus_id is provided in GET
    if bus_id:
        try:
            bus = Bus.objects.get(bus_id=bus_id)
            bus.delete()
            messages.success(request, 'Bus deleted successfully.')
        except Bus.DoesNotExist:
            messages.error(request, 'Bus not found.')

        return redirect('owner_manage_bus')  # Redirect back to bus management page

    # Get all buses associated with this bus owner
    buses = Bus.objects.filter(owner=bus_owner).order_by('bus_id')

    # Pass the buses to the template
    return render(request, 'busowner/edit_bus.html', {'buses': buses})

#---------------------------------------------------------

def owner_manage_schedule(request, schedule_id=None):
    # Fetch the owner_id from the session
    owner_id = request.session.get('owner_id')

    if not owner_id:
        messages.error(request, 'You need to log in as a bus owner to view this page.')
        return render(request, 'index.html')  # Render login page or dashboard

    # Get the logged-in bus owner object
    try:
        bus_owner = BusOwner.objects.get(owner_id=owner_id)
    except BusOwner.DoesNotExist:
        messages.error(request, 'Invalid owner session. Please log in again.')
        return render(request, 'index.html')  # Render login page or dashboard

    # Handle POST request for bulk delete
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'delete_selected':
            selected_schedules = request.POST.getlist('selected_schedules')
            
            if selected_schedules:
                try:
                    # Delete selected schedules that belong to this owner
                    deleted_count = Schedule.objects.filter(
                        schedule_id__in=selected_schedules, 
                        owner=bus_owner
                    ).delete()[0]
                    
                    if deleted_count > 0:
                        messages.success(request, f'{deleted_count} schedule(s) deleted successfully.')
                    else:
                        messages.warning(request, 'No schedules were deleted. They may not belong to you.')
                        
                except Exception as e:
                    messages.error(request, f'Error deleting schedules: {str(e)}')
            else:
                messages.warning(request, 'No schedules selected for deletion.')
                
            return redirect('owner_manage_schedule')

    # Handle schedule deletion if schedule_id is provided in GET (single delete)
    if schedule_id:
        try:
            schedule = Schedule.objects.get(schedule_id=schedule_id, owner=bus_owner)
            schedule.delete()
            messages.success(request, 'Schedule deleted successfully.')
        except Schedule.DoesNotExist:
            messages.error(request, 'Schedule not found or does not belong to you.')
        
        return redirect('owner_manage_schedule')

    # Get all schedules associated with this bus owner
    schedules = Schedule.objects.filter(owner=bus_owner).order_by('schedule_id')

    # Pass the schedules to the template
    return render(request, 'busowner/edit_schedule.html', {'schedules': schedules})


#---------------------------------------------------------

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Bus, BusImage

def owner_edit_bus(request, bus_id):
    bus = get_object_or_404(Bus, bus_id=bus_id)

    if request.method == "POST":
        bus_name = request.POST.get("bus_name")
        capacity = request.POST.get("capacity")
        registration_number = request.POST.get("registration_number")
        bus_type = request.POST.get("bus_type")
        base_fare = request.POST.get("base_fare")
        fare_rate = request.POST.get("fare_rate")
        travel_company_name = request.POST.get("travel_company_name")
        status = request.POST.get("status")

        # Check if registration number already exists for another bus
        if Bus.objects.exclude(bus_id=bus_id).filter(registration_number=registration_number).exists():
            messages.error(request, "This registration number is already in use. Please use a unique registration number.")
            return redirect(request.path)

        # Update and save the bus details
        bus.bus_name = bus_name
        bus.capacity = capacity
        bus.registration_number = registration_number
        bus.bus_type = bus_type
        bus.base_fare = base_fare
        bus.fare_rate = fare_rate
        bus.travel_company_name = travel_company_name
        bus.status = status
        bus.save()

        # Optional: Handle new image uploads
        if request.FILES.getlist('images'):
            # Delete existing images
            bus.images.all().delete()
            for img in request.FILES.getlist('images'):
                BusImage.objects.create(bus=bus, image=img)

        messages.success(request, "Bus details updated successfully.")
        return redirect(request.path)

    return render(request, 'busowner/edit_buses.html', {'bus': bus})


#---------------------------------------------------------

def busowner_profile(request):
    owner_id = request.session.get('owner_id')
    
    if not owner_id:
        messages.error(request, "You need to log in first.")
        return redirect('index')  # Redirect to login page

    # Fetch the bus owner object
    bus_owner = BusOwner.objects.filter(owner_id=owner_id).first()

    if not bus_owner:
        messages.error(request, "Bus owner profile not found!")
        return redirect('busowner_dashboard')  # Redirect to an error page

    if request.method == 'POST':
        email = request.POST.get('email')
        phone_number = request.POST.get('phone_number')
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        # Check if old password matches
        if old_password != bus_owner.password:
            messages.error(request, "Old password is incorrect.")
            return redirect('busowner_profile')

        # Ensure new password is different from the old password
        if new_password == old_password:
            messages.error(request, "New password cannot be the same as the old password.")
            return redirect('busowner_profile')

        # Ensure new password and confirm password match
        if new_password != confirm_password:
            messages.error(request, "New password and confirm password do not match.")
            return redirect('busowner_profile')

        # Update email, phone number, and password
        bus_owner.email = email
        bus_owner.phone_number = phone_number
        bus_owner.password = new_password  # Use hashing in production
        bus_owner.save()

        messages.success(request, "Profile updated successfully!")
        return redirect('busowner_profile')

    return render(request, 'busowner/profile.html', {'bus_owner': bus_owner})



#---------------------------------------------------------

def owner_view_passenger(request):
    passengers = Passenger.objects.all().order_by('passenger_id')
    return render(request, 'busowner/view_passengers.html', {'passengers': passengers})

#---------------------------------------------------------

def owner_view_bookings(request):
    owner_id = request.session.get('owner_id')  # Get logged-in owner ID

    if not owner_id:
        messages.error(request, "You need to log in first.")
        return redirect('index')

    # Get all schedules that belong to this bus owner
    owner_schedules = Schedule.objects.filter(owner_id=owner_id)

    # Get bookings that are linked to these schedules
    bookings = Booking.objects.filter(schedule__in=owner_schedules).order_by('booking_id')

    return render(request, 'busowner/view_bookings.html', {'bookings': bookings})


#---------------------------------------------------------

def owner_view_payments(request):
    owner_id = request.session.get('owner_id')  # Get logged-in owner ID

    if not owner_id:
        messages.error(request, "You need to log in first.")
        return redirect('index')

    # Get all schedules that belong to this bus owner
    owner_schedules = Schedule.objects.filter(owner_id=owner_id)

    # Get all bookings related to the owner's schedules
    owner_bookings = Booking.objects.filter(schedule__in=owner_schedules)

    # Get all payments related to these bookings
    payments = Payment.objects.filter(booking__in=owner_bookings).order_by('payment_id')

    return render(request, 'busowner/view_payment.html', {'payments': payments})

#---------------------------------------------------------

def owner_view_cancellations(request):
    owner_id = request.session.get('owner_id')  # Get logged-in owner ID

    if not owner_id:
        messages.error(request, "You need to log in first.")
        return redirect('index')

    # Get all schedules that belong to this bus owner
    owner_schedules = Schedule.objects.filter(owner_id=owner_id)

    # Get all bookings related to the owner's schedules
    owner_bookings = Booking.objects.filter(schedule__in=owner_schedules)

    # Get all cancellations related to these bookings
    cancellations = Cancellation.objects.filter(booking__in=owner_bookings).order_by('cancellation_id')

    return render(request, 'busowner/view_cancel.html', {'cancellations': cancellations})

#---------------------------------------------------------

def owner_view_buses(request):
    # Fetch the owner_id from the session
    owner_id = request.session.get('owner_id')

    if not owner_id:
        messages.error(request, 'You need to log in as a bus owner to view this page.')
        return redirect('index')  # Redirect to login page or dashboard

    # Get the logged-in bus owner object
    try:
        bus_owner = BusOwner.objects.get(owner_id=owner_id)
    except BusOwner.DoesNotExist:
        messages.error(request, 'Invalid owner session. Please log in again.')
        return redirect('index')  # Redirect to login page or dashboard

    # Get all buses associated with this bus owner
    buses = Bus.objects.filter(owner=bus_owner).order_by('bus_id')

    # Pass the buses to the template
    return render(request, 'busowner/view_bus.html', {'buses': buses})

#---------------------------------------------------------

def owner_view_route(request):
    # Fetch the owner_id from the session
    owner_id = request.session.get('owner_id')

    if not owner_id:
        messages.error(request, 'You need to log in as an owner to view this page.')
        return redirect('index')  # Redirect to login page or dashboard

    # Get the owner object
    try:
        bus_owners = BusOwner.objects.get(owner_id=owner_id)
    except BusOwner.DoesNotExist:
        messages.error(request, 'Invalid owner session. Please log in again.')
        return redirect('index')  # Redirect to login page or dashboard

    # Get the routes of buses added by the bus owners
    routes = Route.objects.filter(owner=bus_owners).order_by('route_id')

    # Render the routes to the template
    return render(request, 'busowner/view_route.html', {'routes': routes})

#---------------------------------------------------------

def owner_view_attendance(request):
    # Fetch the owner_id from the session
    owner_id = request.session.get('owner_id')

    if not owner_id:
        messages.error(request, 'You need to log in as an owner to view this page.')
        return redirect('index')  # Redirect to login page or dashboard

    # Get the owner object
    try:
        bus_owner = BusOwner.objects.get(owner_id=owner_id)
    except BusOwner.DoesNotExist:
        messages.error(request, 'Invalid owner session. Please log in again.')
        return redirect('index')  # Redirect to login page or dashboard

    # Fetch employees that belong to this bus owner
    employees = Employee.objects.filter(owner=bus_owner)

    # Fetch attendance records only for employees belonging to this owner
    attendance_records = Attendance.objects.filter(employee__in=employees).select_related('employee', 'schedule').order_by('attendance_id')

    # Render the attendance records to the template
    return render(request, 'busowner/view_attendance.html', {'attendance_records': attendance_records})

#---------------------------------------------------------

def toggle_attendance_status(request, attendance_id):
    try:
        # Fetch the attendance record manually
        attendance = Attendance.objects.get(attendance_id=attendance_id)
        
        # Toggle the status
        attendance.status = "Absent" if attendance.status == "Present" else "Present"

        # Save the changes
        attendance.save()
        messages.success(request, "Attendance status updated successfully.")

    except Attendance.DoesNotExist:
        messages.error(request, "Attendance record not found.")

    # Redirect back to the same page
    return redirect(request.META.get('HTTP_REFERER', 'owner_view_attendance'))

#---------------------------------------------------------

def owner_view_journey_dates(request):
    # Fetch the owner_id from the session
    owner_id = request.session.get('owner_id')

    if not owner_id:
        messages.error(request, 'You need to log in as an owner to view this page.')
        return redirect('index')  # Redirect to login page or dashboard

    # Get the owner object
    try:
        bus_owner = BusOwner.objects.get(owner_id=owner_id)
    except BusOwner.DoesNotExist:
        messages.error(request, 'Invalid owner session. Please log in again.')
        return redirect('index')  # Redirect to login page or dashboard

    # Fetch employees that belong to this bus owner
    employees = Employee.objects.filter(owner=bus_owner)

    # Fetch all journey dates assigned to these employees
    journey_dates = JourneyDate.objects.filter(employee__in=employees).order_by('journey_id')

    context = {
        'journey_dates': journey_dates
    }

    return render(request, 'busowner/view_journey_details.html', context)

#---------------------------------------------------------

def owner_view_schedules(request):
    # Fetch the owner_id from the session
    owner_id = request.session.get('owner_id')

    if not owner_id:
        messages.error(request, 'You need to log in as an owner to view this page.')
        return redirect('index')  # Redirect to login page or dashboard

    # Get the admin object
    try:
        bus_owners = BusOwner.objects.get(owner_id=owner_id)
    except BusOwner.DoesNotExist:
        messages.error(request, 'Invalid owner session. Please log in again.')
        return redirect('index')  # Redirect to login page or dashboard
    
    # Get schedules added by the bus owners
    schedules = Schedule.objects.filter(owner=bus_owners).order_by('schedule_id')

    # Render the schedules to the template
    return render(request, 'busowner/view_schedule.html', {'schedules': schedules})

#---------------------------------------------------------


def owner_view_employees(request):
    # Fetch the admin_id from the session
    owner_id = request.session.get('owner_id')

    if not owner_id:
        messages.error(request, 'You need to log in as an owner to view this page.')
        return redirect('index')  # Redirect to login page or dashboard

    # Get the owner object
    try:
        bus_owners = BusOwner.objects.get(owner_id=owner_id)
    except BusOwner.DoesNotExist:
        messages.error(request, 'Invalid owner session. Please log in again.')
        return redirect('index')  # Redirect to login page or dashboard

    # Get employees (drivers and staff) associated with the bus owners
    employees = Employee.objects.filter(owner=bus_owners)

    # Render the employees to the template
    return render(request, 'busowner/view_employees.html', {'employees': employees})

#---------------------------------------------------------

def owner_assign_employee(request):
    owner_id = request.session.get("owner_id")

    if not owner_id:
        messages.error(request, "You need to log in as an owner to view this page.")
        return redirect("index")

    # Get the owner object
    try:
        bus_owner = BusOwner.objects.get(owner_id=owner_id)
    except BusOwner.DoesNotExist:
        messages.error(request, "Invalid owner session. Please log in again.")
        return redirect("index")

    # Get employees (drivers and staff) associated with this owner
    employees = Employee.objects.filter(owner=bus_owner)

    # Get all assignments (employee_id, bus_name, schedule_id)
    assignments = EmployeeBusAssignment.objects.filter(employee__in=employees).select_related("bus", "schedule")

    # Dictionary to store employee assignments
    employee_assignments = {
        assignment.employee.employee_id: {
            "bus_name": assignment.bus.bus_name,
            "schedule_id": assignment.schedule.schedule_id,
        }
        for assignment in assignments
    }

    # Attach bus_name and schedule_id dynamically to employee objects
    for employee in employees:
        assignment = employee_assignments.get(employee.employee_id, None)
        employee.bus_name = assignment["bus_name"] if assignment else None
        employee.schedule_id = assignment["schedule_id"] if assignment else None

    context = {
        "employees": employees,
        "employee_assignments": employee_assignments,
    }

    return render(request, "busowner/assign_employee.html", context)

#---------------------------------------------------------

def bus_owner_travel_details_view(request):
    owner_id = request.session.get('owner_id')  # Get logged-in bus owner ID

    if not owner_id:
        messages.error(request, "You need to log in first.")
        return redirect('index')

    # Get all schedules belonging to this owner
    owner_schedules = Schedule.objects.filter(owner_id=owner_id)

    # Get all bookings related to the owner's schedules
    owner_bookings = Booking.objects.filter(schedule__in=owner_schedules)

    # Get PayeeDetails related to these bookings
    payee_list = PayeeDetails.objects.filter(booking__in=owner_bookings)

    # Fetch Passenger Travel Details related to the payees
    travel_details = PassengerTravelDetails.objects.filter(booking__in=owner_bookings)

    return render(request, 'busowner/travel_details.html', {
        'payee_list': payee_list,
        'travel_details': travel_details
    })

#---------------------------------------------------------

from django.db.models import Q

def owner_assign_employee_to_bus(request, employee_id=None):
    owner_id = request.session.get("owner_id")

    if not owner_id:
        messages.error(request, "You need to log in as an owner to view this page.")
        return redirect("index")

    bus_owner = get_object_or_404(BusOwner, owner_id=owner_id)
    employee = get_object_or_404(Employee, employee_id=employee_id, owner=bus_owner)
    buses = Bus.objects.filter(owner=bus_owner)

    assignment_message = None

    if request.method == "POST":
        bus_id = request.POST.get("bus_id")
        schedule_id = request.POST.get("schedule_id")

        if not bus_id or not schedule_id:
            messages.error(request, "Bus and schedule are required.")
            return redirect("owner_assign_employee_to_bus", employee_id=employee_id)

        try:
            bus = get_object_or_404(Bus, bus_id=bus_id)
            schedule = get_object_or_404(Schedule, schedule_id=schedule_id)

            # Check if this assignment already exists
            existing = EmployeeBusAssignment.objects.filter(
                employee=employee,
                bus=bus,
                schedule=schedule,
            ).first()

            if existing:
                messages.info(request, f"{employee.name} is already assigned to {bus.bus_name} on Schedule {schedule.schedule_id}.")
            else:
                # Create a new assignment
                EmployeeBusAssignment.objects.create(
                    employee=employee,
                    bus=bus,
                    schedule=schedule,
                )
                messages.success(request, f"{employee.name} has been assigned to {bus.bus_name} on Schedule {schedule.schedule_id}.")

            return redirect("owner_assign_employee_to_bus", employee_id=employee_id)

        except (Bus.DoesNotExist, Schedule.DoesNotExist):
            messages.error(request, "Invalid bus or schedule selection.")

    return render(
        request,
        "busowner/select_assign_employee.html",
        {
            "employee": employee,
            "buses": buses,
            "assignment_message": assignment_message,
        },
    )

#---------------------------------------------------------

def view_assigned_employees(request):
    # Get the logged-in bus owner's ID from the session
    owner_id = request.session.get('owner_id')

    if not owner_id:
        return render(request, 'error.html', {'message': 'You must be logged in as a bus owner.'})

    # Get all buses owned by the logged-in owner
    buses = Bus.objects.filter(owner_id=owner_id)

    # Get all employees added by this owner
    employees = Employee.objects.filter(owner_id=owner_id)

    # Get all assignments related to those buses and employees
    assignments = EmployeeBusAssignment.objects.filter(
        bus__in=buses,
        employee__in=employees
    ).select_related('employee', 'bus', 'schedule').order_by('employee__employee_id')

    return render(request, 'busowner/view_assign_employee.html', {'assignments': assignments})


#---------------------------------------------------------

def get_schedules(request, bus_id):
    try:
        bus = Bus.objects.get(bus_id=bus_id)
        schedules = Schedule.objects.filter(bus=bus).values("schedule_id", "departure_time", "arrival_time")

        return JsonResponse({"schedules": list(schedules)})
    except Bus.DoesNotExist:
        return JsonResponse({"error": "Bus not found"}, status=404)

#---------------------------------------------------------

def delete_assigned_employee(request, assignment_id):
    try:
        assignment = EmployeeBusAssignment.objects.get(id=assignment_id)
        assignment.delete()
        messages.success(request, 'Employee assignment deleted successfully.')
    except EmployeeBusAssignment.DoesNotExist:
        messages.error(request, 'Assignment not found.')

    return redirect('view_assigned_employees')  # Redirect to the list

#---------------------------------------------------------

def process_employee_bus_assignment(request, employee_id):
    print("1. Function called with employee_id:", employee_id)
    
    try:
        employee = Employee.objects.get(employee_id=employee_id)
        print("2. Found employee:", employee.name)
    except Employee.DoesNotExist:
        messages.error(request, 'Employee not found')
        return redirect('busowner_dashboard')
    
    if request.method == 'POST':
        print("3. POST data:", request.POST)  # This will show all POST data
        bus_id = request.POST.get('bus_id')
        print("4. Selected bus_id:", bus_id)
        
        if bus_id:
            try:
                # Try both ways to get the bus
                print("5. Attempting to find bus with bus_id:", bus_id)
                bus = Bus.objects.filter(bus_id=bus_id).first()
                if not bus:
                    print("6. Bus not found with bus_id, trying different fields")
                    # Try to get the first bus that matches any field
                    buses = Bus.objects.all()
                    print("7. Available buses:", [(b.bus_id, b.bus_name) for b in buses])
                
                if bus:
                    print("8. Found bus:", bus.bus_name)
                    # Check if assignment exists
                    existing_assignment = EmployeeBusAssignment.objects.filter(employee=employee).first()
                    
                    if existing_assignment:
                        print("9. Updating existing assignment")
                        existing_assignment.bus = bus
                        existing_assignment.save()
                        messages.success(request, f'{employee.name} has been reassigned to {bus.bus_name}')
                    else:
                        print("10. Creating new assignment")
                        EmployeeBusAssignment.objects.create(
                            employee=employee,
                            bus=bus
                        )
                        messages.success(request, f'{employee.name} has been assigned to {bus.bus_name}')
                    
                    return redirect('busowner_dashboard')
                else:
                    print("11. Bus not found at all")
                    messages.error(request, 'Selected bus not found')
            
            except Exception as e:
                print("12. Error:", str(e))
                messages.error(request, f'Error assigning bus: {str(e)}')
        else:
            print("13. No bus_id in POST data")
            messages.error(request, 'Please select a bus')
    
    # For GET request or if POST fails
    buses = Bus.objects.all()
    print("14. Available buses for form:", [(b.bus_id, b.bus_name) for b in buses])
    context = {
        'employee': employee,
        'buses': buses,
    }
    return render(request, 'busowner/view_assign_employee.html', context)

#---------------------------------------------------------


#----------------------------------View for login redirect to Staff dashboard function-----------------------

def staff_dashboard(request):
    # Check if the user is logged in by verifying the session
    staff_id = request.session.get('staff_id')  # Retrieve the staff_id from the session

    if not staff_id:
        messages.error(request, 'You need to log in first.')
        return redirect('index')

    try:
        # Retrieve the staff object based on the staff_id in the session
        staff = Employee.objects.get(employee_id=staff_id, role=Employee.STAFF)
        staff_name = staff.name
        owner = staff.owner  # Fetch the owner associated with the employee
        
        # Debugging owner assignment
        print(f"Owner ID: {owner.owner_id if owner else 'No Owner Found'}")
    
    except Employee.DoesNotExist:
        messages.error(request, 'Invalid session. Please log in again.')
        return redirect('index')

    # Fetch total buses owned by the owner
    owner_bus_count = 0
    if owner:
        owner_bus_count = Bus.objects.filter(owner=owner).count()
        print(f"Total Buses Owned by {owner.name}: {owner_bus_count}")  # Debugging

    # Fetch counts relevant to the staff member
    assigned_bus_count = EmployeeBusAssignment.objects.filter(employee=staff).count()
    assigned_buses = Bus.objects.filter(employeebusassignment__employee=staff)
    
    # Fetch all routes and schedules for the owner instead of assigned buses
    route_count = Route.objects.filter(owner=owner).count()
    schedule_count = Schedule.objects.filter(owner=owner).count()
    
    booking_count = Booking.objects.count()
    passenger_count = Passenger.objects.count()
    
    # Search functionality
    search_results = {'passengers': [], 'employees': []}  # Default empty results
    query = request.POST.get('keywords', '').strip()
    
    if query:
        # Searching for passengers based on name, email, or phone number
        passengers = Passenger.objects.filter(
            Q(name__icontains=query) | Q(email__icontains=query) | Q(phone_number__icontains=query),
            
        ).distinct()
        
        # Searching for employees based on name, email, or phone number
        employees = Employee.objects.filter(
            Q(name__icontains=query) | Q(email__icontains=query) | Q(phone_number__icontains=query),
            
        ).distinct()
        
        search_results = {'passengers': passengers, 'employees': employees}
    attendance_records = Attendance.objects.filter(employee=staff).select_related('schedule').order_by('-date')

    # Group attendance data by month
    present_data = defaultdict(int)
    absent_data = defaultdict(int)

    for record in attendance_records:
        month = record.date.strftime("%b")  # Get month abbreviation
        if record.status == "Present":
            present_data[month] += 1
        elif record.status == "Absent":
            absent_data[month] += 1

    # Convert to JSON-friendly format
    present_data_json = json.dumps(present_data)
    absent_data_json = json.dumps(absent_data)

    # Calculate total stats
    total_days = attendance_records.count()
    present_days = sum(present_data.values())
    absent_days = sum(absent_data.values())
    attendance_percentage = round((present_days / total_days) * 100, 2) if total_days > 0 else 0

    context = {
        'staff_name': staff_name,
        'staff': staff,
        'assigned_bus_count': assigned_bus_count,
        'route_count': route_count,
        'booking_count': booking_count,
        'schedule_count': schedule_count,
        'passenger_count': passenger_count,
        'owner_bus_count': owner_bus_count,  # Pass total bus count of owner
        'search_results': search_results,
        'query': query,
        'assigned_buses': assigned_buses,  # Pass assigned buses to the template
        "attendance_records": attendance_records,
        "total_days": total_days,
        "present_days": present_days,
        "absent_days": absent_days,
        "attendance_percentage": attendance_percentage,
        "present_data": present_data_json,
        "absent_data": absent_data_json,
    }

    return render(request, 'employee/staff_dashboard.html', context)

#---------------------------------------------------------

def staff_assigned_buses_view(request):
    employee_id = request.session.get('staff_id')
    
    if not employee_id:
        messages.error(request, 'You need to log in first.')
        return redirect('index')

    try:
        employee = Employee.objects.get(employee_id=employee_id)
    except Employee.DoesNotExist:
        messages.error(request, 'Invalid session. Please log in again.')
        return redirect('index')

    # Get only unique buses assigned to the employee
    assigned_buses = Bus.objects.filter(
        employeebusassignment__employee=employee
    ).distinct()

    context = {
        'assigned_buses': assigned_buses,
        'employee': employee
    }

    return render(request, 'employee/staff_view_bus.html', context)


#---------------------------------------------------------

def staff_view_attendance(request):
    # Retrieve the logged-in employee's ID from the session
    employee_id = request.session.get('staff_id')
    
    if not employee_id:
        messages.error(request, 'You need to log in first.')
        return redirect('index')
    
    try:
        employee = Employee.objects.get(employee_id=employee_id)
    except Employee.DoesNotExist:
        messages.error(request, 'Invalid session. Please log in again.')
        return redirect('index')
    
    # Fetch attendance records for this employee
    attendance_records = Attendance.objects.filter(employee=employee)
    
    context = {
        'attendance_records': attendance_records
    }
    
    return render(request, 'employee/staff_view_attendance.html', context)

#---------------------------------------------------------

def staff_view_journey_dates(request):
    # Retrieve the logged-in employee's ID from the session
    employee_id = request.session.get('staff_id')
    
    if not employee_id:
        messages.error(request, 'You need to log in first.')
        return redirect('index')
    
    try:
        employee = Employee.objects.get(employee_id=employee_id)
    except Employee.DoesNotExist:
        messages.error(request, 'Invalid session. Please log in again.')
        return redirect('index')
    
    # Fetch all journey dates assigned to this staff member
    journey_dates = JourneyDate.objects.filter(employee=employee)
    
    context = {
        'journey_dates': journey_dates
    }
    
    return render(request, 'employee/staff_view_journey_details.html', context)

#---------------------------------------------------------

def staff_assigned_routes_view(request):
    employee_id = request.session.get('staff_id')
    
    if not employee_id:
        messages.error(request, 'You need to log in first.')
        return redirect('index')
    
    try:
        employee = Employee.objects.get(employee_id=employee_id)
    except Employee.DoesNotExist:
        messages.error(request, 'Invalid session. Please log in again.')
        return redirect('index')
    
    # Fetch bus IDs assigned to the employee
    bus_ids = EmployeeBusAssignment.objects.filter(employee=employee).values_list('bus_id', flat=True)
    
    # Fetch routes where bus_id is in the assigned buses
    routes = Route.objects.filter(bus_id__in=bus_ids)
    
    context = {
        'routes': routes
    }
    
    return render(request, 'employee/staff_view_routes.html', context)

#---------------------------------------------------------

def staff_assigned_schedules_view(request):
    # Get the logged-in staff ID from the session
    employee_id = request.session.get('staff_id')

    if not employee_id:
        messages.error(request, 'You need to log in first.')
        return redirect('index')

    try:
        employee = Employee.objects.get(employee_id=employee_id)
    except Employee.DoesNotExist:
        messages.error(request, 'Invalid session. Please log in again.')
        return redirect('index')

    # Fetch assignments where the employee is assigned
    assigned_schedules = EmployeeBusAssignment.objects.select_related('bus', 'schedule').filter(employee=employee)

    context = {
        'assigned_schedules': assigned_schedules
    }

    return render(request, 'employee/staff_view_schedules.html', context)

#---------------------------------------------------------
from django.utils.timezone import now
from datetime import timedelta

def staff_mark_attendance(request, employee_id):
    try:
        employee = Employee.objects.get(employee_id=employee_id)

        # Get all assigned schedules via EmployeeBusAssignment
        assigned_schedules = Schedule.objects.filter(bus__employeebusassignment__employee=employee).distinct()

        # Prepare attendance flags for each schedule and check if the schedule has passed
        attendance_status = {}
        for schedule in assigned_schedules:
            # Check if the attendance has already been marked for the current date
            marked = Attendance.objects.filter(
                employee=employee, schedule=schedule, date=now().date()
            ).exists()

            # Check if the schedule date has passed (compare only the date, not the time)
            schedule_date = schedule.departure_time.date()  # Get only the date part of departure_time
            schedule_is_past = schedule_date < now().date()

            attendance_status[schedule.schedule_id] = {
                'marked': marked,
                'is_past': schedule_is_past
            }

        if request.method == "POST":
            schedule_id = request.POST.get("schedule_id")
            if not schedule_id:
                messages.error(request, "Schedule ID not provided.")
                return redirect('staff_mark_attendance', employee_id=employee_id)

            # Retrieve the corresponding schedule
            try:
                schedule = Schedule.objects.get(schedule_id=schedule_id)
            except Schedule.DoesNotExist:
                messages.error(request, "Schedule not found.")
                return redirect('staff_mark_attendance', employee_id=employee_id)

            already_marked = attendance_status.get(schedule.schedule_id, {}).get('marked', False)
            schedule_is_past = attendance_status.get(schedule.schedule_id, {}).get('is_past', False)

            if already_marked:
                # Check if the attendance for the same schedule has already been marked for today
                messages.warning(request, "Attendance already marked for this schedule today. Please Contact Bus owner for any issues.")
            elif schedule_is_past:
                # Check if the schedule has already passed
                messages.warning(request, "Attendance cannot be marked for a passed schedule. Please Contact Bus owner for any issues.")
            else:
                # Create a new attendance record
                Attendance.objects.create(
                    employee=employee,
                    schedule=schedule,
                    date=now().date(),  # Record attendance for today's date
                    status="Present"
                )
                messages.success(request, f"Attendance marked for Schedule ID {schedule.schedule_id}.")
                # Refresh status after update
                return redirect('staff_mark_attendance', employee_id=employee_id)

        context = {
            'employee': employee,
            'assigned_schedules': assigned_schedules,
            'attendance_status': attendance_status
        }
        return render(request, 'employee/staff_mark_attendance.html', context)

    except Employee.DoesNotExist:
        messages.error(request, "Employee not found.")
        return redirect('index')
    except Schedule.DoesNotExist:
        messages.error(request, "Schedule not found.")
        return redirect('index')


#---------------------------------------------------------

def mark_trip_status(request, schedule_id):
    try:
        schedule = Schedule.objects.get(schedule_id=schedule_id)
    except Schedule.DoesNotExist:
        messages.error(request, "Schedule not found.")
        return redirect('staff_assigned_schedules')

    employee_id = request.session.get('staff_id')  # Fetch employee ID from session
    if not employee_id:
        messages.error(request, "Employee session not found. Please log in again.")
        return redirect('index')
    
    try:
        employee = Employee.objects.get(employee_id=employee_id)
    except Employee.DoesNotExist:
        messages.error(request, "Employee not found.")
        return redirect('index')

    if request.method == "POST":
        start_date = request.POST.get("start_date")
        start_time = request.POST.get("start_time")
        end_date = request.POST.get("end_date")
        end_time = request.POST.get("end_time")

        if not (start_date and start_time and end_date and end_time):
            messages.error(request, "All fields are required.")
            return redirect('staff_assigned_schedules', schedule_id=schedule_id)

        try:
            start_datetime = datetime.strptime(f"{start_date} {start_time}", "%Y-%m-%d %H:%M")
            end_datetime = datetime.strptime(f"{end_date} {end_time}", "%Y-%m-%d %H:%M")
        except ValueError:
            messages.error(request, "Invalid date/time format.")
            return redirect('staff_assigned_schedules', schedule_id=schedule_id)

        # Save the journey date with employee
        JourneyDate.objects.create(
            schedule=schedule,
            employee=employee,
            start_date=start_datetime,
            end_date=end_datetime,
        )

        messages.success(request, "Trip status marked successfully.")
        return redirect('staff_assigned_schedules')

    return render(request, 'employee/mark_trip_status.html', {'schedule': schedule})

#---------------------------------------------------------

def staff_travel_details_view(request):
    staff_id = request.session.get('staff_id')
    
    if not staff_id:
        messages.error(request, "You need to log in first.")
        return redirect('index')  # Make sure 'login' is correctly named in urls.py

    # Fetch staff details
    try:
        staff_member = Employee.objects.get(employee_id=staff_id)
    except Employee.DoesNotExist:
        return render(request, 'employee/travel_details.html', {'payee_list': []})  # No staff found

    # Fetch assigned bus
    assigned_bus = EmployeeBusAssignment.objects.filter(employee=staff_member).first()

    if not assigned_bus:
        return render(request, 'employee/travel_details.html', {'payee_list': []})  # No assigned bus

    # Fetch Payee Details where passengers travel in assigned bus
    payee_list = PayeeDetails.objects.filter(passengertraveldetails__bus=assigned_bus.bus).distinct()

    return render(request, 'employee/travel_details.html', {'payee_list': payee_list})


#---------------------------------------------------------

def staff_journey_form(request):
    employee_id = request.session.get('staff_id')

    if not employee_id:
        messages.error(request, "Employee session not found. Please log in again.")
        return redirect('index')

    try:
        employee = Employee.objects.get(employee_id=employee_id)
        schedule = Schedule.objects.filter(bus__employeebusassignment__employee=employee).first()
    except Employee.DoesNotExist:
        messages.error(request, "Employee not found.")
        return redirect('index')

    context = {
        'employee': employee,
        'schedule': schedule
    }

    return render(request, 'employee/staff_mark_attendance.html', context)

#---------------------------------------------------------

def staff_view_passenger(request):
    passengers = Passenger.objects.all()
    return render(request, 'employee/staff_view_passengers.html', {'passengers': passengers})

#---------------------------------------------------------

def staff_view_bookings(request):
    # Fetch all bookings
    staff_id = request.session.get('staff_id')

    if not staff_id:
        messages.error(request, 'You need to log in first.')
        return redirect('index')

    try:
        employee = Employee.objects.get(employee_id=staff_id, role=Employee.STAFF)
        owner = employee.owner  # this is the key part
        print("Logged-in staff:", employee.name)
        print("Owner ID:", owner.owner_id if owner else "No owner found")
    except Employee.DoesNotExist:
        messages.error(request, 'Invalid session. Please log in again.')
        return redirect('index')

    # Now filter bookings where the schedule is owned by this owner
    bookings = Booking.objects.filter(schedule__owner=owner).select_related('passenger', 'schedule')

    print("Bookings found:", bookings.count())

    context = {
        'bookings': bookings
    }

    # Render the bookings to the template
    return render(request, 'employee/staff_view_bookings.html', {'bookings': bookings})

#---------------------------------------------------------

def staff_view_payments(request):
    staff_id = request.session.get('staff_id')

    if not staff_id:
        messages.error(request, 'You need to log in first.')
        return redirect('index')

    try:
        employee = Employee.objects.get(employee_id=staff_id, role=Employee.STAFF)
        owner = employee.owner
        print(f"Staff: {employee.name}, Owner ID: {owner.owner_id}")
    except Employee.DoesNotExist:
        messages.error(request, 'Invalid session. Please log in again.')
        return redirect('index')

    # Filter payments where the booking is associated with a schedule belonging to the owner
    payments = Payment.objects.filter(
        booking__schedule__owner=owner
    ).select_related('booking', 'passenger')

    print("Payments found:", payments.count())

    return render(request, 'employee/staff_view_payment.html', {'payments': payments})


#---------------------------------------------------------

def staff_view_cancellations(request):
    staff_id = request.session.get('staff_id')

    if not staff_id:
        messages.error(request, 'You need to log in first.')
        return redirect('index')

    try:
        staff = Employee.objects.get(employee_id=staff_id, role=Employee.STAFF)
        owner = staff.owner
        print(f"Staff: {staff.name}, Owner: {owner.owner_id}")
    except Employee.DoesNotExist:
        messages.error(request, 'Invalid session. Please log in again.')
        return redirect('index')

    # Filter cancellations by owner's bookings
    cancellations = Cancellation.objects.filter(
        booking__schedule__owner=owner
    ).select_related('booking', 'passenger')

    return render(request, 'employee/staff_view_cancel.html', {
        'cancellations': cancellations
    })

#---------------------------------------------------------

def staff_profile(request):
    staff_id = request.session.get('staff_id')  # Use session to store staff ID

    if not staff_id:
        messages.error(request, "You need to log in first.")
        return redirect('index')

    try:
        staff = Employee.objects.get(employee_id=staff_id, role='Staff')
    except Employee.DoesNotExist:
        messages.error(request, "Staff profile not found.")
        return redirect('index')

    if request.method == 'POST':
        email = request.POST.get('email')
        phone_number = request.POST.get('phone_number')
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        # Check if the email is already used by another user
        if Employee.objects.filter(email=email).exclude(employee_id=staff_id).exists():
            messages.error(request, "This email is already in use.")
            return redirect('staff_profile')

        # Check if the phone number is already used by another user
        if Employee.objects.filter(phone_number=phone_number).exclude(employee_id=staff_id).exists():
            messages.error(request, "This phone number is already in use.")
            return redirect('staff_profile')

        # Check if old password is correct
        if staff.password != old_password:
            messages.error(request, "Old password is incorrect.")
            return redirect('staff_profile')

        # Ensure new password and confirm password match
        if new_password and new_password != confirm_password:
            messages.error(request, "New password and confirm password do not match.")
            return redirect('staff_profile')

        # Update staff details
        staff.email = email
        staff.phone_number = phone_number

        if new_password:
            staff.password = new_password  # Hashing is recommended

        try:
            staff.save()
            messages.success(request, "Staff profile updated successfully!")
        except IntegrityError:
            messages.error(request, "An error occurred while updating the profile.")

        return redirect('staff_profile')

    return render(request, 'employee/staff_profile.html', {'staff': staff})


#---------------------------------------------------------

#----------------------------------View for login redirect to driver dashboard function-----------------------

def driver_dashboard(request):
    # Check if the user is logged in by verifying the session
    driver_id = request.session.get('driver_id')  # Retrieve the driver_id from the session

    if not driver_id:
        messages.error(request, 'You need to log in first.')
        return redirect('index')

    try:
        # Retrieve the driver object based on the driver_id in the session
        driver = Employee.objects.get(employee_id=driver_id, role=Employee.DRIVER)
        driver_name = driver.name
        owner = driver.owner  # Fetch the owner associated with the driver
        
        # Debugging owner assignment
        print(f"Owner ID: {owner.owner_id if owner else 'No Owner Found'}")
    
    except Employee.DoesNotExist:
        messages.error(request, 'Invalid session. Please log in again.')
        return redirect('index')

    # Fetch total buses owned by the owner
    owner_bus_count = 0
    if owner:
        owner_bus_count = Bus.objects.filter(owner=owner).count()
        print(f"Total Buses Owned by {owner.name}: {owner_bus_count}")  # Debugging

    # Fetch counts relevant to the driver member
    assigned_bus_count = EmployeeBusAssignment.objects.filter(employee=driver).count()
    assigned_buses = Bus.objects.filter(employeebusassignment__employee=driver)
    
    # Fetch all routes and schedules for the owner instead of assigned buses
    route_count = Route.objects.filter(owner=owner).count()
    schedule_count = Schedule.objects.filter(owner=owner).count()
    
    booking_count = Booking.objects.count()
    passenger_count = Passenger.objects.count()
    
    
    # Search functionality
    search_results = {'passengers': [], 'employees': []}  # Default empty results
    query = request.POST.get('keywords', '').strip()
    
    if query:
        # Searching for passengers based on name, email, or phone number
        passengers = Passenger.objects.filter(
            Q(name__icontains=query) | Q(email__icontains=query) | Q(phone_number__icontains=query),
            
        ).distinct()
        
        
        search_results = {'passengers': passengers}

    attendance_records = Attendance.objects.filter(employee=driver).select_related('schedule').order_by('-date')

    # Group attendance data by month
    present_data = defaultdict(int)
    absent_data = defaultdict(int)

    for record in attendance_records:
        month = record.date.strftime("%b")  # Get month abbreviation
        if record.status == "Present":
            present_data[month] += 1
        elif record.status == "Absent":
            absent_data[month] += 1

    # Convert to JSON-friendly format
    present_data_json = json.dumps(present_data)
    absent_data_json = json.dumps(absent_data)

    # Calculate total stats
    total_days = attendance_records.count()
    present_days = sum(present_data.values())
    absent_days = sum(absent_data.values())
    attendance_percentage = round((present_days / total_days) * 100, 2) if total_days > 0 else 0

    context = {
        'driver_name': driver_name,
        'driver': driver,
        'assigned_bus_count': assigned_bus_count,
        'route_count': route_count,
        'booking_count': booking_count,
        'schedule_count': schedule_count,
        'passenger_count': passenger_count,
        'owner_bus_count': owner_bus_count,  # Pass total bus count of owner
        'search_results': search_results,
        'query': query,
        'assigned_buses': assigned_buses,  # Pass assigned buses to the template
        "attendance_records": attendance_records,
        "total_days": total_days,
        "present_days": present_days,
        "absent_days": absent_days,
        "attendance_percentage": attendance_percentage,
        "present_data": present_data_json,
        "absent_data": absent_data_json,
    }

    return render(request, 'employee/driver_dashboard.html', context)

#---------------------------------------------------------
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import Employee
from django.db import IntegrityError

from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import IntegrityError
from .models import Employee

def driver_profile(request):
    driver_id = request.session.get('driver_id')

    if not driver_id:
        messages.error(request, "You need to log in first.")
        return redirect('index')

    try:
        driver = Employee.objects.get(employee_id=driver_id, role=Employee.DRIVER)
    except Employee.DoesNotExist:
        messages.error(request, "Driver profile not found.")
        return redirect('index')

    if request.method == 'POST':
        email = request.POST.get('email')
        phone_number = request.POST.get('phone_number')
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        # Check if the email is already used by another user
        if Employee.objects.filter(email=email).exclude(employee_id=driver_id).exists():
            messages.error(request, "This email is already in use.")
            return redirect('driver_profile')

        # Check if the phone number is already used by another user
        if Employee.objects.filter(phone_number=phone_number).exclude(employee_id=driver_id).exists():
            messages.error(request, "This phone number is already in use.")
            return redirect('driver_profile')

        # Check if old password is correct
        if driver.password != old_password:
            messages.error(request, "Old password is incorrect.")
            return redirect('driver_profile')

        # Ensure new password and confirm password match
        if new_password and new_password != confirm_password:
            messages.error(request, "New password and confirm password do not match.")
            return redirect('driver_profile')

        # Update driver details
        driver.email = email
        driver.phone_number = phone_number

        if new_password:
            driver.password = new_password  # Hashing is recommended

        try:
            driver.save()
            messages.success(request, "Driver profile updated successfully!")
        except IntegrityError:
            messages.error(request, "An error occurred while updating the profile.")

        return redirect('driver_profile')

    return render(request, 'employee/driver/driver_profile.html', {'driver': driver})



#---------------------------------------------------------

def driver_view_passenger(request):
    passengers = Passenger.objects.all()
    return render(request, 'employee/driver/driver_view_passengers.html', {'passengers': passengers})

#---------------------------------------------------------

def driver_view_bookings(request):
    driver_id = request.session.get('driver_id')
    # Fetch all bookings
    if not driver_id:
        messages.error(request, 'You need to log in first.')
        return redirect('index')

    try:
        employee = Employee.objects.get(employee_id=driver_id, role=Employee.DRIVER)
        owner = employee.owner  # this is the key part
        print("Logged-in Driver:", employee.name)
        print("Owner ID:", owner.owner_id if owner else "No owner found")
    except Employee.DoesNotExist:
        messages.error(request, 'Invalid session. Please log in again.')
        return redirect('index')

    # Now filter bookings where the schedule is owned by this owner
    bookings = Booking.objects.filter(schedule__owner=owner).select_related('passenger', 'schedule')

    print("Bookings found:", bookings.count())

    context = {
        'bookings': bookings
    }

    return render(request, 'employee/driver/driver_view_bookings.html', {'bookings': bookings})

#---------------------------------------------------------

def driver_view_payments(request):
    driver_id = request.session.get('driver_id')

    if not driver_id:
        messages.error(request, 'You need to log in first.')
        return redirect('index')

    try:
        employee = Employee.objects.get(employee_id=driver_id, role=Employee.DRIVER)
        owner = employee.owner  # this is the key part
        print("Logged-in Driver:", employee.name)
        print("Owner ID:", owner.owner_id if owner else "No owner found")
    except Employee.DoesNotExist:
        messages.error(request, 'Invalid session. Please log in again.')
        return redirect('index')

    # Filter payments where the booking is associated with a schedule belonging to the owner
    payments = Payment.objects.filter(
        booking__schedule__owner=owner
    ).select_related('booking', 'passenger')

    print("Payments found:", payments.count())

    return render(request, 'employee/driver/driver_view_payment.html', {'payments': payments})

#---------------------------------------------------------

def driver_view_cancellations(request):
    driver_id = request.session.get('driver_id')

    if not driver_id:
        messages.error(request, 'You need to log in first.')
        return redirect('index')

    try:
        employee = Employee.objects.get(employee_id=driver_id, role=Employee.DRIVER)
        owner = employee.owner  # this is the key part
        print("Logged-in Driver:", employee.name)
        print("Owner ID:", owner.owner_id if owner else "No owner found")
    except Employee.DoesNotExist:
        messages.error(request, 'Invalid session. Please log in again.')
        return redirect('index')
    
    # Fetch all cancellations
    cancellations = Cancellation.objects.filter(
        booking__schedule__owner=owner
    ).select_related('booking', 'passenger')

    # Render the cancellations to the template
    return render(request, 'employee/driver/driver_view_cancel.html', {'cancellations': cancellations})

#---------------------------------------------------------

def driver_assigned_buses_view(request):
    # Retrieve the logged-in driver's ID from the session
    driver_id = request.session.get('driver_id')
    
    if not driver_id:
        messages.error(request, 'You need to log in first.')
        return redirect('index')
    
    try:
        driver = Employee.objects.get(employee_id=driver_id)
    except Employee.DoesNotExist:
        messages.error(request, 'Invalid session. Please log in again.')
        return redirect('index')
    
    # Fetch only the buses assigned to the logged-in driver
    assigned_buses = EmployeeBusAssignment.objects.select_related('bus').filter(employee=driver)

    context = {
        'assigned_buses': assigned_buses,
        'employee': driver  # Pass employee details
    }
    
    return render(request, 'employee/driver/driver_view_bus.html', context)

#---------------------------------------------------------

def driver_assigned_schedules_view(request):
    # Get the logged-in driver ID from the session
    driver_id = request.session.get('driver_id')

    if not driver_id:
        messages.error(request, 'You need to log in first.')
        return redirect('index')

    try:
        driver = Employee.objects.get(employee_id=driver_id, role=Employee.DRIVER)
    except Employee.DoesNotExist:
        messages.error(request, 'Invalid session. Please log in again.')
        return redirect('index')

    # Fetch assignments where the driver is assigned
    assigned_schedules = EmployeeBusAssignment.objects.select_related('bus', 'schedule').filter(employee=driver)

    context = {
        'assigned_schedules': assigned_schedules
    }

    return render(request, 'employee/driver/driver_view_schedules.html', context)


#---------------------------------------------------------

def driver_assigned_routes_view(request):
    driver_id = request.session.get('driver_id')
    
    if not driver_id:
        messages.error(request, 'You need to log in first.')
        return redirect('index')
    
    try:
        driver = Employee.objects.get(employee_id=driver_id, role=Employee.DRIVER)
    except Employee.DoesNotExist:
        messages.error(request, 'Invalid session. Please log in again.')
        return redirect('index')
    
    # Fetch bus IDs assigned to the driver
    bus_ids = EmployeeBusAssignment.objects.filter(employee=driver).values_list('bus_id', flat=True)
    
    # Fetch routes where bus_id is in the assigned buses
    routes = Route.objects.filter(bus_id__in=bus_ids)
    
    context = {
        'routes': routes
    }
    
    return render(request, 'employee/driver/driver_view_routes.html', context)

#---------------------------------------------------------
from django.utils.timezone import now
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Employee, Schedule, Attendance

def driver_mark_attendance(request, employee_id):
    try:
        driver = Employee.objects.get(employee_id=employee_id, role=Employee.DRIVER)

        # Get all schedules assigned to this driver
        schedules = Schedule.objects.filter(bus__employeebusassignment__employee=driver).distinct()

        # Get all attendance records for today
        attendance_status = Attendance.objects.filter(
            employee=driver,
            date=now().date()
        ).values_list('schedule_id', flat=True)

        if request.method == "POST":
            schedule_id = request.POST.get("schedule_id")
            if not schedule_id:
                messages.error(request, "Schedule ID not provided.")
                return redirect('driver_mark_attendance', employee_id=employee_id)

            schedule = Schedule.objects.get(schedule_id=schedule_id)

            if int(schedule_id) in attendance_status:
                messages.warning(request, "Attendance already marked for this schedule.")
            else:
                Attendance.objects.create(
                    employee=driver,
                    schedule=schedule,
                    date=now().date(),
                    status="Present"
                )
                messages.success(request, f"Attendance marked for schedule {schedule_id}.")

            return redirect('driver_mark_attendance', employee_id=employee_id)

        context = {
            'driver': driver,
            'assigned_schedules': schedules,
            'attendance_status': attendance_status,
        }
        return render(request, 'employee/driver/driver_mark_attendance.html', context)

    except Employee.DoesNotExist:
        messages.error(request, "Driver not found.")
        return redirect('index')


#---------------------------------------------------------

def driver_view_attendance(request):
    # Retrieve the logged-in driver's ID from the session
    driver_id = request.session.get('driver_id')
    
    if not driver_id:
        messages.error(request, 'You need to log in first.')
        return redirect('index')
    
    try:
        driver = Employee.objects.get(employee_id=driver_id, role=Employee.DRIVER)
    except Employee.DoesNotExist:
        messages.error(request, 'Invalid session. Please log in again.')
        return redirect('index')
    
    # Fetch attendance records for this driver
    attendance_records = Attendance.objects.filter(employee=driver)
    
    context = {
        'attendance_records': attendance_records
    }
    
    return render(request, 'employee/driver/driver_view_attendance.html', context)

#---------------------------------------------------------

#----------------------------------this will register a new passenger----------------------------------------

def passenger_register(request):
    if request.method == 'POST':
        # Retrieve form data
        name = request.POST.get('name')
        email = request.POST.get('Email')
        password = request.POST.get('password')
        phone_number = request.POST.get('phoneNumber')

        # Check if email already exists
        if Passenger.objects.filter(email=email).exists():
            messages.error(request, 'Email is already registered!')
            return render(request, 'passenger/passenger_register.html')

        # Check if username (name) already exists
        if Passenger.objects.filter(name=name).exists():
            messages.error(request, 'Username is already taken!')
            return render(request, 'passenger/passenger_register.html')
        
        if Passenger.objects.filter(phone_number=phone_number).exists():
            messages.error(request, 'Phone number is already registered!')
            return render(request, 'passenger/passenger_register.html')

        # If no conflict, create the new passenger
        Passenger.objects.create(
            name=name,
            email=email,
            password=password,  # Save the password as plain text (not recommended for production)
            phone_number=phone_number
        )
        
        # Add a success message to indicate registration was successful
        messages.success(request, 'Registration successful!')

        # Redirect to the index page after successful registration
        return redirect('index')  # Replace 'index' with your homepage URL

    return render(request, 'passenger/passenger_register.html')

#------------------------------------------------------------------------------------------------------------

#----------------------------------View for login redirect to passenger dashboard function-------------------

def passenger_dashboard(request):
    # Check if the user is logged in by verifying the session
    passenger_id = request.session.get('passenger_id')

    if not passenger_id:
        messages.error(request, 'You need to log in first.')
        return redirect('index')  # Redirect to the login page

    try:
        # Retrieve the Passenger object based on the passenger_id in the session
        passenger = Passenger.objects.get(passenger_id=passenger_id)
    except Passenger.DoesNotExist:
        messages.error(request, 'Invalid session. Please log in again.')
        return redirect('index')  # Redirect to the login page

    # Fetch counts
    booking_count = Booking.objects.count()
    schedule_count = Schedule.objects.count()
    bus_count = Bus.objects.count()
    route_count = Route.objects.count()
    sources = Route.objects.values('source').distinct()
    destinations = Route.objects.values('destination').distinct()

    # Pass the counts and passenger data to the template
    context = {
        'passenger': passenger,
        'booking_count': booking_count,
        'schedule_count': schedule_count,
        'bus_count': bus_count,
        'route_count': route_count,
        'sources': sources,
        'destinations': destinations,
    }

    return render(request, 'passenger/passenger_dashboard.html', context)


#------------------------------------------------------------------------------------------------------------

#-----------------------------------------Passenger Page Views-----------------------------------------------

def passenger_about(request):
    
    booking_count = Booking.objects.count()
    schedule_count = Schedule.objects.count()
    bus_count = Bus.objects.count()
    route_count = Route.objects.count()

    # Pass the counts and passenger data to the template
    context = {
        'booking_count': booking_count,
        'schedule_count': schedule_count,
        'bus_count': bus_count,
        'route_count': route_count,
    }
    return render(request, 'passenger/additional/about.html', context) 

#---------------------------------------------------------

def logout_and_redirect(request):
    # Clear the session
    request.session.flush()  # This clears all session data

    # Optionally, display a message for the user
    messages.success(request, 'You have been logged out.')
    return redirect('passenger_register') 

#---------------------------------------------------------

def passenger_offers(request):
    
    return render(request, 'passenger/additional/offers.html')

#---------------------------------------------------------

def passenger_blog(request):
    
    return render(request, 'passenger/additional/blog.html')

#---------------------------------------------------------

def passenger_contact(request):
    
    return render(request, 'passenger/additional/contact.html')

#---------------------------------------------------------

def passenger_view_bus(request):
    # Optional: Check if the passenger is logged in
    passenger_id = request.session.get('passenger_id')
    
    if not passenger_id:
        messages.error(request, 'You need to log in as a passenger to view this page.')
        return redirect('index')  # Redirect to login page or dashboard
    
    # Get all buses available
    buses = Bus.objects.all()  # Fetch all buses without any filters
    
    # Pass the buses to the template
    return render(request, 'passenger/view_bus.html', {'buses': buses})

#---------------------------------------------------------

def passenger_view_route(request):
    # Optional: Check if the passenger is logged in
    passenger_id = request.session.get('passenger_id')
    
    if not passenger_id:
        messages.error(request, 'You need to log in as a passenger to view this page.')
        return redirect('index')  # Redirect to login page or dashboard
    
    # Get all routes  available
    routes = Route.objects.all()# Fetch all routes  without any filters

    # Pass the buses to the template
    return render(request, 'passenger/view_route.html', {'routes': routes})

#---------------------------------------------------------

def passenger_view_cancel(request):
    # Check if the passenger is logged in
    passenger_id = request.session.get('passenger_id')
    
    if not passenger_id:
        messages.error(request, 'You need to log in as a passenger to view this page.')
        return redirect('index')  # Redirect to login page or dashboard
    
    # Get cancellations of that user along with seat number
    cancellations = Cancellation.objects.filter(passenger_id=passenger_id).select_related('booking')
    
    return render(request, 'passenger/view_cancel.html', {'cancellations': cancellations})

#---------------------------------------------------------

from django.http import JsonResponse
from django.utils.timezone import now
from django.contrib import messages
from django.shortcuts import redirect
from .models import Booking, Cancellation, SnackOrder

def cancel_booking(request, booking_id):
    passenger_id = request.session.get('passenger_id')
    
    if not passenger_id:
        return JsonResponse({'success': False, 'error': 'You need to log in as a passenger to cancel bookings.'})

    try:
        # Retrieve the booking instance
        booking = Booking.objects.get(booking_id=booking_id, passenger_id=passenger_id)

        # Check if booking has a valid schedule and departure time
        if not booking.schedule or not booking.schedule.departure_time:
            return JsonResponse({'success': False, 'error': 'Invalid booking schedule. Please contact support.'})

        # Get current time and departure time
        current_time = now()
        departure_time = booking.schedule.departure_time

        # Calculate time difference in hours
        time_difference = (departure_time - current_time).total_seconds() / 3600  # Convert to hours

        # Debugging print statements
        print(f"\nDEBUG INFO: Booking ID {booking_id}")
        print(f"Current Time: {current_time}")
        print(f"Departure Time: {departure_time}")
        print(f"Time Before Departure: {time_difference:.2f} hours")

        # Apply cancellation policy
        if time_difference >= 72:
            refund_percentage = 100
            cancellation_fee = 0
        elif 48 <= time_difference < 72:
            refund_percentage = 90
            cancellation_fee = 10
        elif 24 <= time_difference < 48:
            refund_percentage = 80
            cancellation_fee = 20
        elif 12 <= time_difference < 24:
            refund_percentage = 70
            cancellation_fee = 30
        elif 2 <= time_difference < 12:
            refund_percentage = 60
            cancellation_fee = 40
        else:
            refund_percentage = 50
            cancellation_fee = 50

        print(f"DEBUG: Refund Percentage = {refund_percentage}%, Cancellation Fee = {cancellation_fee}")

        # Store cancellation details
        Cancellation.objects.create(
            passenger=booking.passenger,
            booking=booking,
            booking_id_value=booking.booking_id,
            schedule=str(booking.schedule),
            status=Booking.Status.CANCELLED,
            cancellation_date=current_time
        )

        # Update booking status
        booking.status = Booking.Status.CANCELLED
        booking.save()

        # Cancel all snack orders related to this booking
        snack_orders = SnackOrder.objects.filter(booking=booking)
        if snack_orders.exists():
            snack_orders.update(status=SnackOrder.CANCELLED)
            print(f"DEBUG: Cancelled {snack_orders.count()} snack orders for Booking ID {booking_id}")

        # Construct a detailed message for alert
        alert_message = (
            f"🚨 Booking & Snack Cancellation Alert 🚨\n"
            f"Booking ID: {booking_id}\n"
            f"Current Time: {current_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"Departure Time: {departure_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"Time Before Departure: {time_difference:.2f} hours\n"
            f"Refund Policy:\n"
            f"  - More than 72 hrs: 100% refund\n"
            f"  - 48-72 hrs: 90% refund\n"
            f"  - 24-48 hrs: 80% refund\n"
            f"  - 12-24 hrs: 70% refund\n"
            f"  - 2-12 hrs: 60% refund\n"
            f"  - Less than 2 hrs: 50% refund\n\n"
            f"Refund Percentage: {refund_percentage}%\n"
            f"Cancellation Fee: ₹{cancellation_fee}\n"
            f"Status: Booking & Snack Orders Cancelled"
        )

        return JsonResponse({
            'success': True,
            'message': alert_message,
            'redirect': '/passenger-dashboard/'
        })

    except Booking.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Booking not found or does not belong to you.'})

    except Exception as e:
        print(f"Error in cancel_booking: {e}")  # Log error to server
        return JsonResponse({'success': False, 'error': f'Unexpected error: {str(e)}'})



#---------------------------------------------------------

def passenger_view_schedule(request):
    # Optional: Check if the passenger is logged in
    passenger_id = request.session.get('passenger_id')
    
    if not passenger_id:
        messages.error(request, 'You need to log in as a passenger to view this page.')
        return redirect('index')  # Redirect to login page or dashboard
    
    # Get Cancellations of that user available
    schedule = Schedule.objects.all()
    
    # Pass the buses to the template
    return render(request, 'passenger/view_schedule.html', {'schedule': schedule})

#---------------------------------------------------------

def passenger_view_booking(request):
    # Get the logged-in passenger ID from the session
    passenger_id = request.session.get('passenger_id')

    if not passenger_id:
        messages.error(request, "You need to log in as a passenger to view your bookings.")
        return redirect('index')  # Redirect to login page if not logged in

    # Fetch only the bookings made by the logged-in passenger
    bookings = Booking.objects.filter(passenger_id=passenger_id).select_related('schedule__route')

    # Fetch payments related to those bookings
    payments = Payment.objects.filter(booking__in=bookings).select_related('booking')

    # Import datetime for comparison
    from django.utils import timezone
    current_datetime = timezone.now()
    today = now().date() 
    # Prepare the data for the template
    booking_data = []
    for booking in bookings:
        payment = payments.filter(booking=booking).first()  # Get payment if available
        
        
        # Default values in case schedule is None
        departure_time = None
        is_departure_passed = False
        source = "Unknown"
        destination = "Unknown"
        
        # Check if schedule exists before accessing its attributes
        if booking.schedule:
            departure_time = booking.schedule.departure_time
            
            # Check if departure time is in the past
            if departure_time and current_datetime > departure_time:
                is_departure_passed = True
                
            # Get route information if available
            if booking.schedule.route:
                source = booking.schedule.route.source
                destination = booking.schedule.route.destination
            
        booking_data.append({
            'booking_id': booking.booking_id,
            'payment_date': payment.payment_date if payment else "N/A",
            'amount': payment.amount if payment else "N/A",
            'payment_method': payment.payment_method if payment else "N/A",
            'seat_number': booking.seat_number,
            'status': booking.get_status_display(),
            'source': source,
            'destination': destination,
            'departure_time': departure_time,
            'is_departure_passed': is_departure_passed
        })

    # Render the template with filtered booking data
    return render(request, 'passenger/view_booking.html', {'booking_data': booking_data, 'today': today})

#---------------------------------------------------------

def booking_details_view(request, booking_id):
    try:
        # Retrieve the booking
        booking = Booking.objects.get(booking_id=booking_id)
    except Booking.DoesNotExist:
        messages.error(request, "Booking not found.")
        return redirect('passenger_view_booking')  # Redirect back to the bookings page

    # Retrieve related Payee Details
    payee_details = PayeeDetails.objects.filter(booking=booking).first()

    # Retrieve related Passenger Travel Details
    travel_details = PassengerTravelDetails.objects.filter(booking=booking)

    # Retrieve related Snack Orders
    snack_orders = SnackOrder.objects.filter(booking=booking)

    context = {
        'booking': booking,
        'payee_details': payee_details,
        'travel_details': travel_details,
        'snack_orders': snack_orders,  # Pass snack orders to the template
    }

    return render(request, 'passenger/booking_details.html', context)

#---------------------------------------------------------

def passenger_view_schedules(request):
        # Optional: Check if the passenger is logged in
    passenger_id = request.session.get('passenger_id')
    
    if not passenger_id:
        messages.error(request, 'You need to log in as a passenger to view this page.')
        return redirect('index')  # Redirect to login page or dashboard
    
    schedules = Schedule.objects.all()
    print("Schedules:", schedules)  # Debugging step
    return render(request, 'passenger/view_schedule.html', {'schedules': schedules})

#---------------------------------------------------------

from datetime import date
from django.utils.dateparse import parse_date
from django.contrib import messages
from django.shortcuts import render, redirect
from .models import Schedule
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils.dateparse import parse_date
from datetime import date
from .models import Schedule, Route
from decimal import Decimal
import difflib

def get_best_match(user_input, options):
    """Fuzzy match the user input to available options."""
    matches = difflib.get_close_matches(user_input.lower(), [opt.lower() for opt in options], n=1, cutoff=0.5)
    if matches:
        return matches[0]
    return user_input  # If no close match found, fallback to original input

#---------------------------------------------------------

def search_buses(request):
    passenger_id = request.session.get('passenger_id')

    if request.method == "GET":
        source = request.GET.get("origin", "").strip()
        destination = request.GET.get("destination", "").strip()
        travel_date = request.GET.get("travel_date")

        if not passenger_id:
            messages.error(request, 'You need to log in as a passenger to view this page.')
            return redirect('index')

        if not travel_date:
            messages.error(request, "Please provide a valid travel date.")
            return redirect('search_buses')

        travel_date_obj = parse_date(travel_date)
        current_date = date.today()

        if travel_date_obj < current_date:
            return render(request, 'passenger/search_results.html', {'schedules': []})

        # Fetch all city names from Route table
        all_sources = Route.objects.values_list('source', flat=True)
        all_destinations = Route.objects.values_list('destination', flat=True)

        # Correct the user-typed input
        corrected_source = get_best_match(source, all_sources)
        corrected_destination = get_best_match(destination, all_destinations)

        print(f"Corrected Source: {corrected_source}")
        print(f"Corrected Destination: {corrected_destination}")

        # Now query with corrected source and destination
        schedules = Schedule.objects.filter(
            route__source__iexact=corrected_source,
            route__destination__iexact=corrected_destination,
            departure_time__date=travel_date_obj,
            bus__status__iexact="active"  # Only include active buses
        ).select_related('bus', 'route')

        if not schedules:
            messages.warning(request, "No buses found for the selected criteria.")

        bus_images = {}
        for schedule in schedules:
            bus_images[schedule.bus.bus_id] = BusImage.objects.filter(bus=schedule.bus)


        for schedule in schedules:
            distance = Decimal(schedule.route.distance)
            fare_rate = Decimal(schedule.bus.fare_rate)
            base_fare = Decimal(schedule.bus.base_fare)
            total_fare = base_fare + (fare_rate * distance)
            schedule.total_fare = total_fare

            arrival = schedule.arrival_time
            departure = schedule.departure_time
            if arrival < departure:
                duration_seconds = (arrival - departure).total_seconds() + (24 * 3600)
            else:
                duration_seconds = (arrival - departure).total_seconds()

            hours = int(duration_seconds // 3600)
            minutes = int((duration_seconds % 3600) // 60)
            schedule.duration = f"{hours}h {minutes}m"
        
    return render(request, 'passenger/search_results.html', {
        'schedules': schedules,
        'bus_images': bus_images,
})
    
#---------------------------------------------------------

def view_bus_images(request, schedule_id):
    # Filter schedule by ID
    schedules = Schedule.objects.filter(schedule_id=schedule_id)

    if not schedules.exists():
        return redirect('search_buses')  # Or show a custom error page

    schedule = schedules.first()  # Safe because we checked above
    bus = schedule.bus

    # Get images related to this bus
    images = BusImage.objects.filter(bus=bus)

    return render(request, 'passenger/view_bus_images.html', {
        'schedule': schedule,
        'images': images
    })
    
#---------------------------------------------------------

from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Bus, Schedule, Booking

def select_seats(request, schedule_id, bus_id):
    passenger_id = request.session.get('passenger_id')
    

    try:
        schedule = Schedule.objects.get(schedule_id=schedule_id)
        bus = Bus.objects.get(bus_id=bus_id)
    except (Schedule.DoesNotExist, Bus.DoesNotExist):
        messages.error(request, "Invalid bus or schedule.")
        return redirect('home')

    # Fetch booked seats from all bookings excluding cancelled ones
    booked_seats = Booking.objects.filter(schedule=schedule).exclude(status=Booking.Status.CANCELLED).values_list('seat_number', flat=True)

    # Convert booked seats into a set of integers
    booked_seat_numbers = set()
    for seat in booked_seats:
        if seat:  # Ensure seat_number is not empty
            booked_seat_numbers.update(map(int, seat.split(',')))  # Split multiple seats and convert to int

    booked_seats = booked_seat_numbers  # Now a proper set of integers

    columns = 5  # Number of seats per row
    rows = (bus.capacity + columns - 1) // columns  # Calculate total rows

    # Generate seat matrix
    seat_matrix = []
    seat_number = 1
    for _ in range(rows):
        row_seats = []
        for _ in range(columns):
            if seat_number <= bus.capacity:
                row_seats.append(seat_number)
                seat_number += 1
            else:
                row_seats.append(None)  # Empty seat
        seat_matrix.append(row_seats)

    if request.method == 'POST':
        selected_seats = request.POST.get('selected_seats', '').split(',')

        try:
            selected_seats = [int(seat) for seat in selected_seats if seat.strip()]
        except ValueError:
            messages.error(request, "Invalid seat numbers.")
            return redirect('select_seats', schedule_id=schedule_id, bus_id=bus_id)

        if not selected_seats:
            messages.error(request, "Please select at least one seat.")
            return redirect('select_seats', schedule_id=schedule_id, bus_id=bus_id)

        # Store selected seats in session
        request.session['selected_seats'] = selected_seats
        request.session['schedule_id'] = schedule_id
        request.session['bus_id'] = bus_id

        # Redirect to the payment page
        return redirect('payment')

    return render(request, 'passenger/select_seats.html', {
        'bus': bus,
        'schedule': schedule,
        'booked_seats': booked_seats,
        'seat_matrix': seat_matrix
    })

    
#---------------------------------------------------------

def payment_success(request):
    print("Session at payment_success:", request.session.items())  # Debugging

    passenger_id = request.session.get('passenger_id')
    if not passenger_id:
        messages.error(request, 'Session expired. Please log in again.')
        return redirect('index')  # Redirect to login page

    request.session['passenger_id'] = passenger_id
    request.session.modified = True  

    messages.success(request, 'Payment successful! Your booking is confirmed.')
    return render(request, 'passenger/payment_success.html')

#---------------------------------------------------------

from django.shortcuts import render, redirect
from django.contrib import messages
from decimal import Decimal

def calculate_total_fare(bus, route, selected_seats):
    # Base Fare and Fare Rate from bus object
    fare_rate = bus.fare_rate  # ₹2 per km (Decimal)
    base_fare = bus.base_fare  # ₹10 (Decimal)
    
    # Distance from route object
    distance = Decimal(route.distance)  # 108.0 km (Decimal)
    
    # Number of selected seats
    number_of_seats = len(selected_seats)  # Assuming 1 seat is selected
    
    # Debugging output
    print(f"Base Fare: {base_fare}, Fare Rate: {fare_rate}, Distance: {distance}, Number of Seats: {number_of_seats}")

    # Fare per seat calculation
    fare_per_seat = fare_rate + (base_fare * distance)  # ₹226 per seat
    
    # Debug output for fare per seat
    print(f"Fare per seat: {fare_per_seat}")

    # Calculate total fare for selected seats
    total_fare = fare_per_seat * number_of_seats  # ₹226 * 1 seat = ₹226
    
    # Debug output for total fare
    print(f"Total Fare: {total_fare}")
    
    return total_fare

#---------------------------------------------------------

from django.shortcuts import render, redirect
from django.contrib import messages
from decimal import Decimal
from .models import Bus, Schedule, Route, Booking

def payment(request):
    # Ensure passenger is logged in
    passenger_id = request.session.get('passenger_id')
    if not passenger_id:
        messages.error(request, 'You need to log in as a passenger to continue.')
        return redirect('index')  # Redirect to login page or dashboard
    
    # Retrieve selected seat details from session
    selected_seats = request.session.get('selected_seats', [])
    schedule_id = request.session.get('schedule_id')
    bus_id = request.session.get('bus_id')
    route_id = request.session.get('route_id')

    try:
        # Fetch schedule, bus, and route details
        schedule = Schedule.objects.get(schedule_id=schedule_id)
        bus = Bus.objects.get(bus_id=bus_id)
        route = Route.objects.get(route_id=schedule.route_id)
    except (Schedule.DoesNotExist, Bus.DoesNotExist, Route.DoesNotExist):
        messages.error(request, "Invalid bus, schedule, or route.")
        return redirect('passenger_dashboard')

    # Calculate fare components
    fare_rate = bus.fare_rate  # Fare rate per kilometer (Decimal)
    base_fare = bus.base_fare  # Base fare (Decimal)
    distance = Decimal(route.distance)  # Convert distance to Decimal for precision
    number_of_seats = len(selected_seats)  # Number of seats selected

    # Fare per seat calculation
    fare_per_seat =  base_fare+ (fare_rate   * distance)

    # Total fare calculation
    total_fare = fare_per_seat * number_of_seats

    # Handle payment confirmation
    if request.method == "POST":
        # Store passenger_id again to prevent session loss
        request.session['passenger_id'] = passenger_id
        request.session.modified = True  # Ensure Django updates the session
        request.session.save()  # Explicitly save session to avoid loss

        # Save booking in DB
        booking = Booking.objects.create(
            passenger_id=passenger_id,
            schedule=schedule,
            bus=bus,
            seat_number=",".join(map(str, selected_seats)),  # Store seats as comma-separated values
            status=Booking.Status.CONFIRMED,
            total_fare=total_fare
        )

        messages.success(request, f"Payment successful! Your booking ID is {booking.booking_id}")
        return redirect('payment_success')  # Redirect to restore session and then go to dashboard

    return render(request, 'passenger/payment.html', {
        'selected_seats': selected_seats,
        'schedule': schedule,
        'bus': bus,
        'route': route,
        'total_fare': total_fare,
        'fare_per_seat': fare_per_seat,  # Send fare per seat to the template
        'base_fare': base_fare,
        'fare_rate': fare_rate,
        'distance': distance,
        'route_id': route_id
    })

#---------------------------------------------------------

from django.shortcuts import render, redirect
from django.contrib import messages
from decimal import Decimal
from .models import Bus, Schedule, Route

def details(request):
    # Get session data
    passenger_id = request.session.get('passenger_id')
    selected_seats = request.session.get('selected_seats', [])
    schedule_id = request.session.get('schedule_id')
    bus_id = request.session.get('bus_id')
    route_id = request.session.get('route_id')

    # Fetch bus, schedule, and route data using the IDs stored in the session
    try:
        # Fetch schedule, bus, and route details
        schedule = Schedule.objects.get(schedule_id=schedule_id)
        bus = Bus.objects.get(bus_id=bus_id)
        route = Route.objects.get(route_id=schedule.route_id)
    except (Schedule.DoesNotExist, Bus.DoesNotExist, Route.DoesNotExist):
        messages.error(request, "Invalid bus, schedule, or route.")
        return redirect('passenger_dashboard')

    # Calculate fare components
    fare_rate = bus.fare_rate  # Fare rate per kilometer (Decimal)
    base_fare = bus.base_fare  # Base fare (Decimal)
    distance = Decimal(route.distance)  # Convert distance to Decimal for precision
    number_of_seats = len(selected_seats)  # Number of seats selected

    # Calculate fare per seat
    fare_per_seat =  fare_rate + ( base_fare * distance)

    # Calculate total fare
    total_fare = fare_per_seat * number_of_seats

    # Save the total fare in session
    request.session['total_fare'] = float(total_fare)

    # Pass all the details to the 'passenger/payment_details.html' template
    return render(request, 'passenger/payment_details.html', {
        'selected_seats': selected_seats,
        'schedule': schedule,
        'bus': bus,
        'route': route,
        'fare_rate': fare_rate,
        'base_fare': base_fare,
        'distance': distance,
        'fare_per_seat': fare_per_seat,
        'total_fare': total_fare,
        'route_id': route_id
    })


#---------------------------------------------------------

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt  # Only if needed
from django.shortcuts import render

def traveller_details(request):
    if request.method == 'POST':
        try:
            # Store traveller data in session
            traveller_data = []
            seat_numbers = request.POST.getlist('seat_numbers[]')
            names = request.POST.getlist('passenger_names[]')
            ages = request.POST.getlist('passenger_ages[]')
            genders = request.POST.getlist('passenger_genders[]')
            
            for i in range(len(seat_numbers)):
                traveller_data.append({
                    'seat': seat_numbers[i],
                    'name': names[i],
                    'age': ages[i],
                    'gender': genders[i]
                })
            
            # Store in session
            request.session['traveller_data'] = traveller_data
            
            return JsonResponse({
                'success': True,
                'message': 'Traveller details saved successfully'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({
        'success': False,
        'error': 'Invalid request method'
    })
    
#---------------------------------------------------------

def payee_details(request):
    if request.method == 'POST':
        try:
            # Store payee data in session
            payee_data = {
                'mobile': request.POST.get('mobile'),
                'email': request.POST.get('email')
            }
            request.session['payee_data'] = payee_data
            
            # Generate HTML summaries
            traveller_data = request.session.get('traveller_data', [])
            traveller_html = generate_traveller_summary(traveller_data)
            payee_html = generate_payee_summary(payee_data)
            
            return JsonResponse({
                'success': True,
                'traveller_details_html': traveller_html,
                'payee_details_html': payee_html
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({
        'success': False,
        'error': 'Invalid request method'
    })

#---------------------------------------------------------

def generate_traveller_summary(traveller_data):
    html = "<h6>Traveller Details:</h6><ul>"
    for traveller in traveller_data:
        html += f"""<li>Seat {traveller['seat']}: {traveller['name']} 
                   (Age: {traveller['age']}, Gender: {traveller['gender']})</li>"""
    html += "</ul>"
    return html

#---------------------------------------------------------

def generate_payee_summary(payee_data):
    return f"""<h6>Contact Details:</h6>
              <p>Mobile: {payee_data['mobile']}<br>
              Email: {payee_data['email']}</p>"""

#---------------------------------------------------------

from django.http import JsonResponse
from django.utils import timezone
from .models import Booking, Schedule, PayeeDetails, PassengerTravelDetails, Payment, Bus  # Import Bus model if needed

def process_booking_payment(request):
    if request.method == 'POST':
        try:
            # Retrieve session data
            passenger_id = request.session.get('passenger_id')
            traveller_data = request.session.get('traveller_data', [])
            payee_data = request.session.get('payee_data', {})
            schedule_id = request.session.get('schedule_id')
            total_fare = request.session.get('total_fare')
            bus_id = request.session.get('bus_id')  # Retrieve bus_id from session

            # Debugging prints
            print(f"Passenger ID: {passenger_id}")
            print(f"Schedule ID: {schedule_id}")
            print(f"Traveller Data: {traveller_data}")
            print(f"Payee Data: {payee_data}")
            print(f"Bus ID: {bus_id}")

            # Validate session data
            if not passenger_id or not traveller_data or not payee_data or not schedule_id or total_fare is None or not bus_id:
                return JsonResponse({
                    'success': False,
                    'error': 'Incomplete data. Please complete all forms.'
                })

            # Retrieve the Schedule object
            try:
                schedule = Schedule.objects.get(schedule_id=schedule_id)
            except Schedule.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid schedule ID. Schedule does not exist.'
                })

            # Retrieve the Bus object
            try:
                bus = Bus.objects.get(bus_id=bus_id)
            except Bus.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid bus ID. Bus does not exist.'
                })

            # Get all seat numbers in a comma-separated string
            seat_numbers = ",".join([traveller['seat'] for traveller in traveller_data])

            # Prevent duplicate booking
            existing_seats = ",".join(sorted([traveller['seat'] for traveller in traveller_data]))
            if Booking.objects.filter(
                passenger_id=passenger_id,
                schedule=schedule,
                seat_number=existing_seats
            ).exists():
                return JsonResponse({
                    'success': False,
                    'error': 'Booking already exists for the selected seats.',
                    'redirect': '/passenger-dashboard/'
                })


            # Create a single Booking entry
            booking = Booking.objects.create(
                passenger_id=passenger_id,
                schedule=schedule,
                seat_number=seat_numbers,
                status=Booking.Status.CONFIRMED 
            )

            # Create PayeeDetails (only once for all travelers)
            payee = PayeeDetails.objects.create(
                booking=booking,
                mobile_number=payee_data['mobile'],
                email=payee_data['email']
            )

            # Store Traveller details with bus_id
            for traveller in traveller_data:
                PassengerTravelDetails.objects.create(
                    payee_details=payee,
                    seat_number=traveller['seat'],
                    name=traveller['name'],
                    age=traveller['age'],
                    gender=traveller['gender'],
                    booking=booking,
                    bus=bus  # Associate traveler with the bus
                )

            # Process Payment
            payment = Payment.objects.create(
                amount=total_fare,
                payment_date=timezone.now(),
                payment_method=request.POST.get('payment_method', 'Pay Later'),
                booking=booking,
                passenger_id=passenger_id
            )

            return JsonResponse({
                'success': True,
                'message': 'Booking successful!',
                'redirect_url': f'/booking-confirmation/{booking.booking_id}/',
                'delay': 3000  # 3 seconds delay (in milliseconds)
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e),
                'redirect': '/passenger-dashboard/'
            })

#---------------------------------------------------------

def booking_success(request):
    return render(request, 'passenger/booking_success.html')

#---------------------------------------------------------

from django.http import HttpResponse
from reportlab.pdfgen import canvas # type: ignore
from reportlab.lib.pagesizes import A4 # type: ignore
from reportlab.lib import colors # type: ignore
from datetime import datetime
from .models import Booking, PayeeDetails, PassengerTravelDetails, Payment, EmployeeBusAssignment, Employee
import os

def generate_booking_pdf(request, booking_id):
    try:
        booking = Booking.objects.get(booking_id=booking_id)
        payee = PayeeDetails.objects.filter(booking=booking).first()
        passengers = PassengerTravelDetails.objects.filter(booking=booking)
        payment = Payment.objects.filter(booking=booking).first()
        assigned_staff = EmployeeBusAssignment.objects.filter(bus=booking.schedule.bus if booking.schedule else None, employee__role=Employee.STAFF)

        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="Bus Ticket Confirmation.pdf"'

        p = canvas.Canvas(response, pagesize=A4)
        width, height = A4

        def add_new_page():
            p.showPage()
            p.setFont("Helvetica", 12)
            return height - 50  # Reset y position

        # **Time Now (Top Left Corner)**
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        p.setFont("Helvetica", 10)
        p.drawString(width - 150, height - 30, current_time)

        # **Title (Centered)**
        p.setFont("Helvetica-Bold", 18)
        title = "Bus Ticket"
        title_width = p.stringWidth(title, "Helvetica-Bold", 18)
        p.drawString((width - title_width) / 2, height - 50, title)

        # **Customer Message**
        p.setFont("Helvetica-Bold", 14)
        p.drawString(50, height - 80, "Dear Customer,")
        p.setFont("Helvetica", 12)
        message = (
            "Thank you for your booking.\n"
            "Please follow and comply with the local government's travel advisories and guidelines, \nsuch as carrying medical certificates, ID, etc. "
            "You may be denied boarding if you don't comply."
        )
        y = height - 100
        for line in message.split("\n"):
            p.drawString(50, y, line)
            y -= 20
        y -= 30  # Extra space for clarity

        # **Trip Details Section**
        # **Trip Details Section**
        p.setFont("Helvetica-Bold", 15)
        p.drawString(50, y, "Trip Details")
        y -= 20
        p.line(50, y, width - 50, y)
        y -= 30
        p.setFont("Helvetica", 12)

        # Show Bus Name Before Departure Time
        p.drawString(50, y, f"Bus Name: {booking.schedule.bus.bus_name if booking.schedule and booking.schedule.bus else 'N/A'}")
        y -= 20

        p.drawString(50, y, f"Departure: {booking.schedule.departure_time.strftime('%Y-%m-%d %H:%M')} | Source: {booking.schedule.route.source}")
        y -= 20
        p.drawString(50, y, f"Arrival: {booking.schedule.arrival_time.strftime('%Y-%m-%d %H:%M')} | Destination: {booking.schedule.route.destination}")
        y -= 40


        # **Assigned Staff Section (Moved Below Trip Details)**
        # Fetch the booking object
        booking = Booking.objects.get(booking_id=booking_id)

        # Ensure that 'schedule' exists before accessing 'bus'
        schedule_instance = booking.schedule
        bus_instance = schedule_instance.bus if schedule_instance else None  # ✅ Fix: Get bus from schedule

        # Ensure bus_instance is not None before querying staff
        if bus_instance:
            assigned_staff = EmployeeBusAssignment.objects.filter(bus=bus_instance, schedule=schedule_instance)
        else:
            assigned_staff = EmployeeBusAssignment.objects.none()  # Empty QuerySet

        p.setFont("Helvetica-Bold", 15)
        p.drawString(50, y, "Bus Staff Details")
        y -= 20
        p.line(50, y, width - 50, y)
        y -= 20
        p.setFont("Helvetica", 12)
        if assigned_staff.exists():
            for assignment in assigned_staff:
                if assignment.employee.role == 'Staff':  # ✅ Filter only "Staff" role
                    p.drawString(50, y, assignment.employee.name)
                    p.drawString(250, y, assignment.employee.phone_number)
                    y -= 20
                    if y < 50:
                        y = add_new_page()
        else:
            p.drawString(50, y, "No assigned staff.")
            y -= 20
        y -= 40

        # **Payee Details Section**
        p.setFont("Helvetica-Bold", 15)
        p.drawString(50, y, "Payee Details")
        y -= 20
        p.line(50, y, width - 50, y)
        y -= 20
        p.setFont("Helvetica", 12)
        p.drawString(50, y, f"Mobile: {payee.mobile_number if payee else 'N/A'}")
        p.drawString(250, y, f"Email: {payee.email if payee else 'N/A'}")
        y -= 40

        # **Payment Details Section**
        p.setFont("Helvetica-Bold", 15)
        p.drawString(50, y, "Payment Details")
        y -= 20
        p.line(50, y, width - 50, y)
        y -= 20
        p.setFont("Helvetica", 12)
        p.drawString(50, y, f"Amount Paid(Rupee): {payment.amount if payment else 'N/A'}/-")
        y -= 20
        p.drawString(50, y, f"Method: {payment.payment_method if payment else 'N/A'}")
        y -= 20
        p.drawString(50, y, f"Date: {payment.payment_date.strftime('%Y-%m-%d %H:%M') if payment else 'N/A'}")
        y -= 40

        # **Passenger Details Section (Moved to Bottom)**
        p.setFont("Helvetica-Bold", 15)
        p.drawString(50, y, "Passenger Details")
        y -= 20
        p.line(50, y, width - 50, y)
        y -= 20
        p.setFont("Helvetica-Bold", 12)
        p.drawString(50, y, "Seat No:")
        p.drawString(150, y, "Name, Age, Sex")
        y -= 20
        p.setFont("Helvetica", 12)
        
        for passenger in passengers:
            p.drawString(50, y, f"{passenger.seat_number}")
            p.drawString(150, y, f"{passenger.name}, {passenger.age}, {passenger.gender}")
            y -= 20
            if y < 50:
                y = add_new_page()

        p.showPage()
        p.save()
        return response

    except Booking.DoesNotExist:
        return HttpResponse("Booking not found", status=404)


#---------------------------------------------------------


from django.shortcuts import render, get_object_or_404
from .models import Booking

def booking_confirmation(request, booking_id):
    booking = get_object_or_404(Booking, booking_id=booking_id)
    return render(request, 'passenger/booking_confirmation.html', {'booking': booking})

#---------------------------------------------------------

def passenger_profile(request):
    passenger_id = request.session.get('passenger_id')

    if not passenger_id:
        messages.error(request, 'You need to log in first.')
        return redirect('index')  # Redirect to the login page

    try:
        # Retrieve the Passenger object based on the passenger_id in the session
        passenger = Passenger.objects.get(passenger_id=passenger_id)
    except Passenger.DoesNotExist:
        messages.error(request, 'Invalid session. Please log in again.')
        return redirect('index')  # Redirect to the login page

    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone_number = request.POST.get('phone_number')
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        # Validate old password
        if old_password != passenger.password:
            messages.error(request, "Old password is incorrect.")
            return redirect('passenger_profile')

        # Ensure new password is different from the old password
        if new_password == old_password:
            messages.error(request, "New password cannot be the same as the old password.")
            return redirect('passenger_profile')

        # Ensure new password and confirm password match
        if new_password != confirm_password:
            messages.error(request, "New password and confirm password do not match.")
            return redirect('passenger_profile')

        # Update details
        passenger.name = name
        passenger.email = email
        passenger.phone_number = phone_number
        passenger.password = new_password  # No hashing applied
        passenger.save()

        messages.success(request, "Profile updated successfully!")
        return redirect('passenger_profile')

    return render(request, 'passenger/profile.html', {'passenger': passenger})

#------------------------------------------------------------------------------------------------------------------

#--------------------------------------------------Snack Page------------------------------------------------------

def order_snacks(request, booking_id):
    snacks = Snack.objects.all()  # Fetch all snacks from the database
    return render(request, 'passenger/order_snacks.html', {'booking_id': booking_id, 'snacks': snacks})

#----------------------------------------------------------

# views.py
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from .models import SnackOrder, Booking, Snack

def cancel_snack_order(request, booking_id, snack_id):
    # Retrieve the booking and snack using the IDs
    booking = get_object_or_404(Booking, booking_id=booking_id)
    snack = get_object_or_404(Snack, id=snack_id)

    # Retrieve the specific SnackOrder that matches the booking and snack
    snack_order = get_object_or_404(SnackOrder, booking=booking, snack=snack, status=SnackOrder.ORDERED)

    # Update the status of the snack order to 'Cancelled'
    snack_order.status = SnackOrder.CANCELLED
    snack_order.save()

    # Redirect to the booking details page (same page)
    return redirect(reverse('passenger_booking_details', kwargs={'booking_id': booking_id}))


  

#---------------------------------------------------------

from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

@csrf_exempt
def add_to_cart(request, snack_id, booking_id):
    if request.method == 'POST':
        snack = get_object_or_404(Snack, id=snack_id)
        booking = get_object_or_404(Booking, booking_id=booking_id)
        
        # Get the cart from session or initialize it
        cart = request.session.get('cart', [])

        # Check if the snack is already in the cart
        for item in cart:
            if item['snack_id'] == snack_id and item['booking_id'] == booking_id:
                item['quantity'] += 1  # Increase quantity if already exists
                break
        else:
            # If not in cart, add new item
            cart.append({
                'snack_id': snack.id,
                'snack_name': snack.name,
                'price': float(snack.price),  # Ensure it's JSON serializable
                'quantity': 1,
                'booking_id': booking_id
            })

        # Save the cart back to session
        request.session['cart'] = cart
        request.session.modified = True

        return JsonResponse({'message': 'Snack added to cart', 'cart': cart}, status=200)

    return JsonResponse({'error': 'Invalid request'}, status=400)


#---------------------------------------------------------

import json
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.urls import reverse

def checkout_view(request):
    if request.method == 'POST':
        try:
            booking_id = request.POST.get('booking_id')
            cart_data = request.POST.get('cart_data')
            print("🔍 Raw booking ID:", booking_id)
            print("🔍 Raw cart data:", cart_data)
            
            if not cart_data:
                return HttpResponse("""
                <script>
                    alert('No cart data received');
                    window.location.href = '{}';
                </script>
                """.format(reverse('checkout')))
            
            try:
                cart_data = json.loads(cart_data)
            except json.JSONDecodeError:
                return HttpResponse("""
                <script>
                    alert('Invalid JSON format in cart data');
                    window.location.href = '{}';
                </script>
                """.format(reverse('checkout')))
                
            if not isinstance(cart_data, list):
                return HttpResponse("""
                <script>
                    alert('Cart data should be a list');
                    window.location.href = '{}';
                </script>
                """.format(reverse('checkout')))
                
            booking = get_object_or_404(Booking, booking_id=booking_id)
            passenger = booking.passenger
            
            for item in cart_data:
                print("🔹 Processing item:", item)
                
                if not isinstance(item, dict):
                    return HttpResponse("""
                    <script>
                        alert('Each cart item must be a dictionary');
                        window.location.href = '{}';
                    </script>
                    """.format(reverse('checkout')))
                
                snack_id = item.get('id')
                quantity = item.get('quantity')
                
                print(f"✅ Extracted snack_id: {snack_id}, quantity: {quantity}")
                
                try:
                    if snack_id is not None and isinstance(snack_id, str):
                        snack_id = int(snack_id)
                    if quantity is not None and isinstance(quantity, str):
                        quantity = int(quantity)
                except ValueError:
                    return HttpResponse("""
                    <script>
                        alert('Invalid conversion of snack ID or quantity');
                        window.location.href = '{}';
                    </script>
                    """.format(reverse('checkout')))
                
                if snack_id is None or not isinstance(snack_id, int):
                    return HttpResponse("""
                    <script>
                        alert('Invalid snack ID: {}');
                        window.location.href = '{}';
                    </script>
                    """.format(snack_id, reverse('checkout')))
                    
                if quantity is None or not isinstance(quantity, int):
                    return HttpResponse("""
                    <script>
                        alert('Invalid quantity: {}');
                        window.location.href = '{}';
                    </script>
                    """.format(quantity, reverse('checkout')))
                    
                try:
                    snack = Snack.objects.get(id=snack_id)
                except Snack.DoesNotExist:
                    return HttpResponse("""
                    <script>
                        alert('No Snack found with ID {}');
                        window.location.href = '{}';
                    </script>
                    """.format(snack_id, reverse('checkout')))
                    
                SnackOrder.objects.create(
                    passenger=passenger,
                    booking=booking,
                    snack=snack,
                    quantity=quantity,
                    total_price=snack.price * quantity,
                    status=SnackOrder.ORDERED
                )
            
            # Success case - all items processed
            return HttpResponse("""
            <script>
                alert('Order placed successfully! Pay for them only when you board the bus.');
                window.location.href = '{}';
            </script>
            """.format(reverse('passenger_dashboard')))
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return HttpResponse("""
            <script>
                alert('An error occurred: {}');
                window.location.href = '{}';
            </script>
            """.format(str(e).replace("'", "\\'"), reverse('checkout')))
            
    return redirect('view_booking')

#---------------------------------------------------------

from django.shortcuts import render, redirect
from .models import Snack, Employee
from decimal import Decimal

def add_snack(request):
    """Handle snack addition with employee_id from session."""
    employee_id = request.session.get('staff_id')  # Using 'staff_id' from session
    print(f"🛠 Session Data: {request.session.items()}")  # Debugging

    if request.method == 'POST':
        print("✅ POST Data Received:", request.POST)  # Debugging
        
        name = request.POST.get('name')
        price = request.POST.get('price')
        image = request.FILES.get('image')

        # Ensure price is valid
        try:
            price = Decimal(price)
            print("✅ Converted Price:", price)
        except:
            print("❌ Invalid price format")
            return render(request, 'employee/add_snack.html', {'error': 'Invalid price format', 'employee_id': employee_id})

        # Insert into database
        if employee_id:
            try:
                employee = Employee.objects.get(employee_id=employee_id)
                snack = Snack.objects.create(name=name, price=price, added_by=employee, image=image)
                print(f"✅ Snack Created: {snack} | Employee ID: {employee.employee_id}")
            except Employee.DoesNotExist:
                print("❌ Employee not found in the database!")
                return render(request, 'employee/add_snack.html', {'error': 'You are not registered as an employee.', 'employee_id': employee_id})

        return redirect('snack_list')

    return render(request, 'employee/add_snack.html', {'employee_id': employee_id})

#---------------------------------------------------------

def edit_snack(request, snack_id):
    """Edit an existing snack."""
    snack = get_object_or_404(Snack, id=snack_id)

    if request.method == 'POST':
        snack.name = request.POST.get('name')
        snack.price = request.POST.get('price')

        # Validate and convert price
        try:
            snack.price = Decimal(snack.price)
        except:
            return render(request, 'employee/edit_snack.html', {'error': 'Invalid price format', 'snack': snack})

        if 'image' in request.FILES:
            snack.image = request.FILES['image']

        snack.save()
        return redirect('snack_list')

    return render(request, 'employee/edit_snack.html', {'snack': snack})

#---------------------------------------------------------

def view_orders(request):
    employee_id = request.session.get('staff_id')  # Using 'staff_id' from session
    if not employee_id:
        return redirect('logout')  # Redirect if no employee is logged in

    snacks = Snack.objects.filter(added_by_id=employee_id)  # Fetch only snacks added by this employee
    return render(request, 'employee/orders.html', {'snacks': snacks})

#---------------------------------------------------------

def delete_snack(request, snack_id):
    """Delete a snack."""
    snack = get_object_or_404(Snack, id=snack_id)
    snack.delete()
    return redirect('snack_list')

#---------------------------------------------------------

def view_snack_orders(request):
    employee_id = request.session.get('staff_id')  # Get the logged-in staff's ID from session
    if not employee_id:
        return redirect('staff_dashboard')  # Redirect to login if not authenticated

    # Get all snacks added by this employee
    staff_snacks = Snack.objects.filter(added_by_id=employee_id)

    # Get orders where the ordered snack was added by this employee
    snack_orders = SnackOrder.objects.filter(snack__in=staff_snacks).order_by('snack_id')

    return render(request, 'employee/snack_order.html', {'snack_orders': snack_orders})

#---------------------------------------------------------

def bus_owner_snacks(request):
    owner_id = request.session.get('owner_id')  # Get the bus owner's ID from the session

    if not owner_id:
        return render(request, 'busowner_dashboard.html', {'message': 'Bus Owner not logged in'})

    # Fetch all snacks added by employees under this bus owner
    snacks = Snack.objects.filter(added_by__owner_id=owner_id)

    return render(request, 'busowner/view_snacks.html', {'snacks': snacks})

#---------------------------------------------------------

def bus_owner_snack_orders(request):
    owner_id = request.session.get('owner_id')
    if not owner_id:
        return render(request, 'busowner_dashboard.html', {'message': 'Bus Owner not logged in'})

    # Get all snack orders where the booking is associated with a bus owned by the logged-in owner
    snack_orders = SnackOrder.objects.filter(
        booking__schedule__bus__owner_id=owner_id
    ).select_related('snack', 'booking', 'booking__schedule', 'booking__schedule__bus')

    return render(request, 'busowner/view_snack_orders.html', {'snack_orders': snack_orders})


#---------------------------------------------------------

def passenger_view_snack_details(request, booking_id):
    booking = Booking.objects.filter(booking_id=booking_id).first()
    if not booking:
        return render(request, 'not_found.html', {'message': 'Booking not found'})

    snack_orders = SnackOrder.objects.filter(booking=booking)
    return render(request, 'passenger/view_snack_details.html', {
        'booking': booking,
        'snack_orders': snack_orders
    })

#---------------------------------------------------------

from django.shortcuts import redirect
from django.contrib import messages

def cancel_snack_order(request, order_id):
    order = SnackOrder.objects.filter(order_id=order_id).first()
    if order and order.status == "Ordered":
        order.status = "Cancelled"
        order.save()
        messages.success(request, "Snack order cancelled successfully.")
    else:
        messages.warning(request, "Snack order could not be cancelled.")
    
    # Redirect back to the snack viewing page
    return redirect('view_snack_details', booking_id=order.booking.booking_id if order else 0)

#---------------------------------------------------------

from django.utils import timezone
from django.shortcuts import redirect
from django.contrib import messages
from .models import Booking, BusOwner

def update_completed_bookings(request):
    now = timezone.now()

    # Fetch the bus owner ID from the session
    owner_id = request.session.get('owner_id')

    if not owner_id:
        messages.error(request, "You need to be logged in as a bus owner to update bookings.")
        return redirect('login')  # Redirect to the login page if the owner_id is not found in the session

    try:
        # Get the bus owner object based on the owner_id from the session
        bus_owner = BusOwner.objects.get(owner_id=owner_id)
    except BusOwner.DoesNotExist:
        messages.error(request, "Bus owner not found.")
        return redirect('login')  # Redirect to the login page if the bus owner is not found

    # Fetch the schedules related to this bus owner
    bus_owner_schedules = bus_owner.schedule_set.all()

    # Fetch bookings related to the bus owner's schedules, that are confirmed and the arrival time has passed
    bookings_to_update = Booking.objects.filter(
        status=Booking.Status.CONFIRMED,
        schedule__in=bus_owner_schedules,
        schedule__arrival_time__lt=now
    )

    # Update the status of the bookings
    updated_count = bookings_to_update.update(status=Booking.Status.COMPLETED)

    # Provide feedback to the bus owner
    messages.success(request, f"{updated_count} booking(s) marked as Completed.")
    return redirect('busowner_dashboard')  # Replace with your actual URL name


#---------------------------------------------------------

from django.utils import timezone
from django.shortcuts import redirect
from django.contrib import messages
from .models import SnackOrder  # Make sure this import is correct

def update_completed_orders(request):
    now = timezone.now()

    # Filter only snack orders with status 'Ordered' and where the booking's arrival time has passed
    orders_to_update = SnackOrder.objects.filter(
        status=SnackOrder.ORDERED,  # Only target 'Ordered' status
        booking__schedule__arrival_time__lt=now
    )

    updated_count = orders_to_update.update(status=SnackOrder.COMPLETED)

    messages.success(request, f"{updated_count} snack order(s) marked as Completed.")
    return redirect('staff_dashboard')  # Change if needed

#---------------------------------------------------------

from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Employee, Schedule, Attendance, BusOwner
from datetime import datetime

def owner_mark_attendance(request):
    owner_id = request.session.get('owner_id')

    if not owner_id:
        messages.error(request, "You need to log in as a bus owner to access this page.")
        return redirect('index')

    if request.method == 'POST':
        employee_id = request.POST.get('employee_id')
        schedule_id = request.POST.get('schedule_id')
        attendance_status = request.POST.get('attendance_status')
        attendance_date = request.POST.get('attendance_date')

        if employee_id and schedule_id and attendance_status and attendance_date:
            try:
                employee = Employee.objects.get(employee_id=employee_id)
                schedule = Schedule.objects.get(schedule_id=schedule_id)
                date = datetime.strptime(attendance_date, "%Y-%m-%d").date()

                # Check if attendance already exists for this employee, schedule, and date
                already_exists = Attendance.objects.filter(
                    employee=employee,
                    schedule=schedule,
                    date=date
                ).exists()

                if already_exists:
                    messages.error(request, "Attendance already marked for this employee and schedule on the selected date.")
                else:
                    Attendance.objects.create(
                        employee=employee,
                        schedule=schedule,
                        date=date,
                        status=attendance_status
                    )
                    messages.success(request, "Attendance marked successfully!")

            except (Employee.DoesNotExist, Schedule.DoesNotExist):
                messages.error(request, "Invalid employee or schedule selection.")
        else:
            messages.error(request, "Please fill in all required fields.")

    employees = Employee.objects.filter(owner_id=owner_id)
    schedules = Schedule.objects.filter(owner_id=owner_id)

    return render(request, 'busowner/mark_attendance.html', {
        'employees': employees,
        'schedules': schedules
    })

#---------------------------------------------------------

def bus_images(request, bus_id):
    bus = Bus.objects.filter(bus_id=bus_id).first()  # Get the first bus matching the bus_id
    if not bus:
        return render(request, 'bus_images.html', {'error': 'Bus not found'})  # Handle case if bus is not found
    images = BusImage.objects.filter(bus=bus)
    return render(request, 'bus_images.html', {'bus': bus, 'images': images})

#---------------------------------------------------------

def add_bus_image(request):
    owner_id = request.session.get('owner_id')

    if not owner_id:
        messages.error(request, "You must be logged in as a Bus Owner to upload images.")
        return redirect('index')

    if request.method == 'POST':
        print("🖼️ POST Data Received:", request.POST)
        bus_id = request.POST.get('bus_id')
        image = request.FILES.get('image')

        if not bus_id or not image:
            return render(request, 'busowner/add_bus_image.html', {
                'error': 'Bus and image are required.',
                'buses': Bus.objects.filter(owner_id=owner_id)
            })

        try:
            bus = Bus.objects.get(bus_id=bus_id, owner_id=owner_id)
        except Bus.DoesNotExist:
            return render(request, 'busowner/add_bus_image.html', {
                'error': 'Invalid bus or you do not own this bus.',
                'buses': Bus.objects.filter(owner_id=owner_id)
            })

        BusImage.objects.create(bus=bus, image=image)
        print("Bus Image uploaded.")
        return redirect('add_bus_image')  # You can change this to your image list view

    # GET request
    buses = Bus.objects.filter(owner_id=owner_id)
    return render(request, 'busowner/add_bus_image.html', {'buses': buses})