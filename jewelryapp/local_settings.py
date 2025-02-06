# Google API Configuration
from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()



GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')
