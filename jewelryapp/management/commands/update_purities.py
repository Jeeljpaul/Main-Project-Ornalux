from django.core.management.base import BaseCommand
from jewelryapp.models import MetalPurity, StonePurity, Metaltype, Stonetype
from jewelryapp.utils.gemini_helper import get_metal_purities, get_stone_purities
from django.db import transaction

class Command(BaseCommand):
    help = 'Update metal and stone purities using Gemini API'

    def handle(self, *args, **kwargs):
        self.stdout.write('Starting purity update...')
        
        # Update metal purities
        try:
            metal_data = get_metal_purities()
            if metal_data:
                self._update_metal_purities(metal_data)
                self.stdout.write(self.style.SUCCESS('Successfully updated metal purities'))
            else:
                self.stdout.write(self.style.WARNING('No metal data received'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error updating metal purities: {str(e)}'))

        # Update stone purities
        try:
            stone_data = get_stone_purities()
            if stone_data:
                self._update_stone_purities(stone_data)
                self.stdout.write(self.style.SUCCESS('Successfully updated stone purities'))
            else:
                self.stdout.write(self.style.WARNING('No stone data received'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error updating stone purities: {str(e)}'))

    @transaction.atomic
    def _update_metal_purities(self, metal_data):
        """
        Update metal purities in the database
        """
        for metal_name, purities in metal_data.items():
            metal_type, _ = Metaltype.objects.get_or_create(name=metal_name.capitalize())
            
            for purity_info in purities:
                MetalPurity.objects.update_or_create(
                    metal_type=metal_type,
                    purity_value=purity_info['purity'],
                    defaults={
                        'purity_percentage': purity_info['percentage'],
                        'description': f"{purity_info['percentage']}% Pure {metal_name.capitalize()}"
                    }
                )

    @transaction.atomic
    def _update_stone_purities(self, stone_data):
        """
        Update stone purities in the database
        """
        for stone_name, grades in stone_data.items():
            stone_type, _ = Stonetype.objects.get_or_create(name=stone_name.capitalize())
            
            for grade_info in grades:
                StonePurity.objects.update_or_create(
                    stone_type=stone_type,
                    purity_grade=grade_info['grade'],
                    defaults={
                        'clarity_rating': grade_info['clarity'],
                        'description': f"{grade_info['clarity']} - {stone_name.capitalize()}",
                        'price_multiplier': grade_info['multiplier']
                    }
                ) 