import os
import google.generativeai as genai
from django.conf import settings

# Configure the Gemini API with proper error handling
def initialize_gemini():
    try:
        api_key = settings.GEMINI_API_KEY
        if not api_key:
            print("No Gemini API key found in settings, using fallback data")
            return None
            
        genai.configure(api_key=api_key)
        
        try:
            # Verify the API key works by listing models
            models = genai.list_models()
            for model in models:
                if 'gemini-pro' in model.name:
                    return model.name
            print("Gemini Pro model not found in available models, using fallback data")
            return None
        except Exception as e:
            print(f"Error verifying Gemini API key: {str(e)}")
            return None
            
    except Exception as e:
        print(f"Error initializing Gemini API: {str(e)}")
        return None

# Get the available Gemini model name
GEMINI_MODEL = initialize_gemini()

# Fallback data for when API is not available
FALLBACK_METAL_DATA = {
    'gold': [
        {'purity': '24K', 'percentage': 99.9, 'rate': 5500},
        {'purity': '22K', 'percentage': 91.6, 'rate': 5060},
        {'purity': '18K', 'percentage': 75.0, 'rate': 4125},
        {'purity': '14K', 'percentage': 58.3, 'rate': 3206}
    ],
    'silver': [
        {'purity': '999', 'percentage': 99.9, 'rate': 75},
        {'purity': '925', 'percentage': 92.5, 'rate': 69}
    ],
    'platinum': [
        {'purity': '950', 'percentage': 95.0, 'rate': 3200},
        {'purity': '900', 'percentage': 90.0, 'rate': 3000}
    ]
}

FALLBACK_STONE_DATA = {
    'diamond': [
        {'grade': 'D-IF', 'clarity': 'Internally Flawless', 'multiplier': 2.0},
        {'grade': 'E-VVS1', 'clarity': 'Very Very Slightly Included 1', 'multiplier': 1.8},
        {'grade': 'F-VVS2', 'clarity': 'Very Very Slightly Included 2', 'multiplier': 1.6},
        {'grade': 'G-VS1', 'clarity': 'Very Slightly Included 1', 'multiplier': 1.4},
        {'grade': 'H-VS2', 'clarity': 'Very Slightly Included 2', 'multiplier': 1.2},
        {'grade': 'I-SI1', 'clarity': 'Slightly Included 1', 'multiplier': 1.0},
        {'grade': 'J-SI2', 'clarity': 'Slightly Included 2', 'multiplier': 0.8}
    ],
    'ruby': [
        {'grade': 'AAA', 'clarity': 'Pigeon Blood Red', 'multiplier': 2.0},
        {'grade': 'AA', 'clarity': 'Vivid Red', 'multiplier': 1.5},
        {'grade': 'A', 'clarity': 'Medium Red', 'multiplier': 1.0}
    ],
    'sapphire': [
        {'grade': 'AAA', 'clarity': 'Royal Blue', 'multiplier': 2.0},
        {'grade': 'AA', 'clarity': 'Medium Blue', 'multiplier': 1.5},
        {'grade': 'A', 'clarity': 'Light Blue', 'multiplier': 1.0}
    ],
    'emerald': [
        {'grade': 'AAA', 'clarity': 'Vivid Green', 'multiplier': 2.0},
        {'grade': 'AA', 'clarity': 'Medium Green', 'multiplier': 1.5},
        {'grade': 'A', 'clarity': 'Light Green', 'multiplier': 1.0}
    ]
}

def get_metal_purities():
    """
    Fetch information about metal purities and their current market rates
    """
    if not GEMINI_MODEL:
        print("Gemini API not available, using fallback data")
        return FALLBACK_METAL_DATA

    try:
        prompt = """
        Please provide detailed information about gold, silver, and platinum purities in jewelry:
        1. List all standard purities
        2. Their percentage values
        3. Current market rates
        Format the response as structured data that can be parsed.
        """
        
        model = genai.GenerativeModel(GEMINI_MODEL)
        response = model.generate_content(prompt)
        
        # Process and structure the response
        return parse_metal_response(response.text)
    except Exception as e:
        print(f"Error getting metal purities from Gemini: {str(e)}")
        return FALLBACK_METAL_DATA

def get_stone_purities():
    """
    Fetch information about stone purities/grades and their pricing factors
    """
    if not GEMINI_MODEL:
        print("Gemini API not available, using fallback data")
        return FALLBACK_STONE_DATA

    try:
        prompt = """
        Please provide detailed information about diamond, ruby, sapphire, and emerald qualities:
        1. List all standard quality grades
        2. Their clarity ratings
        3. Price multipliers based on quality
        Format the response as structured data that can be parsed.
        """
        
        model = genai.GenerativeModel(GEMINI_MODEL)
        response = model.generate_content(prompt)
        
        # Process and structure the response
        return parse_stone_response(response.text)
    except Exception as e:
        print(f"Error getting stone purities from Gemini: {str(e)}")
        return FALLBACK_STONE_DATA

def parse_metal_response(response_text):
    """
    Parse the Gemini response for metals into structured data
    """
    # For now, return fallback data as parsing logic needs to be implemented
    return FALLBACK_METAL_DATA

def parse_stone_response(response_text):
    """
    Parse the Gemini response for stones into structured data
    """
    # For now, return fallback data as parsing logic needs to be implemented
    return FALLBACK_STONE_DATA

def update_metal_prices():
    """
    Update metal prices in the database using Gemini API
    """
    if not GEMINI_MODEL:
        print("Gemini API not available, using fallback data")
        return False

    try:
        prompt = """
        Please provide current market rates for:
        1. 24K Gold (per gram)
        2. Pure Silver (per gram)
        3. Pure Platinum (per gram)
        Format as simple numerical values.
        """
        
        model = genai.GenerativeModel(GEMINI_MODEL)
        response = model.generate_content(prompt)
        
        # Process the response and update prices in the database
        prices = parse_price_response(response.text)
        update_database_prices(prices)
        return True
    except Exception as e:
        print(f"Error updating prices: {str(e)}")
        return False

def parse_price_response(response_text):
    """
    Parse the price response from Gemini
    """
    # Implement parsing logic based on response format
    return {
        'gold': 0.0,
        'silver': 0.0,
        'platinum': 0.0
    }

def update_database_prices(prices):
    """
    Update prices in the database
    """
    # Implement database update logic here
    pass 