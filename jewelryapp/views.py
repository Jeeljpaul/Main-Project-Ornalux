from django.shortcuts import render, redirect
from django.contrib import messages
from .models import *
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from .forms import PasswordResetRequestForm  # Import both forms
from django.utils.crypto import get_random_string
from django.core.mail import send_mail
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.db import transaction
from datetime import datetime, date
import random
import string
from django.conf import settings
from .document_verification import BusinessDocumentVerifier
import os
from django.views.decorators.http import require_POST
import json
from django.contrib.auth import authenticate, login
from django.http import JsonResponse
from .models import VendorPayment, PaymentRequest
from .models import VendorProduct
from .models import Wishlist, WishlistItem
from django.http import JsonResponse
from .ml.image_search import JewelryImageSearch
from PIL import Image
import io
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.cache import cache
import numpy as np
import logging
from .models import Product  # Make sure to import Product model
from django.http import JsonResponse, HttpResponse
import cv2
import google.generativeai as genai
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

def index(request):
    return render(request, 'index.html', {'user': request.user})

def base(request):
    return render(request, 'base.html')

from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from .models import Tbl_login, Tbl_user
from django.core.exceptions import ValidationError
from django.db import transaction
import datetime

def register(request):
    if request.method == 'POST':
        name = request.POST['name']
        dob = request.POST['dob']
        phone = request.POST['phone']
        email = request.POST['email']
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']

        # Basic server-side validations
        errors = []

        # Name validation - only letters and spaces
        if not name.replace(" ", "").isalpha():
            errors.append("Name should only contain letters and spaces.")
        
        # Date of birth validation - age 18+
        try:
            # Convert string to date object
            dob_date = datetime.strptime(dob, '%Y-%m-%d').date()
            current_date = date.today()
            age = current_date.year - dob_date.year - ((current_date.month, current_date.day) < (dob_date.month, dob_date.day))
            
            if age < 18:
                errors.append("You must be at least 18 years old.")
            elif dob_date >= current_date:
                errors.append("Please enter a valid date of birth.")
        except ValueError:
            errors.append("Invalid date format")

        # Phone number validation - 10 digits
        if not phone.isdigit() or len(phone) != 10:
            errors.append("Phone number must be exactly 10 digits.")
        
        # Email validation
        if Tbl_login.objects.filter(email=email).exists():
            errors.append("Email is already registered.")

        # Password validation
        if len(password) < 8 or not any(char.isdigit() for char in password) or not any(char.isalpha() for char in password) or not any(char in '@$!%*#?&' for char in password):
            errors.append("Password must be at least 8 characters long, include a letter, a number, and a special character.")
        
        # Confirm password validation
        if password != confirm_password:
            errors.append("Passwords do not match.")

        # Check for errors
        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, 'register.html', {'form': request.POST})

        # If no errors, save user data
        try:
            with transaction.atomic():
                # Create login entry
                login = Tbl_login.objects.create(
                    email=email,
                    password=password,
                    status=True,
                    last_login=None,
                    login_count=0
                )

                # Create user entry
                Tbl_user.objects.create(
                    name=name,
                    dob=dob_date,
                    phone=phone,
                    login=login,
                    status=True
                )

                messages.success(request, "Account created successfully. Please login.")
                return redirect('login')

        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
            return render(request, 'register.html', {'form': request.POST})

    return render(request, 'register.html')

from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from .models import Tbl_login, Tbl_user, Tbl_staff, Vendor

def login(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        try:
            login_obj = Tbl_login.objects.get(email=email, password=password)

            # Check for admin
            if email == 'admin123@gmail.com':
                request.session['user_type'] = 'admin'
                request.session['login_id'] = login_obj.login_id
                request.session['email'] = login_obj.email
                request.session.save()  # Save session
                return redirect('/adminhome/')  # Make sure this matches your URL pattern

            # Check for vendor
            try:
                vendor = Vendor.objects.get(login=login_obj)
                if vendor.status:
                    request.session['user_type'] = 'vendor'
                    request.session['login_id'] = login_obj.login_id
                    request.session['vendor_id'] = vendor.vendor_id
                    request.session['email'] = login_obj.email
                    request.session['name'] = vendor.business_name
                    request.session.save()  # Save session
                    return redirect('vendor_home')  # Ensure this matches the URL name
                else:
                    messages.error(request, 'Your vendor account is inactive')
                    return redirect('login')
            except Vendor.DoesNotExist:
                pass  # Not a vendor, continue to check other roles

            # Check for staff
            try:
                staff = Tbl_staff.objects.get(login=login_obj)
                request.session['user_type'] = 'staff'
                request.session['login_id'] = login_obj.login_id
                request.session['staff_id'] = staff.staff_id
                request.session['email'] = login_obj.email
                request.session['name'] = staff.name
                return redirect('/staffhome/')
            except Tbl_staff.DoesNotExist:
                pass

            # Check for regular user
            try:
                user = Tbl_user.objects.get(login=login_obj)
                request.session['user_type'] = 'user'
                request.session['login_id'] = login_obj.login_id
                request.session['user_id'] = user.user_id
                request.session['email'] = login_obj.email
                request.session['name'] = user.name
                return redirect('/')
            except Tbl_user.DoesNotExist:
                pass

            messages.error(request, 'Invalid user type')
            return redirect('login')

        except Tbl_login.DoesNotExist:
            messages.error(request, 'Invalid email or password')
            return redirect('login')

    return render(request, 'login.html')


def logout_view(request):
    # Clear the session to log the user out
    request.session.flush()  # This will remove all session data

    # Optionally, you can add a message to inform the user
    from django.contrib import messages
    messages.success(request, 'You have been logged out successfully.')

    # Redirect to the login page
    return redirect('/login/')

def forgot_password(request):
    if request.method == 'POST':
        form = PasswordResetRequestForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = Tbl_login.objects.get(email=email)
                # Generate a random token (you can customize this)
                reset_token = get_random_string(30)
                user.reset_token = reset_token
                user.save()
                
                # Send reset email (for now, let's print the link)
                reset_link = f"http://http://localhost:8000/reset-password/{reset_token}/"
                # Send the email
                subject = "Password Reset Request"
                message = f"Hi, please click the link below to reset your password:\n\n{reset_link}\n\nIf you did not request this, please ignore this email."
                from_email = 'jeeljpaul2025@mca.ajce.in'
                recipient_list = [email]
                
                send_mail(subject, message, from_email, recipient_list)
                
                messages.success(request, 'A password reset link has been sent to your email.')
                return redirect('/login/')
            except Tbl_login.DoesNotExist:
                messages.error(request, 'Email address not found')
    else:
        form = PasswordResetRequestForm()

    return render(request, 'password_reset_request.html', {'form': form})

def reset_password(request, token):
    try:
        user = Tbl_login.objects.get(reset_token=token)
    except Tbl_login.DoesNotExist:
        messages.error(request, 'Invalid or expired reset token')
        return redirect('/login/')
    
    if request.method == 'POST':
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        
        if password == confirm_password and len(password) >= 8:
            user.password = password  # Hash the password in a real-world scenario
            user.reset_token = ''  # Clear the reset token
            user.save()
            messages.success(request, 'Your password has been reset successfully')
            return redirect('/login/')
        else:
            messages.error(request, 'Passwords do not match or are not long enough')
    
    return render(request, 'password_reset.html')





# admin views.py--------------------------------------------------------------------------------------------
from django.utils.decorators import decorator_from_middleware
from django.middleware.cache import CacheMiddleware
from django.shortcuts import render, redirect
from django.contrib import messages

@decorator_from_middleware(CacheMiddleware)
def adminhome(request):
    # Check if user is logged in and is admin
    if 'user_type' not in request.session or request.session['user_type'] != 'admin':
        messages.error(request, 'You need to log in as an admin to access this page.')
        return redirect('login')

    # Get any pending payment requests
    payment_requests = PaymentRequest.objects.filter(status='Pending')

    print(f"Pending payment requests: {payment_requests.count()}")

    context = {
        'payment_requests': payment_requests,
    }

    return render(request, 'admin/adminhome.html', context)



from django.shortcuts import render, get_object_or_404, redirect
from .models import Product
from django.db.models import Q

# View products and filter by category
def view_products(request):
    query = request.GET.get('category', '')  # Get the category from search input
    if query:
        products = Product.objects.filter(Q(category__icontains=query))  # Search by category
    else:
        products = Product.objects.all()  # Display all products if no search query

    return render(request, 'admin/view_products.html', {'products': products})

# View product details
def product_details(request, product_id):
    product = get_object_or_404(Product, product_id=product_id)
    context = {'product': product}
    return render(request, 'admin/product_details.html', context)



from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from .models import Product  # Adjust the import based on your app structure

def toggle_product_status(request, product_id):
    if request.method == 'POST':
        # Get the product object using product_id, or return 404 if not found
        product = get_object_or_404(Product, product_id=product_id)
        
        # Get the action from the request to determine if we should activate or deactivate
        action = request.POST.get('action')

        if action == 'deactivate':
            product.is_active = False
        elif action == 'activate':
            product.is_active = True

        # Save the updated product object to the database
        product.save()

    # Redirect to the product list or any appropriate view after toggling
    return redirect(reverse('product_list'))


#//////////////////////////////////////////////////////////////////////////////////////////////////////////////////#

# from django.shortcuts import render, get_object_or_404, redirect
# from django.contrib import messages
# from .models import Product
# from .forms import ProductForm 

# def update_product(request, product_id):
#     product = get_object_or_404(Product, product_id=product_id)

#     if request.method == "POST":
#         form = ProductForm(request.POST, instance=product)
#         if form.is_valid():
#             form.save()
#             messages.success(request, 'Product updated successfully!')
#             return redirect('product_list') 
#         else:
#             messages.error(request, 'Please correct the errors below.')
#     else:
#         form = ProductForm(instance=product)

#     return render(request, 'admin/update_product.html', {'form': form, 'product': product})




# def delete_product(request, product_id):
#     product = get_object_or_404(Product, product_id=product_id)
#     if request.method == 'POST':
#         product.delete()
#         return redirect('view_products')
#     return render(request, 'admin/view_products.html')



#update a product
# def update_product(request, product_id):
#     product = get_object_or_404(Product, id=product_id)
    
#     if request.method == 'POST':
#         form = ProductForm(request.POST, request.FILES, instance=product)
#         if form.is_valid():
#             form.save()
#             return redirect('product_detail', product_id=product.id)
#     else:
#         form = ProductForm(instance=product)

#     return render(request, 'update_product.html', {'form': form, 'product': product})



#//////////////////////////////////////////////////////////////////////////////////////////////////////////////#
def view_registered_users(request):
    users = Tbl_user.objects.all()  # Fetch all users
    return render(request, 'admin/view_registered_users.html', {'users': users})


from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from .models import Tbl_user, Tbl_login

def toggle_user_status(request, user_id):
    if request.method == 'POST':
        user = get_object_or_404(Tbl_user, user_id=user_id)
        action = request.POST.get('action')

        if action == 'deactivate':
            user.status = False
            user.login.status = False
        elif action == 'activate':
            user.status = True
            user.login.status = True

        user.login.save()
        user.save()

    return redirect(reverse('view_registered_users'))

 #---------------------------------------------------------------
from django.shortcuts import render, redirect
from django.core.mail import send_mail
from django.conf import settings
from .models import Tbl_login, Tbl_staff
from .forms import StaffForm

def add_staff(request):
    if request.method == 'POST':
        form = StaffForm(request.POST)
        if form.is_valid():
            form.save()

            # After saving the staff details, send an email with the login credentials
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            name = form.cleaned_data['name']

            subject = 'Your Staff Account Details'
            message = f'Hello {name},\n\nYou have been added as a staff member.\n\nYour login details are:\nEmail: {email}\nPassword: {password}\n\nPlease login and change your password.\n\nBest regards,\nAdmin Team'

            # Send the email
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )

            return redirect('/adminhome/')  # Redirect to a view after successful staff addition
    else:
        form = StaffForm()

    return render(request, 'admin/add_staff.html', {'form': form})



def view_staff(request):
    # Fetch all staff from the database
    staff_members = Tbl_staff.objects.all()
    # Pass the staff members to the template
    return render(request, 'admin/view_staff.html', {'staff_members': staff_members})




def update_staff(request, staff_id):
    staff = get_object_or_404(Tbl_staff, staff_id=staff_id)

    if request.method == 'POST':
        form = StaffForm(request.POST)
        if form.is_valid():
            # Update login details
            login = get_object_or_404(Tbl_login, login_id=staff.login.login_id)
            login.email = form.cleaned_data['email']
            login.save()

            # Update staff details
            staff.name = form.cleaned_data['name']
            staff.role = form.cleaned_data['role']
            staff.contact_details = form.cleaned_data['contact_details']
            staff.save()

            return redirect('view_staff')  # Redirect to the staff view page
    else:
        form = StaffForm(initial={
            'name': staff.name,
            'email': staff.login.email,
            'role': staff.role,
            'contact_details': staff.contact_details,
        })

    return render(request, 'admin/update_staff.html', {'form': form, 'staff': staff})


def delete_staff(request, staff_id):
    staff = get_object_or_404(Tbl_staff, id=staff_id)
    
    if request.method == 'POST':
        # Delete associated login details
        login = get_object_or_404(Tbl_login, id=staff.login.id)
        login.delete()  # Delete the login entry
        staff.delete()  # Delete the staff entry
        return redirect('view_staff')  # Redirect to the staff view page

    return render(request, 'confirm_delete.html', {'staff': staff})

def staffhome(request):
    if 'login_id' not in request.session:
        return redirect('login')
    
    login_id = request.session['login_id']
    staff = get_object_or_404(Tbl_staff, login_id=login_id)
    
    context = {
        'name': staff.name,
        'role': staff.role
    }
    
    if staff.role == 'Sales':
        # Get all try-at-home requests (both pending and confirmed)
        try_at_home_requests = Booking.objects.filter(
            product__try_at_home=True
        ).select_related('user', 'product').order_by('-booking_date')
        
        # Get all orders except cancelled ones
        orders = Order.objects.exclude(
            status='Cancelled'
        ).select_related('user', 'billing').order_by('-order_date')
        
        context.update({
            'try_at_home_requests': try_at_home_requests,
            'orders': orders
        })
    
    elif staff.role == 'Delivery':
        # Get all orders including delivered ones
        assigned_orders = Order.objects.filter(
            status__in=['Confirmed', 'Shipped', 'Out for Delivery', 'Delivered']
        ).select_related('user', 'billing').order_by('-order_date')
        
        context.update({
            'assigned_orders': assigned_orders
        })
    
    elif staff.role == 'Try at home':
        # Get pending try-at-home bookings
        bookings = Booking.objects.filter(
            status='confirmed',
            product__try_at_home=True
        ).select_related('user', 'product').order_by('-booking_date')
        
        context.update({
            'bookings': bookings
        })
    
    return render(request, 'staff/staffhome.html', context)

def update_order_status(request, order_id):
    if request.method == 'POST':
        staff = get_object_or_404(Tbl_staff, login_id=request.session.get('login_id'))
        if staff.role != 'Sales':
            messages.error(request, 'Unauthorized action')
            return redirect('staffhome')
            
        order = get_object_or_404(Order, id=order_id)
        new_status = request.POST.get('status')
        current_time = timezone.now()
        
        # Update status and corresponding timestamps
        order.status = new_status
        if new_status == 'Confirmed':
            order.confirmed_date = current_time
        elif new_status == 'Shipped':
            order.shipped_date = current_time
        elif new_status == 'Out for Delivery':
            order.out_for_delivery_date = current_time
        
        order.save()
        
        # Send email notification to customer
        try:
            subject = f'Order #{order.id} Status Update'
            message = f'''
            Dear {order.user.name},
            
            Your order status has been updated.
            
            Order Details:
            Order ID: {order.id}
            New Status: {new_status}
            Updated on: {current_time.strftime('%Y-%m-%d %H:%M')}
            
            Track your order in the order details section of your account.
            '''
            
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [order.user.login.email],
                fail_silently=True
            )
        except Exception as e:
            messages.warning(request, f'Email notification failed: {str(e)}')
        
        messages.success(request, f'Order status updated to {new_status}')
        
    return redirect('staffhome')

def mark_delivery_complete(request, order_id):
    if request.method == 'POST':
        staff = get_object_or_404(Tbl_staff, login_id=request.session.get('login_id'))
        if staff.role != 'Delivery':
            messages.error(request, 'Unauthorized action')
            return redirect('staffhome')
            
        order = get_object_or_404(Order, id=order_id)
        current_time = timezone.now()
        
        # Update order status and timestamp
        order.status = 'Delivered'
        order.delivery_date = current_time
        order.save()
        
        # Send delivery confirmation email
        try:
            subject = f'Order #{order.id} Delivered'
            message = f'''
            Dear {order.user.name},
            
            Your order has been successfully delivered.
            
            Order Details:
            Order ID: {order.id}
            Delivery Date: {current_time.strftime('%Y-%m-%d %H:%M')}
            
            Thank you for shopping with us!
            '''
            
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [order.user.login.email],
                fail_silently=True
            )
        except Exception as e:
            messages.warning(request, f'Email notification failed: {str(e)}')
        
        messages.success(request, 'Delivery marked as complete')
        
    return redirect('staffhome')

def handle_try_at_home_request(request, booking_id):
    if request.method == 'POST':
        staff = get_object_or_404(Tbl_staff, login_id=request.session.get('login_id'))
        if staff.role not in ['Sales', 'Try at home']:
            messages.error(request, 'Unauthorized action')
            return redirect('staffhome')
            
        booking = get_object_or_404(Booking, booking_id=booking_id)
        action = request.POST.get('action')
        
        if action == 'accept':
            booking.status = 'confirmed'
            messages.success(request, 'Booking accepted successfully')
        elif action == 'reject':
            booking.status = 'cancelled'
            messages.success(request, 'Booking rejected')
        
        booking.save()
        
        # Send email notification
        try:
            subject = f'Try at Home Booking #{booking.booking_id} Update'
            message = f'Your try at home booking for {booking.product.product_name} has been {booking.status}.'
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [booking.user.login.email],
                fail_silently=True
            )
        except Exception as e:
            messages.warning(request, f'Email notification failed: {str(e)}')
        
    return redirect('staffhome')

# Helper functions for email notifications
def send_order_status_email(order):
    subject = f'Order #{order.id} Status Update'
    message = f'Your order status has been updated to: {order.status}'
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [order.user.login.email],
        fail_silently=True
    )

def send_delivery_confirmation_email(order):
    subject = f'Order #{order.id} Delivered'
    message = 'Your order has been delivered successfully.'
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [order.user.login.email],
        fail_silently=True
    )

def send_booking_status_email(booking):
    subject = f'Try at Home Booking #{booking.booking_id} Update'
    message = f'Your booking status has been updated to: {booking.status}'
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [booking.user.login.email],
        fail_silently=True
    )

#staff views.py-------------------------------------------------------------------------------------------------

# from django.shortcuts import render, redirect
# from .models import Product
# from .forms import ProductForm
 
# def add_p(request):
#     if request.method == "POST":
#         form = ProductForm(request.POST, request.FILES)
#         if form.is_valid():
#             form.save()
#             return redirect('product_list')  
#     else:
#         form = ProductForm()
#     categories = Category.objects.all() 
#     return render(request, 'admin/add_p.html', {'form': form, 'categories': categories})



# def add_product(request):
#     if request.method == "POST":
#         form = ProductForm(request.POST, request.FILES)
#         if form.is_valid():
#             form.save()
#             return redirect('product_list')  
#     else:
#         form = ProductForm()
#     return render(request, 'admin/add_product.html', {'form': form})



from django.shortcuts import render
from .models import Product

def product_list(request):
    products = Product.objects.all()  # Fetch all products
    return render(request, 'admin/product_list.html', {'products': products})



# from django.shortcuts import get_object_or_404

# def update_p(request, product_id):
#     product = get_object_or_404(Product, pk=product_id)
    
#     if request.method == "POST":
#         form = ProductForm(request.POST, request.FILES, instance=product)
#         if form.is_valid():
#             form.save()
#             return redirect('product_list')  
#     else:
#         form = ProductForm(instance=product)

#     return render(request, 'admin/update_p.html', {'form': form, 'product': product})


# -----------------------------------------------------------------------------------------------------

#userpage

def product(request): 
    return render(request, 'user/product.html')


from django.shortcuts import render
from .models import Product, Stonetype, Metaltype, Category
from .models import ProductAttribute
def ring_lists(request):
    # Get all possible filter values from the database
    ring_sizes = ProductAttribute.objects.filter(attribute_name='Ringsize').values_list('attribute_value', flat=True).distinct()
    ring_types = ProductAttribute.objects.filter(attribute_name='Ringtype').values_list('attribute_value', flat=True).distinct()
    gemstones = Stonetype.objects.all()
    materials = Metaltype.objects.all()

    # Retrieve selected filters from the request
    selected_ring_sizes = request.GET.getlist('ring_size')
    selected_ring_types = request.GET.getlist('ring_type')
    selected_gemstones = request.GET.getlist('gemstone')
    selected_materials = request.GET.getlist('metal_type')

    # Initialize the queryset to fetch all ring products initially
    category_ring = Category.objects.get(name='Ring')
    rings = Product.objects.filter(category=category_ring, is_active=True)

    # Apply filtering based on selected values
    if selected_ring_sizes:
        rings = rings.filter(attributes__attribute_name='Ringsize', attributes__attribute_value__in=selected_ring_sizes)
    if selected_ring_types:
        rings = rings.filter(attributes__attribute_name='Ringtype', attributes__attribute_value__in=selected_ring_types)
    if selected_gemstones:
        rings = rings.filter(stonetype__name__in=selected_gemstones)
    if selected_materials:
        rings = rings.filter(metaltype__name__in=selected_materials)

    context = {
        'rings': rings,
        'ring_sizes': ring_sizes,
        'ring_types': ring_types,
        'gemstones': gemstones,
        'materials': materials,
        'selected_ring_sizes': selected_ring_sizes,
        'selected_ring_types': selected_ring_types,
        'selected_gemstones': selected_gemstones,
        'selected_materials': selected_materials,
    }

    return render(request, 'user/ring_list.html', context)







from django.shortcuts import render, get_object_or_404
from .models import Product, Metaltype, Stonetype, Category
from .models import ProductAttribute
def ring_detail(request, product_id):
    # Get the specific product by its ID, along with related Metaltype, Stonetype, and Category
    product = get_object_or_404(Product.objects.select_related('metaltype', 'stonetype', 'category'), product_id=product_id)
  

    # Fetch the product's attributes (e.g., ring size, ring type, etc.)
    product_attributes = ProductAttribute.objects.filter(product=product)

    # Fetch the category attributes for the specific product category (if any)
    category_attributes = product.category.attributes.all() if product.category else []

    context = {
        'product': product,
        'product_attributes': product_attributes,
        'category_attributes': category_attributes,
        'metaltype': product.metaltype,
        'stonetype': product.stonetype,
    }

    return render(request, 'user/ring_detail.html', context)


def earring_list(request):
    # Get all possible filter values from the database
    gemstones = Stonetype.objects.all()
    materials = Metaltype.objects.all()
    earring_styles = ProductAttribute.objects.filter(attribute_name='Earring Style').values_list('attribute_value', flat=True).distinct()
    shop_for_options = Product.objects.values_list('gender', flat=True).distinct()

    # Retrieve selected filters from the request
    selected_gemstones = request.GET.getlist('gemstone')
    selected_materials = request.GET.getlist('metal_type')
    selected_earring_styles = request.GET.getlist('earringstyle')
    selected_shop_for = request.GET.getlist('shop_for')

    # Initialize the queryset to fetch all products initially
    category_earring = Category.objects.get(name='Earring')
    earrings = Product.objects.filter(category=category_earring, is_active=True)


    # Apply filtering based on selected values
    if selected_shop_for:
        earrings = earrings.filter(gender__in=selected_shop_for)
    if selected_gemstones:
        earrings = earrings.filter(stonetype__name__in=selected_gemstones)
    if selected_materials:
        earrings = earrings.filter(metaltype__name__in=selected_materials)
    if selected_earring_styles:
        earrings = earrings.filter(attributes_attribute_name='Earring Style', attributes__attribute_value__in=selected_earring_styles)

    context = {
        'earrings': earrings,
        'gemstones': gemstones,
        'materials': materials,
        'earring_styles': earring_styles,
        'shop_for_options': shop_for_options,
        'selected_gemstones': selected_gemstones,
        'selected_materials': selected_materials,
        'selected_earring_styles': selected_earring_styles,
        'selected_shop_for': selected_shop_for,
    }

    return render(request, 'user/earring_list.html', context)



def earring_detail(request, product_id):
    # Get the specific product by its ID, along with related Metaltype, Stonetype, and Category
    product = get_object_or_404(Product.objects.select_related('metaltype', 'stonetype', 'category'), product_id=product_id)
  

    # Fetch the product's attributes (e.g., ring size, ring type, etc.)
    product_attributes = ProductAttribute.objects.filter(product=product)

    # Fetch the category attributes for the specific product category (if any)
    category_attributes = product.category.attributes.all() if product.category else []

    context = {
        'product': product,
        'product_attributes': product_attributes,
        'category_attributes': category_attributes,
        'metaltype': product.metaltype,
        'stonetype': product.stonetype,
    }

    return render(request, 'user/earring_detail.html', context)


def bracelet_lists(request):
    # Get all possible filter values from the database
    bracelet_styles = ProductAttribute.objects.filter(attribute_name='Bracelet Style').values_list('attribute_value', flat=True).distinct()
    gemstones = Stonetype.objects.all()
    materials = Metaltype.objects.all()
    shop_for_options = Product.objects.values_list('gender', flat=True).distinct()

    # Retrieve selected filters from the request
    selected_styles = request.GET.getlist('bracelet_style')
    selected_shop_for = request.GET.getlist('shop_for')
    selected_gemstones = request.GET.getlist('gemstone')
    selected_materials = request.GET.getlist('metal_type')

    # Initialize the queryset to fetch all bracelet products initially
    category_bracelet = Category.objects.get(name='Bracelets')
    bracelets = Product.objects.filter(category=category_bracelet, is_active=True)

    # Apply filtering based on selected values
    if selected_styles:
        bracelets = bracelets.filter(attributes__attribute_name='Bracelet Style', attributes__attribute_value__in=selected_styles)
    if selected_shop_for:
        bracelets = bracelets.filter(gender__in=selected_shop_for)
    if selected_gemstones:
        bracelets = bracelets.filter(stonetype__name__in=selected_gemstones)
    if selected_materials:
        bracelets = bracelets.filter(metaltype__name__in=selected_materials)

    context = {
        'bracelets': bracelets,
        'bracelet_styles': bracelet_styles,
        'shop_for_options': shop_for_options,
        'gemstones': gemstones,
        'materials': materials,
        'selected_styles': selected_styles,
        'selected_shop_for': selected_shop_for,
        'selected_gemstones': selected_gemstones,
        'selected_materials': selected_materials,
    }

    return render(request, 'user/bracelet.html', context)



def bracelet_detail(request, product_id):
    # Get the specific product by its ID, along with related Metaltype, Stonetype, and Category
    product = get_object_or_404(Product.objects.select_related('metaltype', 'stonetype', 'category'), product_id=product_id)
  

    # Fetch the product's attributes (e.g., ring size, ring type, etc.)
    product_attributes = ProductAttribute.objects.filter(product=product)

    # Fetch the category attributes for the specific product category (if any)
    category_attributes = product.category.attributes.all() if product.category else []

    context = {
        'product': product,
        'product_attributes': product_attributes,
        'category_attributes': category_attributes,
        'metaltype': product.metaltype,
        'stonetype': product.stonetype,
    }

    return render(request, 'user/bracelet_details.html', context)

#----------------------------------------------------------------------------------------------------------------------------------------------

from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from .models import Product, Cart, CartItem
from .models import Tbl_user

def add_to_cart(request, product_id):
    if 'login_id' in request.session:
        product = get_object_or_404(Product, product_id=product_id)
        user_id = request.session['login_id']
        print(user_id)
        if request.method == 'POST':
            # Check if the user is authenticated
            # if request.user.is_authenticated:
                # user = get_object_or_404(Tbl_user, user_id=user_id)
                # print(user)
                user_cart, created = Cart.objects.get_or_create(login=user_id)
                print("kk")
                # Check if the cart item already exists
                cart_item, item_created = CartItem.objects.get_or_create(cart=user_cart, product=product)

                if not item_created:
                    # If the item is already in the cart, increase the quantity
                    cart_item.quantity += 1
                    cart_item.save()

                return JsonResponse({'success': True, 'message': f'{product.product_name} added to cart successfully!'})
            
            # else:
            #     # Handle cart for non-authenticated users using session
            #     cart = request.session.get('cart', {})

            #     # Check if the product is already in the cart
            #     if str(product_id) in cart:
            #         cart[str(product_id)]['quantity'] += 1
            #     else:
            #         cart[str(product_id)] = {
            #             'product_id': product_id,
            #             'product_name': product.product_name,
            #             'quantity': 1,
            #             'price': str(product.price)  # Convert to string for session compatibility
            #         }

            #     # Save the updated cart in the session
            #     request.session['cart'] = cart
            #     return JsonResponse({'success': True, 'message': f'{product.product_name} added to session cart successfully!'})

        return JsonResponse({'success': False, 'message': 'Invalid request.'})
    else:
        return redirect('login')

from django.shortcuts import render, redirect
from django.http import JsonResponse
from .models import Cart, CartItem, Product

def view_cart(request):
    # Check if the user is logged in
    if 'login_id' not in request.session:
        return redirect('login')  # Redirect to login page if the user is not logged in

    user_id = request.session['login_id']

    # Fetch the user's cart using the login_id stored in the session
    try:
        user_cart = Cart.objects.get(login=user_id)
        cart_items = CartItem.objects.filter(cart=user_cart, status=True).select_related('product')
    except Cart.DoesNotExist:
        # If the cart does not exist, initialize an empty list for cart items
        cart_items = []

    # Calculate the total price of all items in the cart
    total_price = sum(item.product.price * item.quantity for item in cart_items)

    context = {
        'cart_items': cart_items,
        'total_price': total_price,
    }

    return render(request, 'user/view_cart.html', context)


def update_cart_quantity(request):
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        product_id = request.POST.get('product_id')
        change = int(request.POST.get('change'))

        try:
            user_id = request.session['login_id']
            user_cart = Cart.objects.get(login=user_id)
            cart_item = CartItem.objects.get(cart=user_cart, product_id=product_id)

            # Update the quantity
            cart_item.quantity += change
            if cart_item.quantity <= 0:
                cart_item.delete()
            else:
                cart_item.save()

            # Calculate the updated total price for the cart item and the cart
            item_total_price = cart_item.product.price * cart_item.quantity
            total_price = sum(item.product.price * item.quantity for item in CartItem.objects.filter(cart=user_cart))

            return JsonResponse({
                'new_quantity': cart_item.quantity,
                'item_total_price': item_total_price,
                'new_total_price': total_price,
            })

        except (Cart.DoesNotExist, CartItem.DoesNotExist):
            return JsonResponse({'error': 'Cart or CartItem not found.'}, status=404)

    return JsonResponse({'error': 'Invalid request.'}, status=400)



def remove_item_from_cart(request):
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        product_id = request.POST.get('product_id')

        try:
            user_id = request.session['login_id']
            user_cart = Cart.objects.get(login=user_id)
            cart_item = CartItem.objects.get(cart=user_cart, product_id=product_id)

            # Remove the item from the cart
            cart_item.delete()

            # Recalculate the total price of the cart
            total_price = sum(item.product.price * item.quantity for item in CartItem.objects.filter(cart=user_cart))

            return JsonResponse({
                'new_total_price': total_price,
            })

        except (Cart.DoesNotExist, CartItem.DoesNotExist):
            return JsonResponse({'error': 'Cart or CartItem not found.'}, status=404)

    return JsonResponse({'error': 'Invalid request.'}, status=400)


from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from .models import Product, Wishlist, WishlistItem, Tbl_user

def add_to_wishlist(request, product_id):
    if 'login_id' in request.session:
        product = get_object_or_404(Product, product_id=product_id)
        user_id = request.session['login_id']

        user_instance = get_object_or_404(Tbl_login, login_id=user_id)
        
        if request.method == 'POST':
            # Get or create a wishlist for the user
            user_wishlist, created = Wishlist.objects.get_or_create(login=user_instance)
            # Check if the product is already in the wishlist
            wishlist_item, item_created = WishlistItem.objects.get_or_create(wishlist=user_wishlist, product=product)
            if not item_created:
                return JsonResponse({'success': False, 'message': f'{product.product_name} is already in your wishlist!'})

            return JsonResponse({'success': True, 'message': f'{product.product_name} added to your wishlist successfully!'})

        return JsonResponse({'success': False, 'message': 'Invalid request.'})
    else:
        return redirect('login')

def view_wishlist(request):
    if 'login_id' in request.session:
        user_id = request.session['login_id']
        user_instance = get_object_or_404(Tbl_login, login_id=user_id)

        # Get the user's wishlist
        user_wishlist = Wishlist.objects.filter(login=user_instance).first()
        wishlist_items = WishlistItem.objects.filter(wishlist=user_wishlist) if user_wishlist else []

        return render(request, 'user/wishlist.html', {'wishlist_items': wishlist_items})
    else:
        return redirect('login')

def remove_from_wishlist(request, item_id):
    if 'login_id' in request.session:
        wishlist_item = get_object_or_404(WishlistItem, id=item_id)
        wishlist_item.delete()
        return JsonResponse({'success': True, 'message': 'Item removed from your wishlist.'})
    else:
        return JsonResponse({'success': False, 'message': 'You need to be logged in to perform this action.'})


#///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
#adminpage
# from django.shortcuts import render, redirect, get_object_or_404
# from .models import Category, CategoryAttribute

# def add_category(request):
#     if request.method == 'POST':
#         category_name = request.POST.get('category_name')
#         attribute_names = request.POST.getlist('attribute_names')
#         attribute_datatypes = request.POST.getlist('attribute_datatypes')

#         existing_category_id = request.POST.get('existing_category')

#         if existing_category_id:
#             category = get_object_or_404(Category, id=existing_category_id)
#         elif category_name:
            
#             category = Category.objects.create(name=category_name)

#         if attribute_names and attribute_datatypes:
           
#             for name, datatype in zip(attribute_names, attribute_datatypes):
#                 if name:  
#                     CategoryAttribute.objects.create(category=category, name=name, datatype=datatype)

#         return redirect('add_category')  

    
#     categories = Category.objects.all()

#     context = {
#         'categories': categories
#     }
#     return render(request, 'admin/add_category.html', context)
from django.shortcuts import render, redirect
from .models import Category

def add_category(request):
    error_message = None

    if request.method == 'POST':
        category_name = request.POST.get('category_name')
        
        if not category_name:
            error_message = "Category name cannot be empty."
        elif Category.objects.filter(name__iexact=category_name).exists():
            error_message = "This category already exists in the database."
        else:
            # Create a new Category if it doesn't already exist
            Category.objects.create(name=category_name)
            return redirect('view_categories')  # Redirect after successful creation

    return render(request, 'admin/add_category.html', {'error_message': error_message})



def view_categories(request):
    categories = Category.objects.all().prefetch_related('attributes')
    return render(request, 'admin/view_categories.html', {'categories': categories})


def add_attribute_to_category(request, category_id):
    category = get_object_or_404(Category, pk=category_id)

    if request.method == 'POST':
        attribute_name = request.POST.get('attribute_name')

        if attribute_name:
            # Add the new attribute to the existing category
            CategoryAttribute.objects.create(category=category, name=attribute_name)
            return redirect('view_categories')  # Redirect to category list after adding attribute

    return render(request, 'admin/add_attribute.html', {'category': category})



#-----------------------------------------------------------------------------------------------------------------------------------------

  
# from django.shortcuts import render, redirect
# from .models import Metaltype
# from django.http import HttpResponse

# def add_metaltype(request):
#     if request.method == 'POST':
#         name = request.POST.get('name')
#         if name:
#             Metaltype.objects.create(name=name)
#             return redirect('add_metaltype') 
#         else:
#             return HttpResponse("Name field cannot be empty.")

#     return render(request, 'admin/add_metaltype.html')

# views.py
from django.shortcuts import render
from .models import Metaltype

def view_metaltypes(request):
    metaltypes = Metaltype.objects.all()
    return render(request, 'admin/view_metaltype.html', {'metaltypes': metaltypes})


from django.shortcuts import render, redirect
from .models import Metaltype

def add_metaltype(request):
    error_message = None

    if request.method == 'POST':
        name = request.POST.get('name')
        
        if not name:
            error_message = "Name field cannot be empty."
        elif Metaltype.objects.filter(name__iexact=name).exists():
            error_message = "This metal type already exists in the database."
        else:
            Metaltype.objects.create(name=name)
            return redirect('view_metaltypes')  # Redirect after successful creation

    # Fetch all metal types to display in the template
    # metaltypes = Metaltype.objects.all()

    return render(request, 'admin/add_metaltype.html', {'error_message': error_message})






#-----------------------------------------------------------------------------------------------------------------


# views.py
from django.shortcuts import render
from .models import Stonetype

def view_stonetypes(request):
    stonetypes = Stonetype.objects.all()
    return render(request, 'admin/view_stonetypes.html', {'stonetypes': stonetypes})




from django.shortcuts import render, redirect
from .models import Stonetype

def add_stonetype(request):
    error_message = None

    if request.method == 'POST':
        name = request.POST.get('name')
        
        if not name:
            error_message = "Name field cannot be empty."
        elif Stonetype.objects.filter(name__iexact=name).exists():
            error_message = "This stone type already exists in the database."
        else:
            Stonetype.objects.create(name=name)
            return redirect('view_stonetypes')  # Redirect after successful creation

    return render(request, 'admin/add_stonetype.html', {'error_message': error_message})



# from django.shortcuts import render, redirect
# from .models import Metaltype
# from django.http import HttpResponse

# def add_stonetype(request):
#     if request.method == 'POST':
#         name = request.POST.get('name')
#         if name:
#             Stonetype.objects.create(name=name)
#             return redirect('add_stonetype')  
#         else:
#             return HttpResponse("Name field cannot be empty.")

#     return render(request, 'admin/add_stonetype.html')




#--------------------------------------------------------------------------------------------------------------------------------------------
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Product, Category, Metaltype, Stonetype, CategoryAttribute
from .models import ProductAttribute

def add_pro(request):
    if request.method == 'POST':
        product_name = request.POST.get('product_name')
        category_id = request.POST.get('id_category')
        product_description = request.POST.get('product_description')
        price = request.POST.get('price')
        stock_quantity = request.POST.get('stock_quantity')
        weight = request.POST.get('weight')
        metaltype_id = request.POST.get('metaltype', None)
        stonetype_id = request.POST.get('stonetype', None)
        gender = request.POST.get('gender', 'Unisex')
        image = request.FILES.get('image')
        vendor_id = request.POST.get('vendor')  # Get the selected vendor ID

        # Handling delivery options (checkboxes)
        delivery_options = request.POST.getlist('delivery_options[]')
        home_delivery = 'Home Delivery' in delivery_options
        store_pickup = 'Store Pickup' in delivery_options
        try_at_home = 'Try at home' in delivery_options
        
        # Handling bestselling checkbox
        bestseller = request.POST.get('bestseller', 'off') == 'Yes'  # Checkbox for bestselling item

        # Validate the inputs
        try:
            price = float(price)
            stock_quantity = int(stock_quantity)
            weight = float(weight)
        except ValueError:
            messages.error(request, "Invalid input values.")
            return redirect('add_pro')

        if not (100 <= price <= 10000000):
            messages.error(request, "Price must be between 100 and 10,000,000.")
            return redirect('add_pro')

        if not (0 <= stock_quantity <= 50):
            messages.error(request, "Stock quantity must be between 0 and 50.")
            return redirect('add_pro')

        if not (1 <= weight <= 100):
            messages.error(request, "Weight must be between 1 and 100 grams.")
            return redirect('add_pro')

        # Check if a product with the same name and weight already exists
        if Product.objects.filter(product_name=product_name, weight=weight).exists():
            messages.error(request, "A product with this name and weight already exists.")
            return redirect('add_pro')

        # Create the product instance and save it
        try:
            vendor = Vendor.objects.get(vendor_id=vendor_id)  # Fetch the vendor
            product = Product(
                product_name=product_name,
                category=category,
                product_description=product_description,
                price=price,
                stock_quantity=stock_quantity,
                weight=weight,
                gender=gender,
                images=image,
                metaltype=metaltype,
                stonetype=stonetype,
                home_delivery=home_delivery,
                store_pickup=store_pickup,
                try_at_home=try_at_home,
                bestselling=bestseller,
                vendor=vendor  # Set the vendor for the product
            )
            product.save()
            messages.success(request, "Product added successfully!")

            # Now handle product attributes
            attributes_data = request.POST.getlist('attributes')
            for attribute_id in attributes_data:
                if attribute_id:  # Only proceed if the ID is not empty
                    try:
                        # Debug print statement to check the attribute ID being processed
                        print(f"Processing attribute ID: {attribute_id}")

                        # Fetch the attribute name from CategoryAttribute using the attribute_id
                        category_attribute = CategoryAttribute.objects.get(id=attribute_id)
                        attribute_name = category_attribute.name

                        # Fetch the attribute value from the form using the attribute ID
                        attribute_value = request.POST.get(f'attribute_{attribute_id}', '')
                        print(f"Processing attribute {attribute_name} with value: {attribute_value}")

                        # Check if attribute value is provided
                        if attribute_value:
                            # Create a ProductAttribute object with the product, attribute name, and value
                            ProductAttribute.objects.create(
                                product=product,
                                attribute_name=attribute_name,
                                attribute_value=attribute_value
                            )
                        else:
                            messages.warning(request, f"Attribute value for {attribute_name} is missing. Skipping.")
                    except CategoryAttribute.DoesNotExist:
                        messages.error(request, f"Attribute with ID {attribute_id} does not exist.")
                    except Exception as e:
                        messages.error(request, f"Error saving attribute: {str(e)}")

            return redirect('add_pro')  # Redirect after success

        except (Metaltype.DoesNotExist, Stonetype.DoesNotExist) as e:
            messages.error(request, f"Error: {str(e)}")
            return redirect('add_pro')

    # GET request to render the page
    categories = Category.objects.all()
    metaltypes = Metaltype.objects.all()
    stonetypes = Stonetype.objects.all()
    vendors = Vendor.objects.all()  # Fetch all vendors

    context = {
        'categories': categories,
        'metaltypes': metaltypes,
        'stonetypes': stonetypes,
        'vendors': vendors,  # Pass the list of vendors to the template

    }
    return render(request, 'admin/add_p.html', context)


def update_pro(request, product_id):
    product = get_object_or_404(Product, product_id=product_id)
    vendors = Vendor.objects.all()  # Fetch all vendors

    if request.method == 'POST':
        product_name = request.POST.get('product_name')
        category_id = request.POST.get('id_category')
        product_description = request.POST.get('product_description')
        price = request.POST.get('price')
        stock_quantity = request.POST.get('stock_quantity')
        weight = request.POST.get('weight')
        metaltype_id = request.POST.get('metaltype', None)
        stonetype_id = request.POST.get('stonetype', None)
        gender = request.POST.get('gender', 'Unisex')
        image = request.FILES.get('image', product.images)  # Keep existing image if not changed
        vendor_id = request.POST.get('vendor')  # Get the selected vendor ID



        # Handling delivery options (checkboxes)
        delivery_options = request.POST.getlist('delivery_options[]')
        home_delivery = 'Home Delivery' in delivery_options
        store_pickup = 'Store Pickup' in delivery_options
        try_at_home = 'Try at home' in delivery_options

        # Handling bestselling checkbox
        bestseller = request.POST.get('bestseller', 'off') == 'Yes'

        # Validate the inputs
        try:
            price = float(price)
            stock_quantity = int(stock_quantity)
            weight = float(weight)
        except ValueError:
            messages.error(request, "Invalid input values.")
            return redirect('update_pro', product_id=product.product_id)

        if not (100 <= price <= 10000000):
            messages.error(request, "Price must be between 100 and 10,000,000.")
            return redirect('update_pro', product_id=product.product_id)

        if not (0 <= stock_quantity <= 50):
            messages.error(request, "Stock quantity must be between 0 and 50.")
            return redirect('update_pro', product_id=product.product_id)

        if not (1 <= weight <= 100):
            messages.error(request, "Weight must be between 1 and 100 grams.")
            return redirect('update_pro', product_id=product.product_id)

        try:
            category = Category.objects.get(category_id=category_id)
            metaltype = Metaltype.objects.get(metaltype_id=metaltype_id) if metaltype_id else None
            stonetype = Stonetype.objects.get(stonetype_id=stonetype_id) if stonetype_id else None
            # Fetch the vendor instance
            vendor = Vendor.objects.get(vendor_id=vendor_id)  # Ensure this line is present

            # Update the product instance with new details
            product.product_name = product_name
            product.category = category
            product.product_description = product_description
            product.price = price
            product.stock_quantity = stock_quantity
            product.weight = weight
            product.gender = gender
            product.images = image
            product.metaltype = metaltype
            product.stonetype = stonetype
            product.home_delivery = home_delivery
            product.store_pickup = store_pickup
            product.try_at_home = try_at_home
            product.bestselling = bestseller
            product.vendor = vendor  # Set the vendor for the product


            product.save()
            messages.success(request, "Product updated successfully!")

            # Handle product attributes
            attributes_data = request.POST.getlist('attributes')
            for attribute_id in attributes_data:
                if attribute_id:
                    try:
                        category_attribute = CategoryAttribute.objects.get(id=attribute_id)
                        attribute_name = category_attribute.name
                        attribute_value = request.POST.get(f'attribute_{attribute_id}', '')

                        # Update or create the product attribute
                        if attribute_value:
                            product_attribute, created = ProductAttribute.objects.update_or_create(
                                product=product,
                                attribute_name=attribute_name,
                                defaults={'attribute_value': attribute_value}
                            )
                    except CategoryAttribute.DoesNotExist:
                        messages.error(request, f"Attribute with ID {attribute_id} does not exist.")
                    except Exception as e:
                        messages.error(request, f"Error updating attribute: {str(e)}")

            return redirect('product_list')

        except (Category.DoesNotExist, Metaltype.DoesNotExist, Stonetype.DoesNotExist) as e:
            messages.error(request, f"Error: {str(e)}")
            return redirect('update_pro', product_id=product.product_id)

    # GET request to render the page with existing product details
    categories = Category.objects.all()
    metaltypes = Metaltype.objects.all()
    stonetypes = Stonetype.objects.all()
    product_attributes = ProductAttribute.objects.filter(product=product)

    context = {
        'product': product,
        'categories': categories,
        'metaltypes': metaltypes,
        'stonetypes': stonetypes,
        'product_attributes': product_attributes,
        'vendors': vendors,  # Pass the list of vendors to the template
    }
    return render(request, 'admin/update_p.html', context)



from django.http import JsonResponse
from .models import CategoryAttribute
from django.http import JsonResponse
from .models import Category, CategoryAttribute

def get_category_attributes(request, category_id):
    print("hello")
    try:
        # Get the category by its ID
        category = Category.objects.get(category_id=category_id)

        # Retrieve attributes associated with this category
        attributes = CategoryAttribute.objects.filter(category=category)

        # Prepare the response data in the expected format
        response_data = {
            'attributes': [{'id': attribute.id, 'name': attribute.name} for attribute in attributes]
        }

        return JsonResponse(response_data, safe=False)
    except Category.DoesNotExist:
        # If the category doesn't exist, return an empty list with a 404 status code
        return JsonResponse({'error': 'Category not found'}, status=404)
    except Exception as e:
        # Handle other errors
        return JsonResponse({'error': str(e)}, status=500)



from django.shortcuts import render
from .models import Product, Category, Metaltype, Stonetype

def product_list(request):
    # Get all possible filter values from the database
    products = Product.objects.all()
    categories = Category.objects.all()

    # Retrieve selected filters from the request
    selected_categories = request.GET.getlist('category')
    selected_price = request.GET.get('price')
    selected_weight = request.GET.get('weight')

    # Apply filtering based on selected categories
    if selected_categories and any(selected_categories):
        products = products.filter(category___in=selected_categories)
    # Apply exact price filtering if specified
    if selected_price:
        products = products.filter(price=selected_price)

    # Apply exact weight filtering if specified
    if selected_weight:
        products = products.filter(weight=selected_weight)

    context = {
        'products': products,
        'categories': categories,
        'selected_categories': selected_categories,
        'selected_price': selected_price,
        'selected_weight': selected_weight,
    }

    return render(request, 'admin/product_list.html', context)


# def all_products(request):
#     categories = Category.objects.all()
#     materials = Metaltype.objects.all()
#     gemstones = Stonetype.objects.all()
#     ring_sizes = ProductAttribute.objects.filter(attribute_name='Ringsize').values_list('attribute_value', flat=True).distinct()
#     ring_types = ProductAttribute.objects.filter(attribute_name='Ringtype').values_list('attribute_value', flat=True).distinct()
#     earring_styles = ProductAttribute.objects.filter(attribute_name='Earring Style').values_list('attribute_value', flat=True).distinct()
#     shop_for_options = Product.objects.values_list('gender', flat=True).distinct()
#     bracelet_styles = ProductAttribute.objects.filter(attribute_name='Bracelet Style').values_list('attribute_value', flat=True).distinct()


#     selected_ring_sizes = request.GET.getlist('ring_size')
#     selected_ring_types = request.GET.getlist('ring_type')
#     selected_earring_styles = request.GET.getlist('earringstyle')
#     selected_shop_for = request.GET.getlist('shop_for')
#     selected_styles = request.GET.getlist('bracelet_style')
#     selected_gemstones = request.GET.getlist('gemstone')
#     selected_materials = request.GET.getlist('metal_type')
#     selected_category =  request.GET.getlist('category')
#     try_at_home_filter = request.GET.get('try_at_home')

#     category_earring = Category.objects.get(name='Earring')
#     category_ring = Category.objects.get(name='Ring')
#     category_bracelets = Category.objects.get(name='Bracelets')

#     products = Product.objects.filter(is_active=True)
#     rings = Product.objects.filter(category=category_ring, is_active=True)
#     earrings = Product.objects.filter(category=category_earring, is_active=True)
#     bracelets = Product.objects.filter(category=category_bracelets, is_active=True)

#     if selected_ring_sizes:
#         rings = rings.filter(attributes__attribute_name='Ringsize', attributes__attribute_value__in=selected_ring_sizes)
#     if selected_ring_types:
#         rings = rings.filter(attributes__attribute_name='Ringtype', attributes__attribute_value__in=selected_ring_types)
#     if selected_earring_styles:
#         earrings = earrings.filter(attributes__attribute_name='Earring Style', attributes__attribute_value__in=selected_earring_styles)
#     if selected_styles:
#         bracelets = bracelets.filter(attributes__attribute_name='Bracelet Style', attributes__attribute_value__in=selected_styles)
#     if selected_shop_for:
#         products = products.filter(gender__in=selected_shop_for)

#     if selected_gemstones:
#         products = products.filter(stonetype__name__in=selected_gemstones)
#     if selected_materials:
#         products = products.filter(metaltype__name__in=selected_materials)
#     if try_at_home_filter:
#         products = products.filter(try_at_home=True)
#     if selected_category:
#         products =  products.filter(category__name__in=selected_category)

#     context = {
#         'products': products,
#         'rings': rings,
#         'earrings': earrings,
#         'bracelets': bracelets,
#         'categories':categories,
#         'earring_styles': earring_styles,
#         'bracelet_styles': bracelet_styles,
#         'ring_sizes': ring_sizes,
#         'ring_types': ring_types,
#         'shop_for_options': shop_for_options,
#         'gemstones': gemstones,
#         'materials': materials,
#         'selected_ring_sizes': selected_ring_sizes,
#         'selected_ring_types': selected_ring_types,
#         'selected_earring_styles': selected_earring_styles,
#         'selected_styles': selected_styles,
#         'selected_gemstones': selected_gemstones,
#         'selected_materials': selected_materials,
#         'selected_shop_for': selected_shop_for,
#     }

#     return render(request, 'user/all_products.html', context)

#-----------------------------------------------------------------------------------------------------------------------------
from django.shortcuts import render
from .models import Product, Category, Metaltype, Stonetype, CategoryAttribute
from .models import ProductAttribute
import json
from django.http import JsonResponse
from django.shortcuts import render
from django.db.models import Q
from nltk.corpus import wordnet
from functools import reduce
import operator



import nltk
nltk.download("wordnet")

def all_products(request):
    products = Product.objects.filter(is_active=True)  # Fetch only active products
    
    # Get filter values from the request
    search_query = request.GET.get('search', '').strip()
    selected_category = request.GET.get('category', '').strip()
    selected_metaltype = request.GET.getlist('metaltype')
    selected_stonetype = request.GET.getlist('stonetype')
    selected_gender = request.GET.getlist('gender')
    try_at_home = request.GET.get('try_at_home', None)
    attribute_filters = {}

    # Debugging output
    print(f"Selected Category: {selected_category}")
    print(f"Search Query: {search_query}")

    # Filter by search query
    if search_query:
        products = products.filter(product_name__icontains=search_query)

    # Filter by category
    category_attributes = None
    if selected_category and selected_category.isdigit():  # Ensure valid category ID
        try:
            category_id = int(selected_category)
            print(f"Filtering by category ID: {category_id}")
            products = products.filter(category_id=category_id)

            # Fetch category-specific attributes
            category_attributes = CategoryAttribute.objects.filter(category_id=category_id)
            
            # Apply attribute filters from user input
            for attribute in category_attributes:
                attribute_value = request.GET.get(f"attribute_{attribute.id}", None)
                if attribute_value:
                    attribute_filters[attribute.name] = attribute_value
                    products = products.filter(
                        attributes__attribute_name=attribute.name,
                        attributes__attribute_value=attribute_value
                    )
        except ValueError:
            print("Invalid category ID passed.")

    # Filter by metal type
    if selected_metaltype:
        products = products.filter(metaltype_id__in=selected_metaltype)

    # Filter by stone type
    if selected_stonetype:
        products = products.filter(stonetype_id__in=selected_stonetype)

    # Filter by gender
    if selected_gender:
        products = products.filter(gender__in=selected_gender)

    # Filter by try at home
    if try_at_home:
        products = products.filter(try_at_home=True)

    # Fetch filter options
    categories = Category.objects.all()
    metaltypes = Metaltype.objects.all()
    stonetypes = Stonetype.objects.all()
    product_gender_choices = Product.GENDER_CHOICES


    query = request.GET.get("search", "").strip() 
    synonyms = set()  
    if query:
        for syn in wordnet.synsets(query):
            for lemma in syn.lemmas():
                synonyms.add(lemma.name().replace("_", " "))  # Replace underscores with spaces

# Base search query
    search_query = Q(product_name__icontains=query) | \
                    Q(product_description__icontains=query) | \
                    Q(category__name__icontains=query) | \
                    Q(metaltype__name__icontains=query) | \
                    Q(stonetype__name__icontains=query)

# Add synonyms dynamically (only if synonyms exist)
    synonym_queries = [Q(product_name__icontains=syn) for syn in synonyms]
    if synonym_queries:  
        full_query = search_query | reduce(operator.or_, synonym_queries, Q())
    else:
        full_query = search_query  # Prevent empty reduce() error

    products = products.filter(full_query).distinct()

    if 'login_id' in request.session:
        user_id = request.session['login_id']
        user_instance = get_object_or_404(Tbl_login, login_id=user_id)
        user_wishlist = Wishlist.objects.filter(login=user_instance).first()
        wishlist_items = WishlistItem.objects.filter(wishlist=user_wishlist).values_list('product_id', flat=True) if user_wishlist else []
    else:
        wishlist_items = []

    context = {
        'products': products,
        'wishlist_items': wishlist_items,  # Pass the wishlist items
        'categories': categories,
        'metaltypes': metaltypes,
        'stonetypes': stonetypes,
        'product_gender_choices': product_gender_choices,
        'selected_category': selected_category,
        'category_attributes': category_attributes,
        'attribute_filters': attribute_filters
    }

    return render(request, 'user/all_products.html', context)

import nltk
from nltk.corpus import wordnet
from django.db.models import Q

def search_suggestions(request):
    query = request.GET.get("term", "")
    if not query:
        return JsonResponse([], safe=False)

    # Find synonyms
    synonyms = set()
    for syn in wordnet.synsets(query):
        for lemma in syn.lemmas():
            synonyms.add(lemma.name())  # Add synonym to the set

    # Create a Q object for the search
    search_query = Q(product_name__icontains=query) | Q(product_description__icontains=query)
    for synonym in synonyms:
        search_query |= Q(product_name__icontains=synonym) | Q(product_description__icontains=synonym)

    # Fetch products that match the query
    products = Product.objects.filter(search_query).distinct()

    # Get the product names for suggestions
    suggestions = list(products.values_list("product_name", flat=True))[:10]
    return JsonResponse(suggestions, safe=False)


from django.shortcuts import render, get_object_or_404
import requests
from .models import Product

def detail(request, product_id):
    # Fetch product details
    product = get_object_or_404(Product, pk=product_id)

    # API setup
    api_key = 'goldapi-13te5osm64x6oty-io'
    headers = {
        'x-access-token': api_key,
        'Content-Type': 'application/json',
    }

    # Metals and API codes
    metals = {
        'Gold': 'XAU',
        'Silver': 'XAG',
        'Platinum': 'XPT',
    }

    metal_rates = {}
    product_metal_rate = None

    for metal, code in metals.items():
        try:
            api_url = f'https://www.goldapi.io/api/{code}/INR'
            response = requests.get(api_url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                # Extract price per gram
                price_per_gram = data.get('price_gram_24k', 0)  # Gold-specific key for price per gram
                if not price_per_gram:
                    price_per_gram = round(data.get('price', 0) / 31.1035, 2)  # Calculate from price per ounce
                metal_rates[metal] = price_per_gram

                # Check if this is the product's metal type
                if product.metaltype and product.metaltype.name.lower() == metal.lower():
                    product_metal_rate = price_per_gram
            else:
                metal_rates[metal] = "Unavailable"
        except Exception as e:
            metal_rates[metal] = "Error fetching rate"

    context = {
        'product': product,
        'metal_rates': metal_rates,
        'product_metal_rate': product_metal_rate,
    }
    return render(request, 'user/all_details.html', context)


#---------------------------------------------------------------------------------------------------------------------------------------------------------

def get_booked_dates_for_product(product):
    # Fetch all booked dates for the given product
    booked_dates = Booking.objects.filter(product=product).values_list('booking_date', flat=True)
    return list(booked_dates)



# from django.shortcuts import render, get_object_or_404, redirect
# from .models import Product, Tbl_user

# def book_schedule(request, product_id):
#     if 'login_id' not in request.session:
#         return redirect('login')  
    
#     login_id = request.session.get('login_id')
    
#     user = get_object_or_404(Tbl_user, login_id=login_id)  
    
#     product = get_object_or_404(Product, pk=product_id)
    
#     booked_dates = get_booked_dates_for_product(product) 

#     context = {
#         'product': product,
#         'user': user,
#         'booked_dates': booked_dates
#     }

#     return render(request, 'user/schedule_booking.html', context)



def book_schedule(request, product_id):
    if 'login_id' not in request.session:
        return redirect('login')  # Redirect to the login page if not logged in

    login_id = request.session.get('login_id')
    user = get_object_or_404(Tbl_user, login_id=login_id)
    product = get_object_or_404(Product, pk=product_id)
    booked_dates = get_booked_dates_for_product(product)

    if request.method == 'POST':
        booking_date = request.POST.get('booking_date')

        # Check if the user has already booked the same product for the selected date
        existing_booking = Booking.objects.filter(user=user, product=product, date=booking_date).exists()

        if existing_booking:
            messages.error(request, "You have already booked this product for the selected date.")
        else:
            # Create a new booking
            Booking.objects.create(user=user, product=product, date=booking_date, status='pending')
            messages.success(request, "Your booking has been scheduled successfully.")
            return redirect('booking_confirmation')  # Redirect to a confirmation page

    context = {
        'product': product,
        'user': user,
        'booked_dates': booked_dates,
    }
    return render(request, 'user/schedule_booking.html', context)  # Render the template with context


from django.core.mail import send_mail
from django.conf import settings

def submit_schedule(request, product_id):
    if request.method == "POST":
        login_id = request.session.get('login_id')
        user = get_object_or_404(Tbl_user, login_id=login_id)
        product = get_object_or_404(Product, pk=product_id)
        address = request.POST.get('address')
        booking_date = request.POST.get('date')

        # Create and save a new booking
        booking = Booking(user=user, product=product, address=address, booking_date=booking_date)
        booking.save()

        # Send email to staff
        staff_email = 'jeelelzapaul@gmail.com'  # Replace with actual staff email
        subject = f'New Booking for {product.product_name}'
        message = f'Booking Details:\n\nUser: {user.name}\nPhone: {user.phone}\nProduct: {product.product_name}\nDate: {booking_date}\nAddress: {address}'
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [staff_email])

        # Redirect to booking details page with booking ID
        return redirect('booking_details', booking_id=booking.booking_id)
    
def booking_details(request, booking_id):
    booking = get_object_or_404(Booking, pk=booking_id)

    context = {
        'booking': booking,
        'product': booking.product,
        'user': booking.user
    }

    return render(request, 'user/booking_detail.html', context)

from django.shortcuts import render, redirect, get_object_or_404
from django.core.mail import send_mail
from django.conf import settings
from .models import Booking, Tbl_user, Product, Tbl_staff
from django.contrib import messages

def view_bookings(request):
    bookings = Booking.objects.all()  # Fetch all bookings
    staff_members = Tbl_staff.objects.filter(status=True)  # Active staff only

    if request.method == 'POST':
        booking_id = request.POST.get('booking_id')
        action = request.POST.get('action')
        booking = get_object_or_404(Booking, booking_id=booking_id)  # Get the specific booking
        user = booking.user
        product = booking.product

        if action == 'approve':
            booking.status = 'confirmed'
            booking.save()

            # Send email to the user
            send_mail(
                'Booking Confirmation',
                f'Dear {user.name},\n\nYour booking for {product.product_name} has been confirmed.',
                settings.DEFAULT_FROM_EMAIL,
                [user.login.email],
            )
            messages.success(request, 'Booking approved and email sent to user.')

        elif action == 'reject':
            booking.status = 'cancelled'
            booking.save()

            # Send email to the user
            send_mail(
                'Booking Cancellation',
                f'Dear {user.name},\n\nYour booking for {product.product_name} has been cancelled.',
                settings.DEFAULT_FROM_EMAIL,
                [user.login.email],
            )
            messages.success(request, 'Booking rejected and email sent to user.')

        elif action == 'assign_staff':
            staff_id = request.POST.get('staff_id')
            staff = get_object_or_404(Tbl_staff, staff_id=staff_id)

            # Assign the staff for try at home
            booking.try_at_home = True  # Assuming this attribute indicates assignment
            booking.save()

            # Send email to the staff
            send_mail(
                'New Try at Home Assignment',
                f'Dear {staff.name},\n\nYou have been assigned to assist with the booking for {product.product_name}.',
                settings.DEFAULT_FROM_EMAIL,
                [staff.login.email],
            )
            messages.success(request, 'Staff assigned and email sent to staff.')

        return redirect('view_bookings')  # Redirect to the same page to see updated status

    return render(request, 'admin/view_booking.html', {
        'bookings': bookings,
        'staff_members': staff_members,
    })

from django.shortcuts import render, redirect, get_object_or_404
from .models import Booking, Tbl_user

def booking_history(request):
    # Check if the user is logged in by verifying 'login_id' in the session
    if 'login_id' not in request.session:
        return redirect('login')  # Redirect to login if not logged in

    # Get the login_id from session and fetch the corresponding user
    login_id = request.session['login_id']
    print(login_id)
    user = get_object_or_404(Tbl_user, login_id=login_id)

    # Retrieve bookings for the logged-in user, ordered by most recent first
    bookings = Booking.objects.filter(user=user).order_by('-booking_date')

    # Pass bookings to the template
    return render(request, 'user/booking.html', {'bookings': bookings})

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Booking, Tbl_user

def edit_booking(request, booking_id):  
    # Check if the user is logged in
    if 'login_id' not in request.session:
        return redirect('login')

    login_id = request.session['login_id']
    user = get_object_or_404(Tbl_user, login_id=login_id)

    # Retrieve the booking based on booking_id and user
    booking = get_object_or_404(Booking, booking_id=booking_id, user=user)

    if request.method == 'POST':
        address = request.POST.get('address')
        phone = request.POST.get('phone')

        # Phone validation
        if not (phone.isdigit() and len(phone) == 10 and phone[0] in '6789'):
            messages.error(request, "Phone number must be 10 digits and start with 6, 7, 8, or 9.")
            return render(request, 'user/edit_booking.html', {'form': None, 'booking': booking})

        # Address validation
        if not address.strip():
            messages.error(request, "Address cannot be empty.")
            return render(request, 'user/edit_booking.html', {'form': None, 'booking': booking})

        # Update the booking if validations pass
        booking.address = address
        booking.phone = phone  # Assuming you have a phone field in the Booking model
        booking.save()
        messages.success(request, "Booking updated successfully.")
        return redirect('booking_history')

    return render(request, 'user/edit_booking.html', {'form': None, 'booking': booking})

#//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

from django.shortcuts import render, redirect
from .models import Billing
from django.contrib import messages

from jewelryapp.models import Billing, Tbl_user, Tbl_login

def address_view(request):
    if 'login_id' not in request.session:
        return redirect('login')  
    # Fetch the login_id from the session
    login_id = request.session['login_id']

    # Get the user_id corresponding to the login_id
    try:
        user = Tbl_user.objects.get(login_id=login_id)  

        # Fetch addresses from the Billing table for the fetched user
        addresses = Billing.objects.filter(user_id=user.user_id)

        context = {
            'addresses': addresses,
        }
        return render(request, 'user/address_view.html', context)
    except Tbl_user.DoesNotExist:
        # Handle case where user does not exist for the given login_id
        return redirect('login')  # Redirect to login if user not found
def select_address(request):
    if request.method == 'POST':
        selected_address_id = request.POST.get('selected_address')
        if selected_address_id:
            request.session['selected_address_id'] = selected_address_id  # Use 'selected_address_id'
            messages.success(request, 'Address selected successfully!')
            return redirect('order_summary')  # Redirect to the order summary page
        else:
            messages.error(request, 'Please select an address.')
            return redirect('addresse_view')  # Redirect back to the address view if no address is selected


from django.shortcuts import redirect, render
from django.contrib import messages
from .models import Billing, Tbl_user

def add_address(request):
    # Check if the user is logged in
    if 'login_id' not in request.session:
        return redirect('login')
    
    # Retrieve the logged-in user's ID from the session
    login_id = request.session['login_id']
    
    # Get the `Tbl_user` instance related to the `Tbl_login` session ID
    try:
        user = Tbl_user.objects.get(login__login_id=login_id)
    except Tbl_user.DoesNotExist:
        messages.error(request, "User not found.")
        return redirect('address_view')

    if request.method == 'POST':
        # Collect form data
        house_name = request.POST.get('house_name')
        postal_address = request.POST.get('postal_address')
        city = request.POST.get('city')
        district = request.POST.get('district')
        state = request.POST.get('state')
        pincode = request.POST.get('pincode')

        # Create and save the new Billing address
        billing_address = Billing(
            user=user,  # `user` is an instance of `Tbl_user`
            house_name=house_name,
            postal_address=postal_address,
            city=city,
            district=district,
            state=state,
            pincode=pincode
        )
        
        try:
            billing_address.save()
            messages.success(request, "Address added successfully!")
            return redirect('address_view')
        except Exception as e:
            messages.error(request, f"Error saving address: {e}")
            return redirect('add_address')

    # Render the add address page if request method is GET
    return render(request, 'user/add_address.html')


# views.py
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Billing  # Replace with your actual address model

@csrf_exempt
def remove_address(request, address_id):
    if request.method == 'POST':
        try:
            address = Billing.objects.get(id=address_id)
            address.delete()
            return JsonResponse({'status': 'success'})
        except Billing.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Address not found'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request'})
def order_summary(request):
    if 'login_id' not in request.session:
        return redirect('login')

    login_id = request.session['login_id']
    try:
        # Fetch the login instance
        login = Tbl_login.objects.get(login_id=login_id)

        # Fetch the user's cart
        cart = Cart.objects.get(login=login)

        # Fetch active cart items
        cart_items = CartItem.objects.filter(cart=cart, status=True)

        # Calculate the total amount for the cart
        total_amount = sum(item.get_total_price() for item in cart_items)

        # Multiply total amount by 100 (for Razorpay API)
        total_amount_paise = int(total_amount * 100)

        # Fetch the selected address from the session
        selected_address_id = request.session.get('selected_address_id')
        if not selected_address_id:
            messages.error(request, "No address selected.")
            return redirect('address_view')

        # Fetch the selected billing address
        user = Tbl_user.objects.get(login_id=login_id)  # Fetch user instance
        address = Billing.objects.get(id=selected_address_id, user_id=user.user_id)

        # Context for the template
        context = {
            'address': address,
            'cart_items': cart_items,
            'total_amount': total_amount,
            'total_amount_paise': total_amount_paise,  # Add this to the context
        }
        return render(request, 'user/order_summary.html', context)

    except Tbl_login.DoesNotExist:
        messages.error(request, "User not found.")
        return redirect('login')

    except Cart.DoesNotExist:
        messages.error(request, "Cart not found.")
        return redirect('view_cart')  # Redirect to cart page

    except Billing.DoesNotExist:
        messages.error(request, "Billing address not found.")
        return redirect('address_view')  # Redirect to address selection page
    


    from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
import json
from .models import Order, OrderItem, CartItem, Tbl_user, Billing, Product, Cart, Tbl_login

@csrf_exempt
def payment_success(request):
    if request.method == 'POST':
        try:
            # Parse the request data
            data = json.loads(request.body)
            payment_id = data.get('payment_id')
            address_id = data.get('address_id')
            total_price = data.get('total_price')

            # Fetch the user and cart
            login_id = request.session.get('login_id')
            if not login_id:
                return JsonResponse({'status': 'error', 'message': 'User not logged in'}, status=403)

            # Get login instance first
            login = Tbl_login.objects.get(login_id=login_id)
            user = Tbl_user.objects.get(login=login)
            cart = Cart.objects.get(login=login)
            cart_items = CartItem.objects.filter(cart=cart, status=True)

            # Create the Order
            billing = Billing.objects.get(id=address_id)
            order = Order.objects.create(
                user=user,
                billing=billing,
                cart=cart,
                status='Confirmed',
                payment_status='Success',
                total_amount=total_price,
                razorpay_order_id=payment_id,
                payment_date=timezone.now(),
                confirmed_date=timezone.now()
            )

            # Process cart items and update stock
            for cart_item in cart_items:
                product = cart_item.product

                # Check if enough stock is available
                if product.stock_quantity < cart_item.quantity:
                    return JsonResponse({
                        'status': 'error',
                        'message': f"Insufficient stock for {product.product_name}. Only {product.stock_quantity} available."
                    }, status=400)

                # Reduce product stock quantity
                product.stock_quantity -= cart_item.quantity
                product.save()

                # Create OrderItem
                OrderItem.objects.create(
                    order=order,
                    product=product.product_name,
                    quantity=cart_item.quantity,
                    price=product.price
                )

                # Mark the cart item as inactive
                cart_item.status = False
                cart_item.save()

            # Mark the cart as completed
            cart.is_completed = True
            cart.save()

            return JsonResponse({'status': 'success', 'message': 'Order placed successfully'})

        except Tbl_login.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'User login not found'}, status=404)
        except Tbl_user.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'User not found'}, status=404)
        except Billing.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Billing address not found'}, status=404)
        except Cart.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Cart not found'}, status=404)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)


# ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

# from django.conf import settings
# from .models import Tbl_login, Tbl_user, Cart, CartItem, Billing, Order, OrderItem, Product
# import razorpay
# from django.shortcuts import get_object_or_404, redirect, render
# from django.contrib import messages

# razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
# def checkout(request):
#     if 'login_id' not in request.session:
#         return redirect('login')

#     login_id = request.session['login_id']
#     login_user = get_object_or_404(Tbl_login, login_id=login_id)
#     user = get_object_or_404(Tbl_user, login=login_user)

#     cart = Cart.objects.filter(login=login_user).last()
#     if not cart:
#         messages.error(request, "No active cart found.")
#         return redirect('view_cart') 

#     cart_items = cart.items.filter(status=True)
#     total_price = sum(item.product.price * item.quantity for item in cart_items)

#     addresses = Billing.objects.filter(user=user)

#     if request.method == 'POST':
#         selected_address_id = request.POST.get('selected_address')
#         if not selected_address_id:
#             messages.error(request, "Please select a billing address.")
#             return redirect('checkout')

#         address = get_object_or_404(Billing, id=selected_address_id, user=user)

#         try:
            
#             razorpay_order = razorpay_client.order.create({
#                 "amount": int(total_price * 100), 
#                 "currency": "INR",
#                 "payment_capture": "1"
#             })

            
#             request.session['razorpay_order_id'] = razorpay_order['id']
#             request.session['selected_address_id'] = selected_address_id

#             return render(request, 'user/billing.html', {
#                 'razorpay_order_id': razorpay_order['id'],
#                 'razorpay_key': settings.RAZORPAY_KEY_ID,
#                 'total_price': total_price * 100,
#             })
#         except Exception as e:
#             messages.error(request, f"Error creating Razorpay order: {str(e)}")
#             return redirect('checkout')

#     return render(request, 'user/billing.html', {
#         'cart_items': cart_items,
#         'total_price': total_price,
#         'addresses': addresses
#     })

# ///////////////////////////////////////////////////////////////////////////////////////////////////////
# def payment_success(request):
#     if 'razorpay_order_id' not in request.session:
#         messages.error(request, "No payment information found.")
#         return redirect('checkout')

#     login_id = request.session['login_id']
#     login_user = get_object_or_404(Tbl_login, login_id=login_id)
#     user = get_object_or_404(Tbl_user, login=login_user)

#     razorpay_order_id = request.session.pop('razorpay_order_id')
#     selected_address_id = request.session.pop('selected_address_id')
#     address = get_object_or_404(Billing, id=selected_address_id, user=user)

#     cart = Cart.objects.filter(login=login_user, is_completed=False).last()
#     cart_items = cart.items.filter(status=True)
#     total_price = sum(item.product.price * item.quantity for item in cart_items)

#     try:
#         order = Order.objects.create(
#             user=user,
#             billing=address,
#             cart=cart,
#             total_amount=total_price,
#             status='Pending',
#             payment_status='Success',
#             razorpay_order_id=razorpay_order_id
#         )

#         for item in cart_items:
#             product = item.product 
            
#             if product.stock_quantity < item.quantity:
#                 raise ValueError(f"Insufficient stock for {product.product_name}. Only {product.stock_quantity} available.")

#             product.stock_quantity -= item.quantity
#             product.save()

#             OrderItem.objects.create(
#                 order=order,
#                 product=product.product_name,
#                 quantity=item.quantity,
#                 price=product.price
#             )
            
#             item.status = False
#             item.save()

#         cart.is_completed = True
#         cart.save()

#         messages.success(request, "Payment successful! Your order has been placed.")
#         return redirect('order_history', order_id=order.id)

#     except Exception as e:
#         messages.error(request, f"Error processing payment: {str(e)}")
#         return redirect('checkout')
# //////////////////////////////////////////////////////////////////////////////////////////////////////////////////

from django.shortcuts import render, redirect, get_object_or_404
from .models import Order, OrderItem, Tbl_user

def order_history(request):
    # Check if the user is logged in
    if 'login_id' not in request.session:
        return redirect('login')  # Redirect to login page if not logged in

    # Get the logged-in user
    login_id = request.session['login_id']
    user = get_object_or_404(Tbl_user, login_id=login_id)

    # Retrieve orders for the user
    orders = Order.objects.filter(user=user).order_by('-order_date')

    return render(request, 'user/order_history.html', {'orders': orders})


def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    order_items = OrderItem.objects.filter(order=order)
    
    # Create status timeline based on payment status
    status_timeline = []
    
    if order.payment_status == 'Pending':
        status_timeline.append({
            'status': 'Pending Payment',
            'date': order.order_date,
            'active': True,
            'show_payment_button': True
        })
    else:
        # Start with Confirmed status for paid orders
        status_timeline = [
            {
                'status': 'Confirmed',
                'date': order.confirmed_date or order.payment_date,  # Use payment date if confirmed date is not set
                'active': order.status == 'Confirmed'
            },
            {
                'status': 'Shipped',
                'date': order.shipped_date,
                'active': order.status == 'Shipped'
            },
            {
                'status': 'Out for Delivery',
                'date': order.out_for_delivery_date,
                'active': order.status == 'Out for Delivery'
            },
            {
                'status': 'Delivered',
                'date': order.delivery_date,
                'active': order.status == 'Delivered'
            }
        ]
    
    context = {
        'order': order,
        'order_items': order_items,
        'status_timeline': status_timeline,
    }
    
    return render(request, 'user/order_detail.html', context)

def update_order_status(request, order_id):
    if request.method == 'POST':
        staff = get_object_or_404(Tbl_staff, login_id=request.session.get('login_id'))
        if staff.role != 'Sales':
            messages.error(request, 'Unauthorized action')
            return redirect('staffhome')
            
        order = get_object_or_404(Order, id=order_id)
        new_status = request.POST.get('status')
        current_time = timezone.now()
        
        # Only allow status updates for paid orders
        if order.payment_status != 'Success':
            messages.error(request, 'Cannot update status for unpaid orders')
            return redirect('staffhome')
        
        # Update status and corresponding timestamps
        order.status = new_status
        if new_status == 'Confirmed':
            order.confirmed_date = current_time
        elif new_status == 'Shipped':
            order.shipped_date = current_time
        elif new_status == 'Out for Delivery':
            order.out_for_delivery_date = current_time
        
        order.save()
        
        # Send email notification to customer
        try:
            subject = f'Order #{order.id} Status Update'
            message = f'''
            Dear {order.user.name},
            
            Your order status has been updated.
            
            Order Details:
            Order ID: {order.id}
            New Status: {new_status}
            Updated on: {current_time.strftime('%Y-%m-%d %H:%M')}
            
            Track your order in the order details section of your account.
            '''
            
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [order.user.login.email],
                fail_silently=True
            )
        except Exception as e:
            messages.warning(request, f'Email notification failed: {str(e)}')
        
        messages.success(request, f'Order status updated to {new_status}')
        
    return redirect('staffhome')

# ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
# user profile displaying and updating
from django.shortcuts import render, redirect, get_object_or_404
from .models import Tbl_user, Tbl_login, Billing, Order
from django.contrib import messages

def profile(request):
    # Ensure the user is logged in
    if 'login_id' not in request.session:
        return redirect('login')

    login_id = request.session['login_id']
    user = get_object_or_404(Tbl_user, login_id=login_id)
    addresses = Billing.objects.filter(user=user)

    return render(request, 'user/profile.html', {
        'user': user,
        'addresses': addresses,
    })

from django.shortcuts import render, redirect, get_object_or_404
from .models import Tbl_user, Billing

def update_profile(request):
    if 'login_id' not in request.session:
        return redirect('login')

    login_id = request.session['login_id']
    user = get_object_or_404(Tbl_user, login_id=login_id)
    addresses = Billing.objects.filter(user=user)

    if request.method == 'POST':
        # Update user email and phone
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        user.phone = phone
        user.login.email = email
        user.login.save()
        user.save()

        # Update addresses
        for index, address in enumerate(addresses, start=1):
            house_name = request.POST.get(f'house_name_{index}')
            postal_address = request.POST.get(f'postal_address_{index}')
            city = request.POST.get(f'city_{index}')
            district = request.POST.get(f'district_{index}')
            state = request.POST.get(f'state_{index}')
            pincode = request.POST.get(f'pincode_{index}')

            address.house_name = house_name
            address.postal_address = postal_address
            address.city = city
            address.district = district
            address.state = state
            address.pincode = pincode
            address.save()

        return redirect('profile')  # Redirect to the profile page after saving changes

    return render(request, 'user/update_profile.html', {
        'user': user,
        'addresses': addresses,
    })
from django.http import JsonResponse
from django.core.mail import send_mail, BadHeaderError
import random
import json
import logging

logger = logging.getLogger(__name__)

# View to send OTP
def send_otp(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)  # Parse JSON body
            email = data.get('email')
            if not email:
                return JsonResponse({'status': 'error', 'message': 'Email is required.'}, status=400)

            otp = random.randint(100000, 999999)
            request.session['email_otp'] = otp
            request.session['email_to_verify'] = email

            try:
                # Send OTP via email
                send_mail(
                    'Your OTP Code',
                    f'Your OTP code is {otp}',
                    'noreply@yourdomain.com',
                    [email],
                    fail_silently=False,
                )
            except BadHeaderError:
                return JsonResponse({'status': 'error', 'message': 'Invalid email header.'}, status=400)
            except Exception as e:
                return JsonResponse({'status': 'error', 'message': f'Error sending email: {str(e)}'}, status=500)

            return JsonResponse({'status': 'success', 'message': 'OTP sent successfully.'})
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON data.'}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=405)


# View to verify OTP
def verify_otp(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)  # Parse JSON body
            otp = data.get('otp')
            if str(otp) == str(request.session.get('email_otp')):
                return JsonResponse({'status': 'success', 'message': 'OTP verified successfully.'})
            return JsonResponse({'status': 'error', 'message': 'Invalid OTP.'}, status=400)
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON data.'}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=405)



#/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

# def staffhome(request):
#     return render(request, 'staff/staffhome.html')

from django.shortcuts import render, redirect, get_object_or_404
from django.core.mail import send_mail
from django.contrib import messages
from .models import Booking
from django.conf import settings
from django.http import HttpResponseForbidden

# Helper function to check if the user is a staff member
# def is_staff_logged_in(request):
#     return request.session.get('user_type') == 'staff' and 'login_id' in request.session

# Staff Home Page View
# def staffhome(request):
    # Check if staff is logged in via session
    # if not is_staff_logged_in(request):
    #     return redirect('/login/')  # Redirect to login if not authenticated

    # Fetch bookings assigned to the staff with status 'pending'
    # bookings = Booking.objects.filter(
    #     status='pending',
    #     product__try_at_home=True
    # ).select_related('user', 'product').order_by('-booking_date')
    
    # context = {
    #     'bookings': bookings,
    #     'name': request.session.get('name')  # Get the staff name from session
    # }
    # return render(request, 'staff/staffhome.html', context)

# Accept Booking View
def accept_booking(request, booking_id):
    # Check if staff is logged in via session
    # if not is_staff_logged_in(request):
    #     return HttpResponseForbidden("Unauthorized access")

    # Fetch the booking details
    booking = get_object_or_404(Booking, booking_id=booking_id)
    
    # Change status to 'confirmed'
    booking.status = 'confirmed'
    booking.save()

    # Send email after accepting the task
    try:
        send_mail(
            subject="Try-at-Home Booking Accepted",
            message=f"Dear {booking.user.name},\n\nYour booking for {booking.product.product_name} has been accepted. Our staff will reach out to you soon.\n\nThank you,\nOrnalux Team",
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[booking.user.email],
            fail_silently=False,
        )
        messages.success(request, "Booking accepted and email sent to the user.")
    except Exception as e:
        messages.error(request, f"Error sending email: {str(e)}")

    return redirect('staffhome')

# /////////////////////////////////////////////////////////////////////////////////////////////////////////////////
# old gold exachange
import requests
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
import json

# Gold API Key
GOLD_API_KEY = 'goldapi-17slwbsm27mhx49-io'
GOLD_API_URL = 'https://www.goldapi.io/api/XAU/INR'

def gold_rates_view(request):
    """
    Fetch real-time gold rates and return as JSON.
    """
    try:
        # Fetch real-time gold rates from the API
        response = requests.get(GOLD_API_URL, headers={
            'x-access-token': GOLD_API_KEY,
            'Content-Type': 'application/json',
        })
        response_data = response.json()
        if 'price' in response_data:
            gold_rate_per_gram_24k = response_data['price'] / 31.1035  # Convert price per ounce to per gram
            rates = {
                '24K': gold_rate_per_gram_24k,
                '22K': gold_rate_per_gram_24k * 0.9167,  # 91.67% of 24K
                '18K': gold_rate_per_gram_24k * 0.75,    # 75% of 24K
                '14K': gold_rate_per_gram_24k * 0.5833,  # 58.33% of 24K
            }
            return JsonResponse({'status': 'success', 'rates': rates})
        else:
            return JsonResponse({'status': 'error', 'message': 'Failed to fetch rates'}, status=500)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@csrf_exempt
def calculate_gold_value(request):
    """
    Calculate the value of gold based on weight and karat provided by the user.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            weight = float(data.get('weight', 0))
            karat = int(data.get('karat', 0))
            
            # Fetch real-time 24K gold rate
            response = requests.get(GOLD_API_URL, headers={
                'x-access-token': GOLD_API_KEY,
                'Content-Type': 'application/json',
            })
            response_data = response.json()
            if 'price' in response_data:
                gold_rate_per_gram_24k = response_data['price'] / 31.1035  # Convert price per ounce to per gram
                purity_factor = karat / 24
                gold_value = weight * gold_rate_per_gram_24k * purity_factor
                return JsonResponse({'status': 'success', 'value': gold_value})
            else:
                return JsonResponse({'status': 'error', 'message': 'Failed to fetch gold rate'}, status=500)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)

def gold_exchange_page(request):
    """
    Render the Old Gold Exchange page.
    """
    return render(request, 'user/old_gold.html')

from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from .models import PickupDetails

def save_pickup_details(request):
    if 'login_id' not in request.session:
        return JsonResponse({'error': 'User not logged in'}, status=403)

    user_id = request.session['login_id']
    user = get_object_or_404(Tbl_user, login_id=user_id)

    if request.method == 'POST':
        try:
            import json
            data = json.loads(request.body)

            # Get form data from the request
            name = data.get('name')
            phone = data.get('phone')
            email = data.get('email')
            place = data.get('place')

            # Ensure all fields are provided
            if not all([name, phone, email, place]):
                return JsonResponse({'success': False, 'error': 'All fields are required.'})

            # Save to database
            PickupDetails.objects.create(user=user, name=name, phone=phone, email=email, place=place)

            return JsonResponse({'success': True})

        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON data.'})
        except Exception as e:
            # Log the exception or handle as needed
            return JsonResponse({'success': False, 'error': f'An error occurred: {str(e)}'})
    else:
        return JsonResponse({'success': False, 'error': 'Invalid request method.'})

from django.http import JsonResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from django.utils.dateparse import parse_date
from datetime import datetime
from .models import StoreVisit
import json


@csrf_exempt
def schedule_store_visit(request):
    if 'login_id' not in request.session:
        return JsonResponse({'error': 'User not logged in'}, status=403)

    user_id = request.session['login_id']
    try:
        user = get_object_or_404(Tbl_user, login_id=user_id)
        print(user)
    except Http404:
        return JsonResponse({'success': False, 'message': 'User not found.'})
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            name = data.get('name')
            phone = data.get('phone')
            date = data.get('date')
            time = data.get('time')
            
            # Validate required fields
            if not all([name, phone, date, time]):
                return JsonResponse({'success': False, 'message': 'All fields are required.'})
            
            # Validate phone number format
            if not phone.isdigit() or len(phone) != 10:
                return JsonResponse({'success': False, 'message': 'Invalid phone number. Please enter a 10-digit number.'})
            
            # Validate date format
            try:
                visit_date = parse_date(date)
                if visit_date < datetime.today().date():
                    return JsonResponse({'success': False, 'message': 'Preferred date cannot be in the past.'})
            except ValueError:
                return JsonResponse({'success': False, 'message': 'Invalid date format.'})
            
            # Check if the same person already has a booking on the same date and time
            same_date_time_booking = StoreVisit.objects.filter(phone=phone, date=date, time=time).exists()
            if same_date_time_booking:
                return JsonResponse({
                    'success': False,
                    'message': 'You already have a booking at this date and time. Please choose another.'
                })
            
            # Check if the same person already has a booking on the same day
            same_day_booking = StoreVisit.objects.filter(phone=phone, date=date).exists()
            if same_day_booking:
                return JsonResponse({
                    'success': False,
                    'message': 'You already have a booking on this day. You cannot make multiple reservations on the same day.'
                })
            
            # Save data to the database
            visit = StoreVisit(
                user=user,  # Link to logged-in user
                name=name,
                phone=phone,
                date=date,
                time=time
            )
            visit.save()

            return JsonResponse({'success': True, 'message': 'Store visit scheduled successfully.'})
        
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'An error occurred: {str(e)}'})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method.'})


from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.csrf import csrf_exempt
from .models import PickupDetails, StoreVisit

def view_old_gold_exchange(request, user_id):
    if 'login_id' not in request.session:
        return redirect('login') # Redirect to login page if user is not authenticated

    user_id = request.session['login_id']
    try:
        # Fetch the user instance
        user = Tbl_user.objects.get(login_id=user_id)
    except Tbl_user.DoesNotExist:
        return redirect('login') 
    # Fetch user-specific old gold exchange details
    pickup_details = PickupDetails.objects.filter(user=user)
    store_visit = StoreVisit.objects.filter(user=user)
    context = {
        'pickup_details': pickup_details,
        'store_visit': store_visit
    }
    return render(request, 'user/view_old_gold_exchange.html', context)


@csrf_exempt
def update_pickup_details(request, pickup_id):
    pickup = get_object_or_404(PickupDetails, id=pickup_id)

    if request.method == 'POST':
        # print("Incoming Data:", request.POST)

        pickup.phone = request.POST.get('phone',pickup.phone)
        pickup.email = request.POST.get('email',pickup.email)
        pickup.place = request.POST.get('place', pickup.place)
        pickup.save()
        # print("Updated Pickup Details:", pickup)

        return redirect('view_old_gold_exchange', user_id=pickup.user.user_id)

    return render(request, 'user/update_pickup_details.html', {'pickup': pickup})

@csrf_exempt
def update_or_cancel_store_visit(request, store_visit_id):
    store_visit = get_object_or_404(StoreVisit, id=store_visit_id)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'update':
            store_visit.phone = request.POST.get('phone', store_visit.phone)
            store_visit.date = request.POST.get('date', store_visit.date)
            store_visit.time = request.POST.get('time', store_visit.time)
            store_visit.save()
        elif action == 'cancel':
            store_visit.status = 'Cancelled'
            store_visit.save()

        return redirect('view_old_gold_exchange', user_id=store_visit.user.user_id)

    return render(request, 'user/update_or_cancel_store_visit.html', {'store_visit': store_visit})



from .models import VendorProduct
def vendor_home(request):
    if 'login_id' not in request.session or request.session.get('user_type') != 'vendor':
        return redirect('login')

    vendor = get_object_or_404(Vendor, login_id=request.session['login_id'])

    # Fetch total orders and customers
    total_orders = Order.objects.filter(user__login=vendor.login).count()
    total_customers = Tbl_user.objects.count()  # Assuming all users are customers

    # Fetch restock requests
    # restock_requests = RestockRequest.objects.filter(vendor_product__vendor=vendor, status='Pending')

    # Prepare data for trading performance chart
    trading_labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    trading_data = [100, 200, 150, 300, 250, 400, 350, 500, 450, 600, 550, 700]  # Example data

    context = {
        'vendor': vendor,
        'total_orders': total_orders,
        'total_customers': total_customers,
        # 'restock_requests': restock_requests,
        'trading_labels': trading_labels,
        'trading_data': trading_data,
    }

    return render(request, 'vendor/dashboard.html', context)


# def add_vendor_product(request):
#     if request.method == 'POST':
#         supplier = get_object_or_404(Supplier, login=request.user)
        
#         try:
#             product = SupplierProduct(
#                 supplier=supplier,
#                 product_name=request.POST['product_name'],
#                 description=request.POST['description'],
#                 price=float(request.POST['price']),
#                 stock=int(request.POST['stock']),
#                 image=request.FILES['image'],
#                 category_id=request.POST['category'],
#                 weight=float(request.POST['weight']),
#                 metaltype_id=request.POST['metaltype']
#             )
#             product.save()
#             messages.success(request, 'Product added successfully!')
#             return redirect('view_supplier_products')
#         except Exception as e:
#             messages.error(request, f'Error adding product: {str(e)}')
    
#     categories = Category.objects.all()
#     metaltypes = Metaltype.objects.all()
#     context = {
#         'categories': categories,
#         'metaltypes': metaltypes
#     }
#     return render(request, 'vendor/add_product.html', context)



def generate_password():
    """Generate a random password"""
    characters = string.ascii_letters + string.digits + "!@#$%^&*()"
    return ''.join(random.choice(characters) for i in range(12))

def add_vendor(request):
    if request.method == 'POST':
        business_name = request.POST.get('business_name')
        email = request.POST.get('email')
        contact = request.POST.get('contact')
        documents = request.FILES.get('documents')

        try:
            # Generate random password
            password = generate_password()

            # Create login entry
            login = Tbl_login.objects.create(
                email=email,
                password=password,  # In production, hash this password
                status=True
            )

            # Create vendor entry
            vendor = Vendor.objects.create(
                business_name=business_name,
                email=email,
                contact=contact,
                login=login,
                documents=documents
            )

            # Send email to vendor
            subject = 'Vendor Account Created - Ornalux'
            message = f"""
            Dear {business_name},

            Your vendor account has been created successfully on Ornalux.

            Login Details:
            Email: {email}
            Password: {password}

            Please login and change your password immediately.

            Best regards,
            Ornalux Team
            """

            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )

            messages.success(request, 'Vendor added successfully. Login credentials have been sent to their email.')
            return redirect('add_vendor')

        except Exception as e:
            messages.error(request, f'Error creating vendor account: {str(e)}')
            return redirect('add_vendor')

    return render(request, 'admin/add_vendor.html')

def verify_vendor_documents(request, vendor_id):
    if not request.session.get('user_type') == 'admin':
        messages.error(request, 'Unauthorized access')
        return redirect('login')

    vendor = get_object_or_404(Vendor, vendor_id=vendor_id)
    
    try:
        # Initialize document verifier
        verifier = BusinessDocumentVerifier()
        
        # Get the full path of the uploaded document
        document_path = os.path.join(settings.MEDIA_ROOT, str(vendor.documents))
        
        # Verify the document
        verification_results = verifier.verify_document(document_path)
        
        # Update vendor status based on verification results
        if verification_results['success'] and verification_results['is_valid']:
            vendor.verification_status = 'verified'
            vendor.verification_remarks = "Document verified successfully"
        else:
            vendor.verification_status = 'rejected'
            vendor.verification_remarks = verification_results.get('message', 'Document verification failed')
        
        vendor.save()
        
        # Send email notification to vendor
        subject = 'Document Verification Status - Ornalux'
        message = f"""
        Dear {vendor.business_name},

        Your document verification status has been updated.
        Status: {vendor.verification_status.title()}
        
        Remarks:
        {vendor.verification_remarks}

        Please contact support if you have any questions.

        Best regards,
        Ornalux Team
        """
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [vendor.email],
            fail_silently=True,
        )

        messages.success(request, 'Document verification completed')
        
    except Exception as e:
        messages.error(request, f'Error during verification: {str(e)}')
    
    return redirect('verify_vendor')

from django.http import JsonResponse
from .document_verification import BusinessDocumentVerifier
import os

def verify_document(request):
    """Handle document verification API endpoint"""
    if request.method == 'POST' and request.FILES.get('document'):
        try:
            document = request.FILES['document']
            
            # Save the uploaded file temporarily
            temp_path = os.path.join(settings.MEDIA_ROOT, 'temp', document.name)
            os.makedirs(os.path.dirname(temp_path), exist_ok=True)
            
            with open(temp_path, 'wb+') as destination:
                for chunk in document.chunks():
                    destination.write(chunk)
            
            # Analyze document
            verifier = BusinessDocumentVerifier()
            results = verifier.verify_document(temp_path)
            
            # Clean up
            os.remove(temp_path)
            
            return JsonResponse(results)
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method or no document provided'
    })

def verify_document_page(request):
    """Render the document verification page"""
    return render(request, 'admin/verify_vendor.html')
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Vendor, Category, Metaltype, Stonetype, VendorProduct  # Ensure VendorProduct is imported

def vendor_add_product(request):
    if 'login_id' not in request.session or request.session.get('user_type') != 'vendor':
        messages.error(request, 'You need to log in as a vendor to access this page.')
        return redirect('login')

    if request.method == 'POST':
        product_name = request.POST.get('product_name')
        category_id = request.POST.get('id_category')
        product_description = request.POST.get('product_description')
        price = request.POST.get('price')
        stock_quantity = request.POST.get('stock_quantity')
        weight = request.POST.get('weight')
        metaltype_id = request.POST.get('metaltype')
        stonetype_id = request.POST.get('stonetype')
        gender = request.POST.get('gender', 'Unisex')  # Default to 'Unisex' if not provided
        image = request.FILES.get('image')  # Get the uploaded image

        # Validate the inputs
        try:
            price = float(price)
            stock_quantity = int(stock_quantity)
            weight = float(weight)
        except ValueError:
            messages.error(request, "Invalid input values.")
            return redirect('vendor_add_product')

        if not (100 <= price <= 10000000):
            messages.error(request, "Price must be between 100 and 10,000,000.")
            return redirect('vendor_add_product')

        if not (0 <= stock_quantity <= 50):
            messages.error(request, "Stock quantity must be between 0 and 50.")
            return redirect('vendor_add_product')

        if not (1 <= weight <= 100):
            messages.error(request, "Weight must be between 1 and 100 grams.")
            return redirect('vendor_add_product')

        # Create the VendorProduct instance and save it
        try:
            vendor = get_object_or_404(Vendor, login_id=request.session['login_id'])  # Fetch the vendor
            vendor_product = VendorProduct(
                vendor=vendor,
                product_name=product_name,
                product_description=product_description,
                price=price,
                stock_quantity=stock_quantity,
                weight=weight,
                gender=gender,
                image=image,
                category_id=category_id,
                metaltype_id=metaltype_id,
                stonetype_id=stonetype_id
            )
            vendor_product.save()

            # Save category attributes
            attributes_data = request.POST.getlist('attributes')
            for attribute_id in attributes_data:
                if attribute_id:  # Only proceed if the ID is not empty
                    attribute_value = request.POST.get(f'attribute_{attribute_id}', '')
                    if attribute_value:
                        VendorProductAttribute.objects.create(
                            vendor_product=vendor_product,
                            attribute_name=attribute_id,  # Assuming you have a way to get the attribute name
                            attribute_value=attribute_value
                        )

            messages.success(request, "Product added successfully!")
            return redirect('vendor_view_products')  # Redirect to the view products page

        except Exception as e:
            messages.error(request, f"Error adding product: {str(e)}")
            return redirect('vendor_add_product')

    # GET request to render the page
    categories = Category.objects.all()
    metaltypes = Metaltype.objects.all()
    stonetypes = Stonetype.objects.all()  # Fetch stonetypes from the database
    vendors = Vendor.objects.all()  # Fetch all vendors

    context = {
        'categories': categories,
        'metaltypes': metaltypes,
        'stonetypes': stonetypes,  # Pass the list of stonetypes to the template
        'vendors': vendors,  # Pass the list of vendors to the template
    }
    return render(request, 'vendor/add_product.html', context)

def vendor_view_products(request):
    print("Vendor View Products Called")  # Debugging line
    if 'login_id' not in request.session or request.session.get('user_type') != 'vendor':
        return redirect('login')

    vendor = get_object_or_404(Vendor, login_id=request.session['login_id'])
    
    # Fetch products associated with the vendor from the VendorProduct table only
    vendor_products = VendorProduct.objects.filter(vendor=vendor)

    context = {
        'products': vendor_products,  # Only pass vendor products to the template
        'vendor': vendor,
    }
    return render(request, 'vendor/view_products.html', context)


def vendor_edit_product(request, product_id):
    print(f"Editing product with ID: {product_id}")  # Debugging line
    if not request.session.get('user_type') == 'vendor':
        messages.error(request, 'You need to log in as a vendor to access this page.')
        return redirect('login')
        
    product = get_object_or_404(VendorProduct, pk=product_id, vendor__login_id=request.session['login_id'])
    
    if request.method == 'POST':
        try:
            # Update product fields based on the form data
            product.product_name = request.POST['product_name']
            product.product_description = request.POST['product_description']
            product.price = float(request.POST['price'])
            product.stock_quantity = int(request.POST['stock_quantity'])
            product.weight = float(request.POST['weight'])
            product.gender = request.POST['gender']
            
            # Update category, metal type, and stone type
            product.category_id = request.POST['id_category']
            product.metaltype_id = request.POST['metaltype']
            product.stonetype_id = request.POST['stonetype']
            
            # Handle image upload
            if 'image' in request.FILES:
                product.image = request.FILES['image']
            
            # Save the updated product
            product.save()
            messages.success(request, 'Product updated successfully!')
            return redirect('vendor_view_products')
        except Exception as e:
            messages.error(request, f'Error updating product: {str(e)}')
    
    # Fetch categories, metal types, and stone types for the form
    categories = Category.objects.all()
    metaltypes = Metaltype.objects.all()
    stonetypes = Stonetype.objects.all()
    
    context = {
        'product': product,
        'categories': categories,
        'metaltypes': metaltypes,
        'stonetypes': stonetypes,
    }
    
    return render(request, 'vendor/edit_product.html', context)

def vendor_pending_orders(request):
    if not request.user.is_authenticated or request.session.get('user_type') != 'vendor':
        messages.error(request, 'You need to log in as a vendor to access this page.')
        return redirect('login')
    
    vendor = get_object_or_404(Vendor, login_id=request.user.login_id)  # Adjust based on your user model
    pending_orders = RestockRequest.objects.filter(
        product__vendor=vendor,
        status='Pending'
    ).select_related('product')
    
    return render(request, 'vendor/pending_orders.html', {
        'pending_orders': pending_orders
    })


def vendor_order_history(request):
    if not request.session.get('user_type') == 'vendor':
        messages.error(request, 'You need to log in as a supplier to access this page.')
        return redirect('login')
    
    completed_orders = RestockRequest.objects.filter(
        product__supplier=request.user.vendor
    ).exclude(status='Pending').order_by('-requested_date')
    
    return render(request, 'vendor/order_history.html', {
        'completed_orders': completed_orders
    })

def handle_restock_request(request, request_id):
    if not request.session.get('user_type') == 'vendor':
        return JsonResponse({'success': False, 'error': 'Unauthorized'})
    
    try:
        restock_request = get_object_or_404(RestockRequest, id=request_id)
        
        action = request.POST.get('action')
        if action == 'accept':
            restock_request.status = 'Accepted'
            restock_request.save()
            # Create a payment request for the admin
            PaymentRequest.objects.create(
                vendor=restock_request.product.vendor,
                amount=restock_request.requested_quantity * restock_request.product.price,
                status='Pending'
            )
            return JsonResponse({'success': True, 'message': 'Restock request accepted and payment request created.'})
        
        elif action == 'reject':
            restock_request.status = 'Declined'
            restock_request.save()
            return JsonResponse({'success': True, 'message': 'Restock request declined.'})
        
    except Exception as e:
        print(f"Error handling restock request: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)})

@require_POST
def vendor_delete_product(request, product_id):
    if not request.session.get('user_type') == 'vendor':
        return JsonResponse({'success': False, 'error': 'Unauthorized'})
    
    try:
        product = get_object_or_404(VendorProduct, pk=product_id, vendor__login_id=request.session['login_id'])
        product.status = False  # Soft delete
        product.save()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

from django.shortcuts import render, get_object_or_404
from .models import Vendor

def vendor_restock_requests(request):
    if 'login_id' not in request.session or request.session.get('user_type') != 'vendor':
        return redirect('login')

    vendor = get_object_or_404(Vendor, login_id=request.session['login_id'])
    # Correctly filter restock requests based on the vendor
    restock_requests = RestockRequest.objects.filter(product__vendor=vendor, status='Pending')

    context = {
        'vendor': vendor,
        'restock_requests': restock_requests,
    }

    return render(request, 'vendor/restock_requests.html', context)

from django.shortcuts import render, get_object_or_404
from .models import Order, Vendor

def vendor_declined_orders(request):
    if 'login_id' not in request.session or request.session.get('user_type') != 'vendor':
        return redirect('login')

    vendor = get_object_or_404(Vendor, login_id=request.session['login_id'])
    declined_orders = Order.objects.filter(user__login=vendor.login, status='Cancelled')  # Adjust the filter as needed

    context = {
        'vendor': vendor,
        'declined_orders': declined_orders,
    }

    return render(request, 'vendor/declined_orders.html', context)

from django.shortcuts import render, get_object_or_404
from .models import Vendor, Order

def vendor_payment_details(request):
    if 'login_id' not in request.session or request.session.get('user_type') != 'vendor':
        return redirect('login')

    vendor = get_object_or_404(Vendor, login_id=request.session['login_id'])
    # Fetch payment details related to the vendor's orders
    payment_details = Order.objects.filter(user__login=vendor.login)  # Adjust the filter as needed

    context = {
        'vendor': vendor,
        'payment_details': payment_details,
    }

    return render(request, 'vendor/payment_details.html', context)

@require_POST
def vendor_toggle_product_status(request, product_id):
    if not request.session.get('user_type') == 'vendor':
        return JsonResponse({'success': False, 'error': 'Unauthorized'})
    
    try:
        product = get_object_or_404(VendorProduct, pk=product_id, vendor__login_id=request.session['login_id'])
        product.status = not product.status  # Toggle the status
        product.save()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@require_POST
def vendor_restock_product(request, product_id):
    if not request.session.get('user_type') == 'admin':
        return JsonResponse({'success': False, 'error': 'Unauthorized'})
    
    try:
        # Get the product using product_id
        product = get_object_or_404(Product, product_id=product_id)
        
        # Get the requested quantity from the request body
        data = json.loads(request.body)
        requested_quantity = int(data.get('requested_quantity', 0))  # Convert to integer

        # Check if a restock request already exists for this product
        restock_request, created = RestockRequest.objects.get_or_create(
            product=product,
            defaults={'requested_quantity': requested_quantity, 'status': 'Pending'}
        )

        if not created:
            # If the request already exists, update the requested quantity to the new value
            restock_request.requested_quantity = requested_quantity
            restock_request.save()

        # Log the request
        print(f'Restock request for product {product.product_name} set to quantity {requested_quantity}')
        
        return JsonResponse({
            'success': True,
            'message': 'Restock request processed successfully'
        })
    except Product.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Product not found'
        })
    except ValueError as ve:
        return JsonResponse({
            'success': False,
            'error': f'Invalid quantity: {str(ve)}'
        })
    except Exception as e:
        print(f"Error in restock request: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@require_POST
def vendor_cancel_order(request, product_id):
    if not request.session.get('user_type') == 'vendor':
        return JsonResponse({'success': False, 'error': 'Unauthorized'})
    
    try:
        product = get_object_or_404(Product, product_id=product_id)
        
        # Logic to cancel the order (e.g., update status in the database)
        # Assuming you have a way to mark the order as cancelled
        # This could involve updating a status field in the relevant model
        
        print(f'Order for product {product.product_name} has been cancelled.')

        # Send notification to the vendor
        vendor_email = product.vendor.email  # Assuming the vendor has an email field
        subject = f'Order Cancellation Notification for {product.product_name}'
        message = f'Dear Vendor,\n\nThe order for the product "{product.product_name}" is no longer needed for the meantime.\n\nThank you.'
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,  # Your default email from settings
            [vendor_email],
            fail_silently=False,
        )
        
        return JsonResponse({'success': True, 'message': 'Order cancelled successfully and notification sent to the vendor.'})
    except Exception as e:
        print(f"Error cancelling order: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)})

@require_POST
def accept_restock_request(request, request_id):
    if not request.session.get('user_type') == 'vendor':
        return JsonResponse({'success': False, 'error': 'Unauthorized'})
    
    try:
        restock_request = get_object_or_404(RestockRequest, id=request_id)
        restock_request.status = 'Accepted'
        restock_request.save()

        # Create a payment request for the admin
        PaymentRequest.objects.create(
            vendor=restock_request.product.vendor,
            amount=restock_request.requested_quantity * restock_request.product.price,  # Assuming price is available
            status='Pending'
        )

        return JsonResponse({'success': True, 'message': 'Restock request accepted and payment request created.'})
    except Exception as e:
        print(f"Error accepting restock request: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)})

@require_POST
def process_payment(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        payment_id = data.get('payment_id')
        amount = data.get('amount')
        date = data.get('date')
        product_name = data.get('product_name')
        quantity = data.get('quantity')
        payment_type = data.get('payment_type')

        # Create a new VendorPayment entry
        try:
            vendor_payment = VendorPayment.objects.create(
                payment_id=payment_id,
                amount=amount,
                date=date,
                product_name=product_name,
                quantity=quantity,
                payment_type=payment_type,
                status='Completed'  # Set status to completed
            )

            # Update the corresponding PaymentRequest status
            payment_request = PaymentRequest.objects.get(id=window.currentPaymentId)
            payment_request.status = 'Completed'
            payment_request.save()

            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'})

from django.http import JsonResponse

def update_payment_status(request, payment_id):
    if request.method == 'POST':
        data = json.loads(request.body)
        status = data.get('status')

        try:
            payment_request = PaymentRequest.objects.get(id=payment_id)
            payment_request.status = status
            payment_request.save()
            return JsonResponse({'status': 'success'})
        except PaymentRequest.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Payment request not found.'})

    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'})

def view_new_products(request):
    products = VendorProduct.objects.all().order_by('-created_at')  # Assuming 'created_at' is the field for the date added
    return render(request, 'admin/view_new_products.html', {'products': products})

@require_POST
def send_purchase_request(request):
    data = json.loads(request.body)
    product_id = data.get('product_id')
    quantity = data.get('quantity')

    # Logic to send the purchase request to the vendor
    # This could involve creating a new OrderRequest model or similar
    # For example:
    # OrderRequest.objects.create(product_id=product_id, quantity=quantity, vendor=vendor)

    return JsonResponse({'status': 'success'})

from django.http import JsonResponse

# Initialize the image search system
jewelry_search = JewelryImageSearch()

def search_by_image(request):
    if request.method == 'POST' and request.FILES.get('image'):
        try:
            # Get the uploaded image
            uploaded_file = request.FILES['image']
            
            # Read and validate the image
            if isinstance(uploaded_file, InMemoryUploadedFile):
                img = Image.open(io.BytesIO(uploaded_file.read()))
            else:
                img = Image.open(uploaded_file)
            
            # Convert to RGB if necessary
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Extract features from the uploaded image
            query_features = jewelry_search.extract_features(img)
            
            # Get all active products
            products = Product.objects.filter(is_active=True)
            
            # Calculate similarity scores
            similarities = []
            for product in products:
                try:
                    # Get cached features or compute new ones
                    cache_key = f'product_features_{product.product_id}'  # Changed from id to product_id
                    product_features = cache.get(cache_key)
                    
                    if product_features is None:
                        product_img = Image.open(product.images.path)
                        if product_img.mode != 'RGB':
                            product_img = product_img.convert('RGB')
                        product_features = jewelry_search.extract_features(product_img)
                        cache.set(cache_key, product_features.tobytes(), timeout=86400)  # Cache for 24 hours
                    else:
                        product_features = np.frombuffer(product_features, dtype=np.float32)
                    
                    # Compute similarity
                    similarity = jewelry_search.compute_similarity(query_features, product_features)
                    
                    # Only include products with similarity above threshold
                    if similarity > 0.5:  # Adjust threshold as needed
                        similarities.append((product, similarity))
                        
                except Exception as e:
                    logging.error(f"Error processing product {product.product_id}: {str(e)}")
                    continue
            
            # Sort by similarity and get top results
            similarities.sort(key=lambda x: x[1], reverse=True)
            top_results = similarities[:12]  # Adjust number of results as needed
            
            # Prepare response
            results = [
                {
                    'id': product.product_id,  # Changed from id to product_id
                    'name': product.product_name,
                    'image_url': product.images.url,
                    'price': str(product.price),
                    'similarity_score': float(score),
                    'category': product.category.name if product.category else None,
                }
                for product, score in top_results
            ]
            
            return JsonResponse({
                'success': True,
                'results': results,
                'total_matches': len(similarities)
            })
            
        except Exception as e:
            logging.exception("Error in image search")
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({
        'success': False,
        'error': 'Invalid request'
    })


import google.generativeai as genai
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from django.shortcuts import render
from google.cloud import vision
import os
from django.conf import settings
import io

# Use environment variables or Django settings for API configuration
genai.configure(api_key=settings.GOOGLE_API_KEY)

@csrf_exempt
def get_response(request):
    try:
        if request.method != 'POST':
            return JsonResponse({'error': 'Only POST method is allowed'}, status=405)

        query = request.POST.get('query')
        if not query:
            return JsonResponse({'error': 'No query provided'}, status=400)

        # Handle image if present
        if 'image' in request.FILES:
            image_file = request.FILES['image']
            image_content = image_file.read()
            
            # Initialize Gemini Pro Vision model
            model = genai.GenerativeModel('gemini-1.5-pro')
            
            # Convert image to base64 and create image part
            image_parts = [
                {
                    "mime_type": image_file.content_type,
                    "data": image_content
                }
            ]
            
            # Create prompt with image context
            prompt = f"""You are a jewelry expert assistant. Analyze the provided image and answer the following question: {query}
            Please provide detailed information about the jewelry piece, including:
            - Type of jewelry
            - Materials used
            - Any visible gemstones
            - Condition assessment
            - Relevant care or maintenance advice
            
            Question: {query}"""
            
            # Generate response with image
            response = model.generate_content([prompt] + image_parts)
        else:
            # Text-only query using Gemini Pro
            model = genai.GenerativeModel('gemini-pro')
            prompt = f"""You are a jewelry expert assistant. Please answer the following question: {query}
            If the question is not related to jewelry, politely explain that you can only assist with jewelry-related queries.
            
            Question: {query}"""
            response = model.generate_content(prompt)

        return JsonResponse({
            'response': response.text
        })

    except Exception as e:
        print(f"Error in get_response: {str(e)}")
        return JsonResponse({
            'error': 'Error processing request',
            'details': str(e)
        }, status=500)

@csrf_exempt
def jwellery_view(request):
    return render(request, 'user/jewelry_assistant.html')

def is_jewelry_related(query):
    # Expanded list of jewelry-related keywords
    jewelry_keywords = {
        # General terms
        'jewelry', 'jewellery', 'jewel', 'accessory',
        # Types of jewelry
        'necklace', 'ring', 'bracelet', 'earring', 'pendant', 'brooch', 'anklet',
        'tiara', 'crown', 'chain', 'locket', 'charm', 'bangle', 'cuff',
        # Materials and gems
        'gold', 'silver', 'platinum', 'diamond', 'ruby', 'sapphire', 'emerald',
        'pearl', 'gem', 'stone', 'crystal', 'metal', 'precious',
        # Actions and maintenance
        'clean', 'polish', 'maintain', 'care', 'repair', 'resize', 'restore',
        'shine', 'fix', 'adjust', 'wash', 'store', 'keep',
        # Parts and components
        'clasp', 'setting', 'band', 'link', 'prong', 'backing'
    }
    
    # Convert query to lowercase for case-insensitive matching
    query_lower = query.lower()
    
    # Check for maintenance/cleaning related phrases first
    maintenance_phrases = [
        'how to clean', 'how do i clean', 'cleaning tips', 
        'maintenance', 'take care', 'caring for'
    ]
    
    if any(phrase in query_lower for phrase in maintenance_phrases):
        return True
    
    # Then check for jewelry keywords
    return any(keyword in query_lower for keyword in jewelry_keywords)

@csrf_exempt
def validate_image(request):
    try:
        if 'image' not in request.FILES:
            return JsonResponse({
                'error': 'No image file provided',
                'is_jewelry': False
            }, status=400)

        image_file = request.FILES['image']

        # Validate file size (5MB max)
        if image_file.size > 5 * 1024 * 1024:  # 5MB in bytes
            return JsonResponse({
                'error': 'Image size should be less than 5MB',
                'is_jewelry': False
            }, status=400)

        # Validate file type
        allowed_types = ['image/jpeg', 'image/png', 'image/jpg', 'image/webp']
        if image_file.content_type not in allowed_types:
            return JsonResponse({
                'error': 'Invalid file type. Please upload JPEG, PNG, or WebP',
                'is_jewelry': False
            }, status=400)

        try:
            # Update Vision API client initialization
            client_options = {'api_key': settings.GOOGLE_API_KEY}
            client = vision.ImageAnnotatorClient(client_options=client_options)

            # Read the image file
            content = image_file.read()
            image = vision.Image(content=content)

            # Perform label detection
            response = client.label_detection(image=image)
            labels = response.label_annotations

            # Keywords that indicate jewelry
            jewelry_keywords = {
                'jewelry', 'jewellery', 'necklace', 'ring', 'bracelet', 'earring',
                'pendant', 'gem', 'stone', 'diamond', 'gold', 'silver', 'platinum',
                'accessory', 'ornament', 'precious metal', 'pearl', 'gemstone',
                'chain', 'bangle', 'brooch', 'anklet', 'tiara', 'crown'
            }

            # Check if any of the detected labels match jewelry keywords
            detected_labels = {label.description.lower() for label in labels}
            is_jewelry = bool(detected_labels & jewelry_keywords)

            # Add confidence threshold
            if is_jewelry:
                # Check if any jewelry-related label has high confidence
                jewelry_confidence = max(
                    (label.score for label in labels 
                     if label.description.lower() in jewelry_keywords),
                    default=0
                )
                is_jewelry = jewelry_confidence > 0.7  # 70% confidence threshold

            return JsonResponse({
                'is_jewelry': is_jewelry,
                'detected_labels': list(detected_labels)
            })

        except Exception as e:
            print(f"Vision API Error: {str(e)}")  # Log the specific error
            return JsonResponse({
                'error': 'Error processing image with Vision API',
                'is_jewelry': False
            }, status=500)

    except Exception as e:
        print(f"General Error: {str(e)}")  # Log the specific error
        return JsonResponse({
            'error': str(e),
            'is_jewelry': False
        }, status=500)

@csrf_exempt
def validate_query(request):
    if request.method == 'POST':
        try:
            return JsonResponse({
                'is_jewelry_related': True  # Always allow queries to pass through
            })
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
    return JsonResponse({'error': 'Invalid request method'}, status=405)



# ///////////////////////////////////////////////////////////////////////////////////////////////////////////////
# admin side views

from django.shortcuts import render
from .models import Order  # Import your Order model

def view_all_orders(request):
    # Fetch all orders from the database
    orders = Order.objects.all()  # Adjust this query as needed (e.g., filter by user if necessary)

    context = {
        'orders': orders,
    }

    return render(request, 'admin/view_all_orders.html', context)

def view_payments(request):
    if 'login_id' not in request.session or request.session.get('user_type') != 'admin':
        return redirect('login')  # Redirect to login if not an admin
    
    # Fetch all orders to display payment details
    payments = Order.objects.filter(payment_status='Success').values(
        'user__name', 'payment_date', 'total_amount', 'payment_status'
    )
    
    context = {
        'payments': payments,
    }
    
    return render(request, 'admin/view_payments.html', context)  # Render the payments template

# ///////////////////////////////////////////////////////////////////////////////////////////////////////////////
