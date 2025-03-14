# This empty file makes the directory a Python package 

from .price_calculator import PriceCalculator

# Initialize a calculator instance for utility functions
_calculator = PriceCalculator()

def get_current_metal_rate():
    return _calculator.get_gold_rate()

def get_diamond_rate(quality='GH-VS', weight=1.0):
    return _calculator.get_diamond_price(quality, weight)

def get_gemstone_rate(stone_type, quality=None):
    """Get gemstone rate based on type and quality"""
    return _calculator.get_gemstone_price(stone_type, quality, 1.0)  # Get rate for 1 carat

def calculate_diamond_price(weight, quality, count=1):
    """
    Calculate the total price for diamonds based on weight, quality, and count.
    
    Args:
        weight (float): Weight of each diamond in carats
        quality (str): Quality grade of the diamond (e.g., 'D-IF', 'E-VVS1', etc.)
        count (int): Number of diamonds (default: 1)
    
    Returns:
        tuple: (total_price, rate_per_carat, weight_multiplier_applied)
    """
    # Base rates per carat for different quality grades (in INR)
    base_rates = {
        'D-IF': 1000000,    # Flawless
        'E-VVS1': 850000,   # Very Very Slightly Included 1
        'F-VVS2': 750000,   # Very Very Slightly Included 2
        'G-VS1': 650000,    # Very Slightly Included 1
        'H-VS2': 550000,    # Very Slightly Included 2
        'I-SI1': 450000,    # Slightly Included 1
        'J-SI2': 350000     # Slightly Included 2
    }
    
    # Get base rate for the quality grade
    base_rate = base_rates.get(quality, 350000)  # Default to lowest grade if not found
    
    # Weight multiplier for larger stones (premium for larger diamonds)
    weight_multiplier = 1.0
    weight_multiplier_applied = False
    
    if weight >= 1.0:
        weight_multiplier = 1.5
        weight_multiplier_applied = True
    elif weight >= 0.5:
        weight_multiplier = 1.25
        weight_multiplier_applied = True
    
    # Calculate final rate per carat
    rate_per_carat = base_rate * weight_multiplier
    
    # Calculate total price
    total_price = rate_per_carat * weight * count
    
    return total_price, rate_per_carat, weight_multiplier_applied 

__all__ = ['PriceCalculator', 'get_current_metal_rate', 'get_diamond_rate', 'get_gemstone_rate'] 