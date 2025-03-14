from django.http import JsonResponse
from jewelryapp.utils.price_calculator import PriceCalculator

def get_stone_rate(request):
    try:
        stone_type = request.GET.get('stone_type', '').strip().lower()
        quality = request.GET.get('quality', '')
        weight = float(request.GET.get('weight', 0))
        count = int(request.GET.get('count', 1))

        calculator = PriceCalculator()
        
        if stone_type == 'diamond':
            # For diamonds, use get_diamond_price
            base_rate = calculator.get_diamond_price(quality, 1.0)  # Get rate for 1 carat
            total_price = calculator.calculate_stone_cost(True, weight, quality, count)
            return JsonResponse({
                'success': True,
                'rate': base_rate,
                'total_price': total_price,
                'weight_multiplier_applied': weight >= 0.5
            })
        else:
            # For other stones, use get_gemstone_price
            base_rate = calculator.get_gemstone_price(stone_type, quality, 1.0)  # Get rate for 1 carat
            total_price = calculator.calculate_stone_cost(False, weight, stone_type, count)
            return JsonResponse({
                'success': True,
                'rate': base_rate,
                'total_price': total_price,
                'weight_multiplier_applied': False
            })
    except Exception as e:
        print(f"Error in get_stone_rate: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })