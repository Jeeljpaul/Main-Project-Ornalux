import requests
from django.conf import settings
from datetime import datetime
from django.core.cache import cache
import json

def get_current_metal_rate(metal_type):
    """Get real-time metal rates from GoldAPI"""
    # Convert metal type to API symbol
    metal_symbols = {
        'gold': 'XAU',
        'silver': 'XAG',
        'platinum': 'XPT',
        'palladium': 'XPD'
    }
    
    metal_type = metal_type.lower()
    if metal_type not in metal_symbols:
        return settings.PRICE_SETTINGS['DEFAULT_GOLD_RATE']  # Return default rate for unknown metals
    
    # Check cache first
    cache_key = f'metal_rate_{metal_type}'
    cached_rate = cache.get(cache_key)
    if cached_rate:
        return cached_rate

    try:
        # Make API request
        headers = {
            'x-access-token': settings.GOLD_API_KEY,
            'Content-Type': 'application/json'
        }
        symbol = metal_symbols[metal_type]
        url = f'https://www.goldapi.io/api/{symbol}/INR'
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            # Convert price from per ounce to per gram (1 troy oz = 31.1034768 grams)
            price_per_gram = float(data['price']) / 31.1034768
            
            # Cache the result for 1 hour
            cache.set(cache_key, price_per_gram, timeout=3600)
            
            # Log successful rate fetch
            print(f"Successfully fetched {metal_type} rate: {price_per_gram} INR/gram")
            return price_per_gram
        else:
            print(f"API request failed with status code: {response.status_code}")
            # If API call fails, return default rate from settings
            return settings.PRICE_SETTINGS['DEFAULT_GOLD_RATE']

    except Exception as e:
        print(f"Error fetching {metal_type} rate: {str(e)}")
        return settings.PRICE_SETTINGS['DEFAULT_GOLD_RATE']

def get_diamond_rate(quality):
    """Get diamond rate based on quality"""
    # Default rates based on quality
    default_rates = {
        'IF': 500000,   # Internally Flawless
        'VVS1': 450000,
        'VVS2': 400000,
        'VS1': 350000,
        'VS2': 300000,
        'SI1': 250000,
        'SI2': 200000
    }
    
    try:
        clarity = quality.split('-')[1]  # e.g., 'IJ-SI1' -> 'SI1'
        return default_rates.get(clarity, 200000)  # Default to 200000 if quality not found
        
    except Exception as e:
        print(f"Error getting diamond rate: {str(e)}")
        return 200000  # Default rate if something goes wrong

def get_gemstone_rate(stone_type, quality=None):
    """Get gemstone rate based on type and quality"""
    # Diamond rates
    diamond_rates = {
        'D-IF': 1000000,    # Flawless
        'E-VVS1': 800000,   # Very Very Slightly Included 1
        'F-VVS2': 700000,   # Very Very Slightly Included 2
        'G-VS1': 600000,    # Very Slightly Included 1
        'H-VS2': 500000,    # Very Slightly Included 2
        'I-SI1': 400000,    # Slightly Included 1
        'J-SI2': 300000     # Slightly Included 2
    }
    
    # Base rates per carat for different qualities
    base_rates = {
        'ruby': {
            'pigeon-blood': 50000,
            'vivid-red': 35000,
            'medium-red': 25000,
            'light-red': 15000
        },
        'sapphire': {
            'royal-blue': 45000,
            'cornflower-blue': 35000,
            'medium-blue': 25000,
            'light-blue': 15000
        },
        'emerald': {
            'muzo-green': 40000,
            'vivid-green': 30000,
            'medium-green': 20000,
            'light-green': 12000
        },
        'pearl': {
            'aaa': 15000,
            'aa': 10000,
            'a': 7000,
            'b': 4000
        }
    }

    try:
        stone_type = stone_type.lower().strip()
        
        # Handle diamonds separately
        if stone_type == 'diamond':
            return diamond_rates.get(quality, 300000)  # Default to lowest quality if not found
            
        if stone_type not in base_rates:
            return 5000  # Default rate for unknown stones

        if quality and quality in base_rates[stone_type]:
            return base_rates[stone_type][quality]
        
        # Return lowest rate if quality not specified or invalid
        return min(base_rates[stone_type].values())

    except Exception as e:
        print(f"Error getting gemstone rate: {str(e)}")
        return 5000  # Default fallback rate

def calculate_diamond_price(weight, quality, count=1):
    """Calculate diamond price based on weight, quality and count with weight multiplier"""
    try:
        base_rate = get_gemstone_rate('diamond', quality)
        
        # Weight multiplier for diamonds (price increases exponentially with size)
        weight_multiplier = 1.0
        if weight >= 0.5:
            weight_multiplier = 1.5
        elif weight >= 1.0:
            weight_multiplier = 2.0
        elif weight >= 2.0:
            weight_multiplier = 3.0
        elif weight >= 5.0:
            weight_multiplier = 4.0
            
        # Calculate total price with multiplier
        price_per_diamond = base_rate * weight * weight_multiplier
        total_price = price_per_diamond * count
        
        return total_price
        
    except Exception as e:
        print(f"Error calculating diamond price: {str(e)}")
        return 0

# Add PriceCalculator class to your existing utils.py
class PriceCalculator:
    def __init__(self):
        # Initialize with default rates from settings
        self.gold_rate = 5500  # Default gold rate per gram
        self.making_charges_percentage = 8
        self.gst_percentage = 3
        
        # Fixed rates for diamonds and stones
        self.diamond_rates = {
            'SI-IJ': 40000,
            'VS-GH': 50000,
            'VVS-EF': 60000,
            'default': 40000
        }
        
        self.gemstone_rates = {
            'ruby': 5000,
            'emerald': 4000,
            'sapphire': 3000,
            'pearl': 1000,
            'default': 1000
        }

    def get_gold_rate(self):
        """Get current gold rate"""
        return self.gold_rate
    
    def get_diamond_price(self, quality, weight):
        """Calculate diamond price based on quality and weight"""
        try:
            # Base prices per carat for different qualities
            base_prices = {
                'IJ-SI': 40000,
                'GH-VS': 60000,
                'GH-SI': 50000,
                'EF-VVS': 80000,
                'SI-IJ': 40000,
                'VS-GH': 50000,
                'VVS-EF': 60000
            }

            # Weight multipliers
            weight_multipliers = {
                (0, 0.3): 0.8,
                (0.3, 0.7): 1.0,
                (0.7, 1.5): 1.2,
                (1.5, 999): 1.5
            }

            # Quality multipliers
            quality_multipliers = {
                'IJ-SI': 1.0,
                'GH-VS': 1.2,
                'GH-SI': 1.1,
                'EF-VVS': 1.4,
                'SI-IJ': 1.0,
                'VS-GH': 1.2,
                'VVS-EF': 1.3
            }

            weight = float(weight or 0)
            base_price = base_prices.get(quality, base_prices['IJ-SI'])

            # Get weight multiplier
            weight_multiplier = 1.0
            for (min_weight, max_weight), multiplier in weight_multipliers.items():
                if min_weight <= weight < max_weight:
                    weight_multiplier = multiplier
                    break

            quality_multiplier = quality_multipliers.get(quality, 1.0)
            final_price = base_price * weight_multiplier * quality_multiplier
            
            # Market adjustment
            market_adjustment = 1.1 if datetime.now().year >= 2024 else 1.0
            total_price = final_price * weight * market_adjustment

            return round(total_price, 2)
        except (ValueError, TypeError) as e:
            print(f"Error calculating diamond price: {str(e)}")
            return 0
    
    def calculate_stone_cost(self, is_diamond, weight, quality=None, count=1):
        """Calculate stone cost"""
        try:
            weight = float(weight or 0)
            count = int(count or 1)
            
            if is_diamond:
                price_per_piece = self.get_diamond_price(quality, weight)
                return price_per_piece * count
            else:
                rate = self.get_gemstone_rate(quality)
                return weight * rate * count
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