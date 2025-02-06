from django.core.management.base import BaseCommand
from jewelryapp.models import Product
from tqdm import tqdm

class Command(BaseCommand):
    help = 'Precompute and cache image features for all products'

    def handle(self, *args, **options):
        products = Product.objects.filter(is_active=True)
        total = products.count()
        
        self.stdout.write(f"Computing features for {total} products...")
        
        success_count = 0
        with tqdm(total=total) as pbar:
            for product in products:
                if product.compute_and_cache_features():
                    success_count += 1
                pbar.update(1)
        
        self.stdout.write(self.style.SUCCESS(
            f"Successfully computed features for {success_count}/{total} products"
        )) 