import os

# Gemini API Settings
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY', '')  # Get API key from environment variable

# Price Settings
PRICE_SETTINGS = {
    'DEFAULT_GOLD_RATE': 5500,  # Default rate per gram for 24K gold
    'DEFAULT_SILVER_RATE': 75,  # Default rate per gram for pure silver
    'DEFAULT_PLATINUM_RATE': 3200,  # Default rate per gram for pure platinum
} 