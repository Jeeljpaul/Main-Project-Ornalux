from django.conf import settings
from datetime import datetime

class PriceCalculator:
    def __init__(self):
        # Initialize with default rates from settings
        self.gold_rate = 5500  # Default gold rate per gram
        self.making_charges_percentage = 8
        self.gst_percentage = 3
        
        # Fixed rates for diamonds and stones
        self.diamond_rates = {
            'D-IF': 1000000,    # Flawless
            'E-VVS1': 800000,   # Very Very Slightly Included 1
            'F-VVS2': 700000,   # Very Very Slightly Included 2
            'G-VS1': 600000,    # Very Slightly Included 1
            'H-VS2': 500000,    # Very Slightly Included 2
            'I-SI1': 400000,    # Slightly Included 1
            'J-SI2': 300000,    # Slightly Included 2
            'default': 300000   # Default rate
        }
        
        self.gemstone_rates = {
            'ruby': {
                'pigeon-blood': 50000,
                'vivid-red': 35000,
                'medium-red': 25000,
                'light-red': 15000,
                'default': 15000
            },
            'sapphire': {
                'royal-blue': 45000,
                'cornflower-blue': 35000,
                'medium-blue': 25000,
                'light-blue': 15000,
                'default': 15000
            },
            'emerald': {
                'muzo-green': 40000,
                'vivid-green': 30000,
                'medium-green': 20000,
                'light-green': 12000,
                'default': 12000
            },
            'pearl': {
                'aaa': 15000,
                'aa': 10000,
                'a': 7000,
                'b': 4000,
                'default': 4000
            },
            'default': 5000  # Default rate for unknown stones
        }

    def get_gold_rate(self):
        """Get current gold rate"""
        return self.gold_rate
    
    def get_diamond_price(self, quality, weight):
        """Calculate diamond price based on quality and weight"""
        try:
            weight = float(weight or 0)
            base_rate = self.diamond_rates.get(quality, self.diamond_rates['default'])

            # Weight multipliers
            weight_multiplier = 1.0
            if weight >= 0.5 and weight < 1.0:
                weight_multiplier = 1.5
            elif weight >= 1.0 and weight < 2.0:
                weight_multiplier = 2.0
            elif weight >= 2.0 and weight < 5.0:
                weight_multiplier = 3.0
            elif weight >= 5.0:
                weight_multiplier = 4.0

            total_price = base_rate * weight * weight_multiplier
            return round(total_price, 2)
        except (ValueError, TypeError) as e:
            print(f"Error calculating diamond price: {str(e)}")
            return 0
    
    def get_gemstone_price(self, stone_type, quality, weight):
        """Calculate gemstone price based on type, quality and weight"""
        try:
            stone_type = stone_type.lower().strip()
            weight = float(weight or 0)
            
            if stone_type not in self.gemstone_rates:
                return self.gemstone_rates['default'] * weight
            
            stone_rates = self.gemstone_rates[stone_type]
            if isinstance(stone_rates, dict):
                base_rate = stone_rates.get(quality, stone_rates['default'])
            else:
                base_rate = stone_rates
                
            return base_rate * weight
        except (ValueError, TypeError) as e:
            print(f"Error calculating gemstone price: {str(e)}")
            return 0
    
    def calculate_stone_cost(self, is_diamond, weight, stone_type_or_quality, count=1):
        """Calculate stone cost
        Args:
            is_diamond (bool): Whether the stone is a diamond
            weight (float): Weight of the stone in carats
            stone_type_or_quality (str): For diamonds, this is the quality. For other stones, this is the stone type
            count (int): Number of stones
        """
        try:
            weight = float(weight or 0)
            count = int(count or 1)
            
            if is_diamond:
                # For diamonds, stone_type_or_quality is the quality
                price_per_piece = self.get_diamond_price(stone_type_or_quality, weight)
            else:
                # For other stones, stone_type_or_quality is the stone type
                stone_type = stone_type_or_quality
                quality = None  # Default quality
                price_per_piece = self.get_gemstone_price(stone_type, quality, weight)
            
            return price_per_piece * count
        except (ValueError, TypeError) as e:
            print(f"Error calculating stone cost: {str(e)}")
            return 0
    
    def calculate_metal_cost(self, weight, purity):
        """Calculate metal cost based on weight and purity"""
        try:
            weight = float(weight or 0)
            purity = float(purity or 24)
            gold_rate = self.get_gold_rate()
            return weight * gold_rate * (purity / 24)
        except (ValueError, TypeError):
            return 0
    
    def calculate_making_charges(self, metal_cost):
        """Calculate making charges"""
        try:
            metal_cost = float(metal_cost or 0)
            return metal_cost * (self.making_charges_percentage / 100)
        except (ValueError, TypeError):
            return 0
    
    def calculate_gst(self, amount):
        """Calculate GST"""
        try:
            amount = float(amount or 0)
            return amount * (self.gst_percentage / 100)
        except (ValueError, TypeError):
            return 0
    
    def calculate_total_price(self, metal_cost, stone_cost=0):
        """Calculate total price including all components"""
        try:
            metal_cost = float(metal_cost or 0)
            stone_cost = float(stone_cost or 0)
            
            making_charges = self.calculate_making_charges(metal_cost)
            subtotal = metal_cost + stone_cost + making_charges
            gst = self.calculate_gst(subtotal)
            total = subtotal + gst
            
            return {
                'metal_cost': round(metal_cost, 2),
                'stone_cost': round(stone_cost, 2),
                'making_charges': round(making_charges, 2),
                'subtotal': round(subtotal, 2),
                'gst': round(gst, 2),
                'total': round(total, 2)
            }
        except (ValueError, TypeError) as e:
            print(f"Error in calculate_total_price: {str(e)}")
            return {
                'metal_cost': 0,
                'stone_cost': 0,
                'making_charges': 0,
                'subtotal': 0,
                'gst': 0,
                'total': 0
            } 