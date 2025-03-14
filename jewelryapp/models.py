from django.db import models
from django.utils import timezone
from django.core.cache import cache
import numpy as np
import logging
from PIL import Image
from jewelryapp.ml.image_search import jewelry_search  # Updated import
from .utils import get_current_metal_rate, get_diamond_rate  # Remove get_gemstone_rate from here
from .utils.price_calculator import PriceCalculator  # Add this import

# Initialize a calculator for gemstone rates
_calculator = PriceCalculator()

def get_gemstone_rate(stone_type, quality=None):
    """Get gemstone rate based on type and quality"""
    return _calculator.get_gemstone_price(stone_type, quality, 1.0)  # Get rate for 1 carat

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
    STONE_CHOICES = [
        ('diamond', 'Diamond'),
        ('ruby', 'Ruby'),
        ('sapphire', 'Sapphire'),
        ('emerald', 'Emerald')
    ]
    
    stonetype_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50, choices=STONE_CHOICES)

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
    images = models.ImageField(upload_to='pic/', default='')  # Main image
    image2 = models.ImageField(upload_to='pic/', blank=True, null=True)  # Additional image
    image3 = models.ImageField(upload_to='pic/', blank=True, null=True)  # Additional image
    image4 = models.ImageField(upload_to='pic/', blank=True, null=True)  # Additional image
    product_video = models.FileField(upload_to='product_videos/', blank=True, null=True)  # Video field
    metaltype = models.ForeignKey(Metaltype, on_delete=models.CASCADE, null=True, blank=True)
    stonetype = models.ForeignKey(Stonetype, on_delete=models.CASCADE, null=True, blank=True)
    home_delivery = models.BooleanField(default=False)
    store_pickup = models.BooleanField(default=False)
    try_at_home = models.BooleanField(default=False)
    bestselling = models.BooleanField(default=False)
    vendor = models.ForeignKey('Vendor', on_delete=models.CASCADE, null=True, blank=True)
    
    is_active = models.BooleanField(default=True)
    bis_hallmark = models.CharField(max_length=50, blank=True, null=True)  # BIS hallmark number
    making_charges = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    diamond_weight = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # in carats
    diamond_quality = models.CharField(max_length=50, blank=True, null=True)  # e.g., IJ-SI
    estimated_delivery = models.IntegerField(default=7)  # delivery time in days
    ratings = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    total_ratings = models.IntegerField(default=0)

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

    def calculate_metal_cost(self):
        try:
            # Get the metal type name from the related metaltype field
            metal_type = self.metaltype.name  # This should give 'Gold', 'Silver', or 'Platinum'
            current_rate = get_current_metal_rate(metal_type)
            return self.weight * current_rate
        except Exception as e:
            print(f"Error calculating metal cost: {e}")
            return 0

    def calculate_diamond_cost(self):
        """Calculate cost of diamonds"""
        if self.diamond_weight and self.diamond_quality:
            diamond_rate = get_diamond_rate(self.diamond_quality)
            return float(self.diamond_weight) * float(diamond_rate)
        return 0

    def calculate_total_price(self):
        """Calculate total price including metal, diamonds, and making charges"""
        metal_cost = self.calculate_metal_cost()
        diamond_cost = self.calculate_diamond_cost()
        return metal_cost + diamond_cost + float(self.making_charges)




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

class VendorPurchase(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ]

    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE)
    product_name = models.CharField(max_length=255)
    quantity = models.PositiveIntegerField()
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    expected_arrival = models.DateField()
    requested_arrival_date = models.DateField(null=True, blank=True)
    has_date_update_request = models.BooleanField(default=False)
    purchase_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    is_user_purchased = models.BooleanField(default=False)  # Track if a user has purchased this product
    user_purchased_count = models.PositiveIntegerField(default=0)  # Track number of items purchased by users
    payment = models.OneToOneField('VendorPayment', on_delete=models.SET_NULL, null=True, blank=True)
    payment_processed = models.BooleanField(default=False)  # Add this field

    def __str__(self):
        return f"Purchase of {self.product_name} from {self.vendor.business_name}"

    def update_purchase_count(self):
        """Update the count of user purchases and check if half quantity is reached"""
        self.user_purchased_count = Order.objects.filter(
            cart__items__product__vendor=self.vendor,
            status='Delivered'
        ).count()
        
        if self.user_purchased_count >= (self.quantity / 2) and not self.is_user_purchased:
            self.is_user_purchased = True
            # Create notification for admin
            Notification.objects.create(
                recipient=get_admin_user(),
                title='Payment Request Available',
                message=f'Half of the products from {self.vendor.business_name} have been purchased. Payment can be processed.',
                notification_type='payment_request',
                related_id=self.id
            )
        self.save()

class VendorPayment(models.Model):
    PAYMENT_PURPOSE_CHOICES = [
        ('purchase', 'Product Purchase'),
        ('restock', 'Restock Request')
    ]
    
    PAYMENT_TYPE_CHOICES = [
        ('advance', 'Advance Payment'),
        ('half', 'Half Payment'),
        ('post', 'Post Delivery Payment')
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('partial_paid', 'Partially Paid'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ]

    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE)
    payment_id = models.CharField(max_length=255, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    remaining_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    date = models.DateTimeField(auto_now_add=True)
    product_name = models.CharField(max_length=255, null=True)
    quantity = models.PositiveIntegerField(null=True)
    payment_purpose = models.CharField(max_length=20, choices=PAYMENT_PURPOSE_CHOICES, default='purchase')
    payment_type = models.CharField(max_length=50, choices=PAYMENT_TYPE_CHOICES, default='post')
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')

    def save(self, *args, **kwargs):
        if not self.pk:  # Only on creation
            self.remaining_amount = self.amount - self.amount_paid
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Payment for {self.product_name} - {self.get_status_display()}"

class DateChangeRequest(models.Model):
    """Model for tracking vendor requests to change delivery dates"""
    purchase = models.ForeignKey('VendorPurchase', on_delete=models.CASCADE)
    requested_date = models.DateField()
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ], default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Date change request for purchase #{self.purchase.id}'

# Add this after the Product model
class Review(models.Model):
    RATING_CHOICES = [
        (1, '1 Star'),
        (2, '2 Stars'),
        (3, '3 Stars'),
        (4, '4 Stars'),
        (5, '5 Stars'),
    ]
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(Tbl_user, on_delete=models.CASCADE)
    rating = models.IntegerField(choices=RATING_CHOICES)
    comment = models.TextField()
    image = models.ImageField(upload_to='review_images/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        # Ensure one review per user per product
        unique_together = ('product', 'user')

    def __str__(self):
        return f"{self.user.name}'s review on {self.product.product_name}"


class MetalPurity(models.Model):
    metal_type = models.ForeignKey(Metaltype, on_delete=models.CASCADE)
    purity_value = models.CharField(max_length=10)  # e.g., "24K", "999"
    purity_percentage = models.DecimalField(max_digits=5, decimal_places=2)  # e.g., 99.9
    description = models.CharField(max_length=100)  # e.g., "99.9% Pure Gold"

    def __str__(self):
        return f"{self.purity_value} ({self.description})"

    class Meta:
        unique_together = ('metal_type', 'purity_value')

class StonePurity(models.Model):
    stone_type = models.ForeignKey(Stonetype, on_delete=models.CASCADE)
    purity_grade = models.CharField(max_length=20)  # e.g., "VS1", "SI1" for diamonds, "AAA" for other gems
    clarity_rating = models.CharField(max_length=50)  # e.g., "Very Slightly Included", "Slightly Included"
    description = models.CharField(max_length=200)  # Detailed description of the quality grade
    price_multiplier = models.DecimalField(max_digits=5, decimal_places=2)  # Price factor based on quality

    def __str__(self):
        return f"{self.stone_type.name} - {self.purity_grade} ({self.clarity_rating})"
        

    class Meta:
        unique_together = ('stone_type', 'purity_grade')
        verbose_name_plural = "Stone Purities"

class VendorProduct(models.Model):
    vendor_product_id = models.AutoField(primary_key=True)
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='vendor_products')
    product_name = models.CharField(max_length=255)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    product_description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    is_approved = models.BooleanField(default=False)
    approval_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.product_name} by {self.vendor.business_name}"

class VendorProductMetal(models.Model):
    vendor_product = models.OneToOneField(VendorProduct, on_delete=models.CASCADE, related_name='metal_details')
    metal_type = models.ForeignKey(Metaltype, on_delete=models.CASCADE)
    purity = models.ForeignKey(MetalPurity, on_delete=models.CASCADE)
    weight = models.DecimalField(max_digits=8, decimal_places=2)  # Weight in grams
    rate_per_gram = models.DecimalField(max_digits=10, decimal_places=2)
    total_cost = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.metal_type.name} - {self.weight}g at {self.purity.purity_value}"

    def save(self, *args, **kwargs):
        # Calculate total cost before saving
        purity_factor = self.purity.purity_percentage / 100
        self.total_cost = self.weight * self.rate_per_gram * purity_factor
        super().save(*args, **kwargs)

class VendorProductStone(models.Model):
    vendor_product = models.ForeignKey(VendorProduct, on_delete=models.CASCADE, related_name='stones')
    stone_type = models.ForeignKey(Stonetype, on_delete=models.CASCADE)
    weight = models.DecimalField(max_digits=7, decimal_places=3)  # Weight in carats
    count = models.PositiveIntegerField()
    quality = models.CharField(max_length=50)  # e.g., "D-IF", "pigeon-blood"
    rate_per_carat = models.DecimalField(max_digits=10, decimal_places=2)
    total_cost = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.count} {self.stone_type.name}(s) - {self.weight} carats"

    def save(self, *args, **kwargs):
        # Calculate total cost before saving
        self.total_cost = self.weight * self.rate_per_carat * self.count
        super().save(*args, **kwargs)

class VendorProductAttribute(models.Model):
    vendor_product = models.ForeignKey(VendorProduct, on_delete=models.CASCADE, related_name='attributes')
    attribute_name = models.CharField(max_length=100)
    attribute_value = models.CharField(max_length=255)
    datatype = models.CharField(max_length=50, choices=[
        ('string', 'String'),
        ('number', 'Number'),
        ('date', 'Date'),
        ('boolean', 'Boolean'),
    ], default='string')

    def __str__(self):
        return f"{self.attribute_name}: {self.attribute_value} for {self.vendor_product.product_name}"

    class Meta:
        unique_together = ('vendor_product', 'attribute_name')

class VendorProductPricing(models.Model):
    vendor_product = models.OneToOneField(VendorProduct, on_delete=models.CASCADE, related_name='pricing_details')
    metal_cost = models.DecimalField(max_digits=12, decimal_places=2)
    stone_cost = models.DecimalField(max_digits=12, decimal_places=2)
    making_charges_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    making_charges = models.DecimalField(max_digits=12, decimal_places=2)
    total_price = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"Pricing for {self.vendor_product.product_name}"

    def save(self, *args, **kwargs):
        # Calculate making charges and total price before saving
        self.making_charges = (self.metal_cost * self.making_charges_percentage) / 100
        self.total_price = self.metal_cost + self.stone_cost + self.making_charges
        super().save(*args, **kwargs)

class VendorProductImage(models.Model):
    vendor_product = models.OneToOneField(VendorProduct, on_delete=models.CASCADE, related_name='images')
    main_image = models.ImageField(upload_to='vendor_products/')
    image2 = models.ImageField(upload_to='vendor_products/', blank=True, null=True)
    image3 = models.ImageField(upload_to='vendor_products/', blank=True, null=True)
    image4 = models.ImageField(upload_to='vendor_products/', blank=True, null=True)
    product_video = models.FileField(upload_to='vendor_product_videos/', blank=True, null=True)

    def __str__(self):
        return f"Images for {self.vendor_product.product_name}"

class VendorAdditionalDetails(models.Model):
    GENDER_CHOICES = [
        ('Men', 'Men'),
        ('Women', 'Women'),
        ('Unisex', 'Unisex'),
        ('Kids', 'Kids'),
        ('Baby', 'Baby')
    ]

    vendor_product = models.OneToOneField(VendorProduct, on_delete=models.CASCADE, related_name='additional_details')
    stock_quantity = models.PositiveIntegerField()
    bis_hallmark = models.CharField(max_length=50, blank=True, null=True)
    estimated_delivery = models.PositiveIntegerField(default=7)  # in days
    gender = models.CharField(max_length=6, choices=GENDER_CHOICES, default='Unisex')
    home_delivery = models.BooleanField(default=False)
    store_pickup = models.BooleanField(default=False)
    try_at_home = models.BooleanField(default=False)

    def __str__(self):
        return f"Additional details for {self.vendor_product.product_name}"
