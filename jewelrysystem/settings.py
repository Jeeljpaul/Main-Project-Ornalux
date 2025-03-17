from pathlib import Path
import os
from dotenv import load_dotenv
import mimetypes

load_dotenv()


GOOGLE_OAUTH_CLIENT_ID = os.environ.get('CLIENT_ID')
CLIENT_SECRET = os.environ.get('CLIENT_SECRET')

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-7ac1#6p@u*6eibbh(cafy0@@fdr-w8buz73_h$^hqp$rde)529'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True


ALLOWED_HOSTS = ['*']

CSRF_TRUSTED_ORIGINS = ['https://miniproject-ornalux.onrender.com']

CSRF_TRUSTED_ORIGINS = ['https://d8fc-117-193-79-225.ngrok-free.app']

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'jewelryapp',
    'social_django',
]

AUTHENTICATION_BACKENDS = (
    'social_core.backends.google.GoogleOAuth2',
    'django.contrib.auth.backends.ModelBackend',
)

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'social_django.middleware.SocialAuthExceptionMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware'
]

# Add WebAssembly MIME type
MIDDLEWARE.append('django.middleware.common.CommonMiddleware')

# Add MIME type configuration
mimetypes.add_type('application/wasm', '.wasm')

SOCIAL_AUTH_PIPELINE = (
    'social_core.pipeline.social_auth.social_details',  
    'social_core.pipeline.social_auth.social_uid',      
    'social_core.pipeline.social_auth.auth_allowed',    
    'social_core.pipeline.social_auth.social_user',     
    'social_core.pipeline.user.get_username',          
    'social_core.pipeline.user.create_user',                             
    'social_core.pipeline.social_auth.associate_user',  
    'social_core.pipeline.social_auth.load_extra_data', 
    'social_core.pipeline.user.user_details',          
)

LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = GOOGLE_OAUTH_CLIENT_ID  
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = CLIENT_SECRET

ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = False
SOCIALACCOUNT_QUERY_EMAIL = True
SOCIALACCOUNT_EMAIL_VERIFICATION = "none"

ROOT_URLCONF = 'jewelrysystem.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': ['templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'jewelrysystem.wsgi.application'

# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'db_ornalux',
        'USER': 'root',
        'PASSWORD': '',
        'HOST': 'localhost',
        'PORT': '3306',
    }
}


# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.mysql',
#         'NAME': 'ornalux123_facinggold',
#         'USER': 'ornalux123_facinggold',
#         'PASSWORD': 'fc549d0d4a1b800378dee77be3a7c1056d2b4d7e', 
#         'HOST': 'em-ju.h.filess.io',
#         'PORT': '3307',
#         'OPTIONS': {
#             'init_command': "SET sql_mode='STRICT_TRANS_TABLES'"
#         }
#     }
# }


# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True



LOGIN_URL = '/login/'

SESSION_ENGINE = 'django.contrib.sessions.backends.db'  # This should be enabled by default
SESSION_COOKIE_AGE = 1209600  # Two weeks in seconds (default)
SESSION_EXPIRE_AT_BROWSER_CLOSE = False  # Set to True if you want to expire when the browser closes
SESSION_SAVE_EVERY_REQUEST = True  # Ensures that the session is saved on every request




# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = '/static/'

# Ensure that STATIC_ROOT is correctly set for collecting static files in production
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# This should point to the directory where your static files are located
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

# Media files (Uploaded by users)
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# email configuration for forgot password

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = os.environ.get('EMAIL_HOST_USER')  # Email sender's address

# Razorpay credentials
RAZORPAY_KEY_ID = os.environ.get('RAZORPAY_KEY_ID')
RAZORPAY_KEY_SECRET = os.environ.get('RAZORPAY_KEY_SECRET')

# Google Cloud Vision Settings
GOOGLE_CLOUD_CREDENTIALS = os.path.join(BASE_DIR, 'credentials', 'google-cloud-credentials.json')
if os.path.exists(GOOGLE_CLOUD_CREDENTIALS):
    os.environ['GOOGLE_CLOUD_CREDENTIALS'] = GOOGLE_CLOUD_CREDENTIALS

# Separate Google API keys for different services
GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY', '')  # For Maps and other Google services
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')  # Specifically for Gemini AI

if not GEMINI_API_KEY:
    print("Warning: GEMINI_API_KEY not found in environment variables! Gemini AI features will use fallback data.")

CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_METHODS = [
    'GET',
    'POST',
    'PUT',
    'PATCH',
    'DELETE',
    'OPTIONS'
]

# Add MIME type for GLTF files
mimetypes.add_type('model/gltf+json', '.gltf')
mimetypes.add_type('model/gltf-binary', '.glb')

GOLD_API_KEY = os.environ.get('GOLD_API_KEY')  # You're using this key in views.py


# Add fallback configurations
PRICE_SETTINGS = {
    'GOLD_RATE_CACHE_TIMEOUT': 3600,  # 1 hour
    'DEFAULT_GOLD_RATE': 5500,  # Default gold rate per gram
    'MAKING_CHARGES_PERCENTAGE': 8,
    'GST_PERCENTAGE': 3,
    'DIAMOND_BASE_PRICES': {
        'IJ-SI': 40000,
        'GH-VS': 60000,
        'GH-SI': 50000,
        'EF-VVS': 80000
    },
    'MARKET_ADJUSTMENT': 1.0  # Can be updated based on market conditions
}

PERFECT_CORP_API_KEY = os.environ.get('PERFECT_CORP_API_KEY')  # Replace with actual API key