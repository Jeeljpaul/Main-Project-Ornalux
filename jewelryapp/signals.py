from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Product, RestockRequest

@receiver(post_save, sender=Product)
def check_product_stock(sender, instance, **kwargs):
    if instance.stock_quantity <= 5:
        # Create restock request if one doesn't exist
        existing_request = RestockRequest.objects.filter(
            product=instance,
            status='Pending'
        ).exists()
        
        if not existing_request:
            RestockRequest.objects.create(
                product=instance,
                quantity=10  # Default restock quantity
            ) 