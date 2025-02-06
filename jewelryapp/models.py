from django.db import models
from django.utils import timezone
from django.core.cache import cache
import numpy as np
import logging
from PIL import Image
from jewelryapp.ml.image_search import jewelry_search  # Updated import

class Tbl_login(models.Model):
    login_id = models.AutoField(primary_key=True)
    email = models.CharField(max_length=30, unique=True)  # Ensure email is unique
    password = models.CharField(max_length=30)
    reset_token = models.CharField(max_length=100, blank=True, null=True)
    status = models.BooleanField(default=True)
    last_login = models.DateTimeField(null=True, blank=True)
    last_logout = models.DateTimeField(null=True, blank=True)
    login_count = models.IntegerField(default=0)

    def login(self):
        """ Logs the user in by updating the login timestamp, status, and login count. """
        self.status = True  # Set status to True on login
        self.last_login = timezone.now()
        self.login_count += 1
        self.save()


    def __str__(self):
        return self.email


class Tbl_user(models.Model):
    user_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50)
    dob = models.DateField()
    phone = models.CharField(max_length=15)
    login = models.OneToOneField(Tbl_login, on_delete=models.CASCADE)  # One-to-One relationship
    status = models.BooleanField(default=True)


    def __str__(self):
        return self.name


class Tbl_staff(models.Model):
    ROLE_CHOICES = [
        ('Sales', 'Sales'),
        ('Delivery', 'Delivery'),
        ('Try at home', 'Try at home')
    ]
    
    staff_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    role = models.CharField(max_length=50, choices=ROLE_CHOICES)
    contact_details = models.CharField(max_length=15)
    login = models.ForeignKey(Tbl_login, on_delete=models.CASCADE)
    status = models.BooleanField(default=True)


    def __str__(self):
        return self.name

class Category(models.Model):
    category_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    

    def __str__(self):
        return self.name

class CategoryAttribute(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='attributes')
    name = models.CharField(max_length=100)
    datatype = models.CharField(max_length=50, choices=[
        ('string', 'String'),
        ('number', 'Number'),
        ('date', 'Date'),
        ('boolean', 'Boolean'),
    ],
     default='string'
    )



    def __str__(self):
        return f"{self.name} ({self.category.name}) ({self.datatype})"
    
class Metaltype(models.Model):
    metaltype_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Stonetype(models.Model):
    stonetype_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


# Model for Product
class Product(models.Model):
    GENDER_CHOICES = [
        ('Men', 'Men'),
        ('Women', 'Women'),
        ('Unisex', 'Unisex'),
        ('Kids', 'Kids'),
        ('Baby', 'Baby')
    ]

    product_id = models.AutoField(primary_key=True)
    product_name = models.CharField(max_length=255)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, null=True, blank=True)
    product_description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_quantity = models.PositiveIntegerField()
    weight = models.DecimalField(max_digits=5, decimal_places=2)
    gender = models.CharField(max_length=6, choices=GENDER_CHOICES, default='Unisex')
    occasion = models.CharField(max_length=255)
    images = models.ImageField(upload_to='pic/', default='')
    metaltype = models.ForeignKey(Metaltype, on_delete=models.CASCADE, null=True, blank=True)
    stonetype = models.ForeignKey(Stonetype, on_delete=models.CASCADE, null=True, blank=True)
    home_delivery = models.BooleanField(default=False)
    store_pickup = models.BooleanField(default=False)
    try_at_home = models.BooleanField(default=False)
    bestselling = models.BooleanField(default=False)
    vendor = models.ForeignKey('Vendor', on_delete=models.CASCADE, null=True, blank=True)
    
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.product_name
    
    def compute_and_cache_features(self):
        """
        Compute and cache image features
        """
        try:
            if self.images:
                img = Image.open(self.images.path)
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                    
                features = jewelry_search.extract_features(img)
                cache_key = f'product_features_{self.product_id}'
                cache.set(cache_key, features.tobytes(), timeout=86400)  # Cache for 24 hours
                return True
        except Exception as e:
            logging.error(f"Error computing features for product {self.id}: {str(e)}")
            return False




class Vendor(models.Model):
    vendor_id = models.AutoField(primary_key=True)
    business_name = models.CharField(max_length=200)
    email = models.EmailField(unique=True)
    contact = models.CharField(max_length=15)
    login = models.OneToOneField(Tbl_login, on_delete=models.CASCADE)
    documents = models.FileField(upload_to='vendor_documents/')
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.BooleanField(default=True)

    def __str__(self):
        return self.business_name


class VendorProduct(models.Model):
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE)
    product_name = models.CharField(max_length=255)
    product_description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_quantity = models.IntegerField()
    weight = models.FloatField()
    gender = models.CharField(max_length=50)
    image = models.ImageField(upload_to='vendor_products/')  # Adjust the upload path as needed
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    metaltype = models.ForeignKey(Metaltype, on_delete=models.CASCADE)
    stonetype = models.ForeignKey(Stonetype, on_delete=models.CASCADE, null=True)  # Allow null if needed
    created_at = models.DateTimeField(auto_now_add=True)  # Automatically set the field to now when the object is created
    updated_at = models.DateTimeField(auto_now=True)  # Automatically update the field when the object is updated
    status = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Vendor Product"
        verbose_name_plural = "Vendor Products"

    def __str__(self):
        return self.product_name




class ProductAttribute(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='attributes')
    attribute_name = models.CharField(max_length=100)
    attribute_value = models.CharField(max_length=255)
    def __str__(self):
        return f"{self.attribute_name}: {self.attribute_value} for {self.product.product_name}"
    


class Cart(models.Model):
    cart_id = models.AutoField(primary_key=True)
    login = models.OneToOneField(Tbl_login, on_delete=models.CASCADE, related_name='cart')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart for {self.login.email}"

    def total_price(self):
        return sum(item.product.price * item.quantity for item in self.items.all())

class CartItem(models.Model):
    cartitem_id = models.AutoField(primary_key=True)
    cart = models.ForeignKey(Cart, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    status = models.BooleanField(default=True)  # True if active in cart, False if removed

    def __str__(self):
        return f"{self.quantity} of {self.product.product_name} in cart"

    def get_total_price(self):
        return self.product.price * self.quantity



    def __str__(self):
        return f"{self.quantity} of {self.product.product_name} in cart"
    


class Wishlist(models.Model):
    wishlist_id = models.AutoField(primary_key=True)
    login = models.ForeignKey(Tbl_login, on_delete=models.CASCADE, related_name='wishlists')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Wishlist of User ID: {self.login.email}"

class WishlistItem(models.Model):
    wishlist = models.ForeignKey(Wishlist, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product.product_name} in Wishlist ID: {self.wishlist.wishlist_id}"


class Booking(models.Model):
    booking_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(Tbl_user, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    booking_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed')
    ], default='pending')
    address = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return f"Booking {self.booking_id} by {self.user.name} for {self.product.product_name} on {self.booking_date}"


class Billing(models.Model):
    user = models.ForeignKey(Tbl_user, on_delete=models.CASCADE)  # Change to ForeignKey
    house_name = models.CharField(max_length=255)
    postal_address = models.CharField(max_length=255)
    city = models.CharField(max_length=50)
    district = models.CharField(max_length=50)
    state = models.CharField(max_length=50)
    pincode = models.CharField(max_length=6)

    def __str__(self):
        return f"{self.house_name}, {self.city}"

class Order(models.Model):
    user = models.ForeignKey(Tbl_user, on_delete=models.CASCADE)
    billing = models.ForeignKey(Billing, on_delete=models.SET_NULL, null=True)
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Processing', 'Processing'),
        ('Shipped', 'Shipped'),
        ('Delivered', 'Delivered'),
        ('Cancelled', 'Cancelled'),
        ('Returned', 'Returned'),
    ]
    status = models.CharField(max_length=50, choices=[
        ('Confirmed', 'Confirmed'),
        ('Shipped', 'Shipped'),
        ('Out for Delivery', 'Out for Delivery'),
        ('Delivered', 'Delivered'),
        ('Cancelled', 'Cancelled')
    ], default='Pending')

    PAYMENT_STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Success', 'Success'),
        ('Failed', 'Failed')
    ]
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='Pending')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    razorpay_order_id = models.CharField(max_length=255, null=True, blank=True)
    payment_date = models.DateTimeField(null=True, blank=True)
    order_date = models.DateTimeField(auto_now_add=True)
    confirmed_date = models.DateTimeField(null=True, blank=True)
    shipped_date = models.DateTimeField(null=True, blank=True)
    out_for_delivery_date = models.DateTimeField(null=True, blank=True)
    delivery_date = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        # Set initial status to Confirmed when payment is successful
        if self.payment_status == 'Success' and not self.status:
            self.status = 'Confirmed'
            self.confirmed_date = self.payment_date
        super().save(*args, **kwargs)

    def _str_(self):
        return f"Order {self.id} by {self.user.email} - Status: {self.status}"

    def mark_payment_successful(self, payment_id):
        """Mark payment as successful, store order items, and clear the cart."""
        self.payment_status = 'Success'
        self.razorpay_order_id = payment_id
        self.payment_date = timezone.now()
        self.save()

        # Copy each item from CartItem to OrderItem and reduce stock accordingly
        for cart_item in self.cart.items.all():
            if cart_item.batch.stock_quantity < cart_item.quantity:
                raise ValueError(f"Insufficient stock for {cart_item.batch.product.name}. Only {cart_item.batch.stock_quantity} available.")

            # Update stock quantity
            cart_item.batch.stock_quantity -= cart_item.quantity
            cart_item.batch.save()

            OrderItem.objects.create(
                order=self,
                product=cart_item.batch.product.name,
                batch=cart_item.batch,
                quantity=cart_item.quantity,
                price=cart_item.batch.price,
                discount=getattr(cart_item.batch, 'discount', 0)
            )

        # Mark the cart as completed
        self.cart.is_completed = True
        self.cart.save()


# OrderItem Model
class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='order_items')
    product = models.CharField(max_length=255)  # Store product name for reference
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Store price at the time of order

    def _str_(self):
        return f"{self.product} - Quantity: {self.quantity} - Price: {self.price}"

    def get_total_price(self):
        return self.price * self.quantity

    def get_total_price_with_discount(self):
        return self.get_total_price() - ((self.get_total_price() * self.discount) / 100)

class PickupAddress(models.Model):  # New table for pickup addresses
    user = models.ForeignKey(Tbl_user, on_delete=models.CASCADE)  # Connect to Tbl_user
    house_name = models.CharField(max_length=255)
    postal_address = models.CharField(max_length=255)
    city = models.CharField(max_length=50)
    district = models.CharField(max_length=50)
    state = models.CharField(max_length=50)
    pincode = models.CharField(max_length=6)
    phone = models.CharField(max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)  # To track when the record was added

    def __str__(self):
        return f"{self.house_name}, {self.city}, {self.state}"

class PickupDetails(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(Tbl_user, on_delete=models.CASCADE)
    name = models.CharField(max_length=100) 
    phone = models.CharField(max_length=15)  
    email = models.EmailField()  
    place = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')

    def __str__(self):
        return f"{self.name} - {self.place} - {self.status}"


class StoreVisit(models.Model):
    STATUS_CHOICES = [
        ('Scheduled', 'Scheduled'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(Tbl_user, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=10)
    date = models.DateField()
    time = models.TimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Scheduled')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.date} at {self.time} ({self.status})"

class VendorProductAttribute(models.Model):
    vendor_product = models.ForeignKey(VendorProduct, on_delete=models.CASCADE, related_name='attributes')
    attribute_name = models.CharField(max_length=255)  # Name of the attribute (e.g., "Color", "Size")
    attribute_value = models.CharField(max_length=255)  # Value of the attribute (e.g., "Red", "Large")

    class Meta:
        verbose_name = "Vendor Product Attribute"
        verbose_name_plural = "Vendor Product Attributes"

    def __str__(self):
        return f"{self.attribute_name}: {self.attribute_value} for {self.vendor_product.product_name}"

class RestockRequest(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    requested_quantity = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=[
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Declined', 'Declined')
    ], default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Restock Request for {self.product.product_name}"

class VendorPayment(models.Model):
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE)
    payment_id = models.CharField(max_length=255, null=True)  # Make payment_id nullable
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateTimeField(auto_now_add=True)
    product_name = models.CharField(max_length=255, null=True)  # Make product_name nullable
    quantity = models.PositiveIntegerField(null=True)  # Make quantity nullable
    payment_type = models.CharField(max_length=50, choices=[('advance', 'Advance'), ('post', 'Post')], null=True)  # Make payment_type nullable
    status = models.CharField(max_length=20, default='Pending')  # Default status can be 'Pending'

    def __str__(self):
        return f"Payment of {self.amount} for {self.product_name}"

class PaymentRequest(models.Model):
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=[
        ('Pending', 'Pending'),
        ('Completed', 'Completed'),
        ('Failed', 'Failed')
    ], default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment request of {self.amount} for {self.vendor.business_name}"


