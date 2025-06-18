from django.db import models

# Create your models here.

class Admin(models.Model):
    admin_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    email = models.EmailField(max_length=100)
    password = models.CharField(max_length=100)

    def __str__(self):
        return f'Admin ID: {self.admin_id}, Name: {self.name}, Email: {self.email}'

class BusOwner(models.Model):
    owner_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    email = models.EmailField(max_length=100)
    password = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=15, unique=True)
    admin = models.ForeignKey(Admin, on_delete=models.CASCADE)

    def __str__(self):
        return f'Owner ID: {self.owner_id}, Name: {self.name}, Email: {self.email}, Phone: {self.phone_number}, Admin ID: {self.admin.admin_id}'

class Bus(models.Model):
    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Inactive', 'Inactive'),
    ]

    bus_id = models.AutoField(primary_key=True)
    bus_name = models.CharField(max_length=20)
    capacity = models.IntegerField()
    registration_number = models.CharField(max_length=50, unique=True)
    bus_type = models.CharField(max_length=50, null=True, blank=True)
    owner = models.ForeignKey(BusOwner, null=True, blank=True, on_delete=models.SET_NULL)
    base_fare = models.DecimalField(max_digits=10, decimal_places=2)  # Fixed base fare
    fare_rate = models.DecimalField(max_digits=10, decimal_places=2)  # Fare rate per kilometer
    travel_company_name = models.CharField(max_length=100, null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='none')

    def calculate_total_fare(self, distance, number_of_seats):
        """Calculates total fare based on distance and number of seats."""
        
        # Calculate fare per seat (Base Fare + Fare per Km * Distance)
        fare_per_seat = self.base_fare + (self.fare_rate * distance)
        
        # Calculate total fare (Fare per seat * Number of seats)
        total_fare = fare_per_seat * number_of_seats
        
        return total_fare

   
    def __str__(self):
        return f'Bus ID: {self.bus_id}, Name: {self.bus_name}, Capacity: {self.capacity}, Registration: {self.registration_number}, Base Fare: {self.base_fare}, Fare Rate: {self.fare_rate}, Bus Type: {self.bus_type}, Owner ID: {self.owner.owner_id if self.owner else None}, Travels Company: {self.travel_company_name if self.travel_company_name else "N/A"}, Status: {self.status}'

class BusImage(models.Model):
    bus = models.ForeignKey('Bus', on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='bus_images/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for Bus ID {self.bus.bus_id}"

class Route(models.Model):
    route_id = models.AutoField(primary_key=True)
    source = models.CharField(max_length=100)
    destination = models.CharField(max_length=100)
    distance = models.FloatField(null=True, blank=True)
    owner = models.ForeignKey(BusOwner, null=True, blank=True, on_delete=models.SET_NULL)
    bus = models.ForeignKey(Bus, null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return f'Route ID: {self.route_id}, Source: {self.source}, Destination: {self.destination}, Distance: {self.distance}, Owner ID: {self.owner.owner_id if self.owner else None}, Bus ID: {self.bus.bus_id if self.bus else None}'

class Schedule(models.Model):
    schedule_id = models.AutoField(primary_key=True)
    bus = models.ForeignKey(Bus, null=True, blank=True, on_delete=models.SET_NULL)
    route = models.ForeignKey(Route, null=True, blank=True, on_delete=models.SET_NULL)
    departure_time = models.DateTimeField()
    arrival_time = models.DateTimeField()
    owner = models.ForeignKey(BusOwner, null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return f'Schedule ID: {self.schedule_id}, Bus ID: {self.bus.bus_id if self.bus else None}, Route ID: {self.route.route_id if self.route else None}, Departure: {self.departure_time}, Arrival: {self.arrival_time}, Owner ID: {self.owner.owner_id if self.owner else None}'

class Passenger(models.Model):
    passenger_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    email = models.EmailField(max_length=100)
    password = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=15, unique=True)

    def __str__(self):
        return f'Passenger ID: {self.passenger_id}, Name: {self.name}, Email: {self.email}, Phone: {self.phone_number}'

from django.utils import timezone

class Booking(models.Model):
    class Status(models.TextChoices):
        CONFIRMED = 'Confirmed', 'Confirmed'
        CANCELLED = 'Cancelled', 'Cancelled'
        PENDING = 'Pending', 'Pending'
        COMPLETED = 'Completed', 'Completed'
    
    booking_id = models.AutoField(primary_key=True)
    passenger = models.ForeignKey('Passenger', null=True, blank=True, on_delete=models.SET_NULL)
    schedule = models.ForeignKey('Schedule', null=True, blank=True, on_delete=models.SET_NULL)
    seat_number = models.CharField(max_length=100)
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING
    )
    
    def __str__(self):
        return f'Booking ID: {self.booking_id}, Passenger ID: {self.passenger.passenger_id if self.passenger else None}, Schedule ID: {self.schedule.schedule_id if self.schedule else None}, Seat Number: {self.seat_number}, Status: {self.status}'

class Payment(models.Model):
    payment_id = models.AutoField(primary_key=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateTimeField()
    payment_method = models.CharField(max_length=50)
    booking = models.ForeignKey(Booking, null=True, blank=True, on_delete=models.SET_NULL)
    passenger = models.ForeignKey(Passenger, null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return f'Payment ID: {self.payment_id}, Amount: {self.amount}, Payment Date: {self.payment_date}, Payment Method: {self.payment_method}, Booking ID: {self.booking.booking_id if self.booking else None}, Passenger ID: {self.passenger.passenger_id if self.passenger else None}'

class Cancellation(models.Model):
    cancellation_id = models.AutoField(primary_key=True)
    passenger = models.ForeignKey(Passenger, null=True, blank=True, on_delete=models.SET_NULL)
    booking = models.ForeignKey(Booking, null=True, blank=True, on_delete=models.SET_NULL)
    booking_id_value = models.IntegerField(null=True, blank=True)  # Store Booking ID
    schedule = models.CharField(max_length=255, null=True, blank=True)  # Store schedule
    status = models.CharField(max_length=50, null=True, blank=True)  # Store booking status
    cancellation_date = models.DateTimeField()
 
    def __str__(self):
        return f'Cancellation ID: {self.cancellation_id}, Passenger: {self.passenger.passenger_id if self.passenger else None}, Booking ID: {self.booking_id_value}, Date: {self.cancellation_date}'

class Employee(models.Model):
    DRIVER = 'Driver'
    STAFF = 'Staff'
    ROLE_CHOICES = [
        (DRIVER, 'Driver'),
        (STAFF, 'Staff')
    ]
    employee_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    email = models.EmailField(max_length=100, unique=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    phone_number = models.CharField(max_length=15, unique=True)
    license_number = models.CharField(max_length=50, null=True, blank=True)
    password = models.CharField(max_length=255)
    owner = models.ForeignKey(BusOwner, null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return f'Employee ID: {self.employee_id}, Name: {self.name}, Role: {self.role}, Email: {self.email}, Phone: {self.phone_number}, License Number: {self.license_number if self.license_number else "N/A"}, Owner ID: {self.owner.owner_id if self.owner else None}'

class Attendance(models.Model):
    attendance_id = models.AutoField(primary_key=True)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE, null=True, blank=True)  # Added schedule_id
    date = models.DateField()
    status = models.CharField(max_length=10, choices=[('Present', 'Present'), ('Absent', 'Absent')], default='Present')

    def __str__(self):
        return f'Attendance ID: {self.attendance_id}, Employee: {self.employee.name}, Schedule: {self.schedule.schedule_id if self.schedule else "None"}, Date: {self.date}, Status: {self.status}'

class PayeeDetails(models.Model):
    booking = models.ForeignKey(Booking, null=True, blank=True, on_delete=models.CASCADE)
    mobile_number = models.CharField(max_length=15)
    email = models.EmailField()

    def __str__(self):
        return f'Payee ID: {self.id}, Booking ID: {self.booking.booking_id if self.booking else None}, Mobile: {self.mobile_number}, Email: {self.email}'

class PassengerTravelDetails(models.Model):
    payee_details = models.ForeignKey(PayeeDetails, on_delete=models.SET_NULL, null=True, blank=True)  # Link PayeeDetails here
    seat_number = models.CharField(max_length=100)
    name = models.CharField(max_length=100)
    age = models.PositiveIntegerField()
    gender = models.CharField(max_length=10)
    booking = models.ForeignKey('Booking', on_delete=models.SET_NULL, null=True, blank=True)
    bus = models.ForeignKey('Bus', on_delete=models.SET_NULL, null=True, blank=True)  # New FK to Bus

    def __str__(self):
        return f'Name: {self.name}, Age: {self.age}, Gender: {self.gender}, Seat: {self.seat_number}, Bus: {self.bus.bus_name if self.bus else "Unknown"}'

class EmployeeBusAssignment(models.Model):
    employee = models.ForeignKey('Employee', on_delete=models.CASCADE)
    bus = models.ForeignKey('Bus', on_delete=models.CASCADE)
    schedule = models.ForeignKey('Schedule', on_delete=models.CASCADE)  # New ForeignKey to Schedule

    def __str__(self):
        return f'{self.employee.name} assigned to {self.bus.bus_name} on Schedule ID {self.schedule.schedule_id}'

class JourneyDate(models.Model):
    journey_id = models.AutoField(primary_key=True)
    schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)  # Added employee field
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()

    def __str__(self):
        return f'Journey ID: {self.journey_id}, Schedule ID: {self.schedule.schedule_id}, Employee ID: {self.employee.employee_id}, Start: {self.start_date}, End: {self.end_date}'
    
    
    
#---------------------------------------------------- Snack models----------------------------------------------------


class Snack(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    added_by = models.ForeignKey('Employee', on_delete=models.CASCADE)  # No role restriction
    image = models.ImageField(upload_to="snacks/", blank=True, null=True)  # Allow image uploads

    def __str__(self):
        return f'{self.name} - ₹{self.price}'



class SnackOrder(models.Model):
    ORDERED = 'Ordered'
    CANCELLED = 'Cancelled'
    PENDING = 'Pending'
    COMPLETED = 'Completed'

    STATUS_CHOICES = [
        (ORDERED, 'Ordered'),
        (CANCELLED, 'Cancelled'),
        (PENDING, 'Pending'),
        (COMPLETED, 'Completed')
    ]

    order_id = models.AutoField(primary_key=True)
    passenger = models.ForeignKey('Passenger', on_delete=models.CASCADE)
    booking = models.ForeignKey('Booking', null=True, blank=True, on_delete=models.CASCADE)  # Link to Booking
    snack = models.ForeignKey('Snack', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=PENDING)
    ordered_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.snack:
            self.total_price = self.quantity * self.snack.price
        super().save(*args, **kwargs)

    def __str__(self):
        return f'Order #{self.order_id} - {self.passenger.name} (Booking #{self.booking.booking_id if self.booking else "N/A"}, {self.status})'
