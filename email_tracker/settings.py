"""
Django settings for email_tracker project.

Generated by 'django-admin startproject' using Django 4.0.6.

For more information on this file, see
https://docs.djangoproject.com/en/4.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.0/ref/settings/
"""
import os
from pathlib import Path
import environ
import dj_database_url

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env()
# Read the .env file
env_file = os.path.join(BASE_DIR, '.env')
if os.path.exists(env_file):
    environ.Env.read_env(env_file)
# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('SECRET_KEY')


# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env('DEBUG').lower() == "true"

# ALLOWED_HOSTS = []

ALLOWED_HOSTS = env('ALLOWED_HOSTS').split(",")

RENDER_EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME') 
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

# ALLOWED_HOSTS = ['127.0.0.1', 'localhost', 'b28d-2405-201-5009-6022-8fef-7e89-a12e-b610.ngrok-free.app']

# CSRF_TRUSTED_ORIGINS = ['https://b28d-2405-201-5009-6022-8fef-7e89-a12e-b610.ngrok-free.app']



# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'tracking',
    'sending',
    'frontend',
    'unsubscribers',
    'receiving',
    'emails',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'email_tracker.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'email_tracker.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.0/ref/settings/#databases

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
#     }
# }

# Replace the SQLite DATABASES configuration with PostgreSQL:
# DATABASE_USER = env('POSTGRESQL_USER')
# DATABASE_PASS = env('POSTGRESQL_PASS')
# DATABASE_NAME = env('POSTGRESQL_DB_NAME')
    
DATABASES = {
    'default': dj_database_url.config(
        default= env('DATABASE_URL'),
        #f'postgresql://{DATABASE_USER}:{DATABASE_PASS}@localhost:5432/{DATABASE_NAME}',
        #f'postgresql://email_tracker_user:password@localhost:5432/email_tracker_db',
        conn_max_age=600)
    }


# Password validation
# https://docs.djangoproject.com/en/4.0/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/4.0/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "Asia/Kolkata"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.0/howto/static-files/

# STATIC_URL = 'static/'
STATIC_URL = '/static/'

# This production code might break development mode, so we check whether we're in DEBUG mode
# if not DEBUG:    # Tell Django to copy static assets into a path called `staticfiles` (this is specific to Render)
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
    # Enable the WhiteNoise storage backend, which compresses static files to reduce disk use
    # and renames the files with unique names for each version to support long-term caching
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# # The absolute path to the directory where collectstatic will collect static files for deployment.
# STATIC_ROOT = os.path.join(BASE_DIR, 'collected_static')

# # Additional locations the staticfiles app will traverse to collect static files.
# STATICFILES_DIRS = [
#     os.path.join(BASE_DIR, 'static'),
# ]

# Default primary key field type
# https://docs.djangoproject.com/en/4.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# default static files settings for PythonAnywhere.
# see https://help.pythonanywhere.com/pages/DjangoStaticFiles for more info
# MEDIA_ROOT = '/home/1chandailrc1/email_tracker/media'
# MEDIA_URL = '/media/'
# STATIC_ROOT = '/home/1chandailrc1/email_tracker/static'

#!!!!!!!!! IMPORTANT !!!!!!!!! CHECK .env file in the project root directory for env variables.
# EXAMPLE: "GMAIL_EMAIL_USER"

USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

mail_case = env('MAIL_SERVICE')

if mail_case:
    print(f'MAILING SERVICE SELECTED: {mail_case}')

if mail_case == 'GMAIL':
    
    #Email settings
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = 'smtp.gmail.com'
    EMAIL_PORT = 587
    EMAIL_USE_TLS = True
    EMAIL_HOST_USER = env('GMAIL_EMAIL_USER') # Use your personal gmail here
    EMAIL_HOST_PASSWORD = env('GMAIL_EMAIL_PASS')  # Use your gmail app pass key. Different from your account password
    DEFAULT_FROM_EMAIL = env('GMAIL_DEFAULT_EMAIL')  # Replace with your default email address
    
if mail_case == 'IONOS':
    
    #Email SMTP settings
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = 'smtp.ionos.com'
    EMAIL_PORT = 587
    EMAIL_USE_TLS = True
    EMAIL_USE_SSL = False
    EMAIL_HOST_USER = env('IONOS_EMAIL_USER') # Use your personal gmail here
    EMAIL_HOST_PASSWORD = env('IONOS_EMAIL_PASS')  # Use your gmail app pass key. Different from your account password
    DEFAULT_FROM_EMAIL = env('IONOS_DEFAULT_EMAIL')  # Replace with your default email address
    
    # IMAP settings
    EMAIL_IMAP_SERVER = 'imap.ionos.com'
    EMAIL_IMAP_PORT = 993
    EMAIL_IMAP_USE_SSL = True
    EMAIL_HOST_USER = env('IONOS_EMAIL_USER')
    EMAIL_HOST_PASSWORD = env('IONOS_EMAIL_PASS')
    
elif mail_case == 'MAILGUN':
    
    # MAILGUN
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = 'smtp.mailgun.org'
    EMAIL_PORT = 587
    EMAIL_USE_TLS = True
    EMAIL_HOST_USER = env('MAILGUN_SMTP_USER')  # Replace YOUR_DOMAIN with your Mailgun domain
    EMAIL_HOST_PASSWORD = env('MAILGUN_SMTP_PASS')  # Replace with your Mailgun SMTP password
    DEFAULT_FROM_EMAIL = env('MAILGUN_DEFAULT_EMAIL')  # Replace with your default email address

    # FOR API ONLY    
    MAILGUN_API_KEY = env('MAILGUN_API_KEY')
    MAILGUN_DOMAIN = env('MAILGUN_DOMAIN')
    
elif mail_case == 'SENDGRID':

    # SENDGRID
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = 'smtp.sendgrid.net'
    EMAIL_PORT = 587
    EMAIL_USE_TLS = True
    EMAIL_HOST_USER = env('SENDGRID_API_USER')  # This is the string 'apikey', not your username
    EMAIL_HOST_PASSWORD = env('SENDGRID_API_PASS')  # Replace with your SendGrid API key
    DEFAULT_FROM_EMAIL = env('SENDGRID_DEFAULT_EMAIL')  # Replace with your default email address
    
elif mail_case == 'MAILHOG':
    
    # MAILHOG
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = 'localhost'
    EMAIL_PORT = 1025
    EMAIL_HOST_USER = ''
    EMAIL_HOST_PASSWORD = ''
    EMAIL_USE_TLS = False
    EMAIL_USE_SSL = False
    DEFAULT_FROM_EMAIL='tester@mailhog.com'

# Site URL for tracking pixel
BASE_URL = env('BASE_URL')#'http://127.0.0.1:8000'
# BASE_URL = 'http://1chandailrc1.pythonanywhere.com'
# BASE_URL = 'https://b28d-2405-201-5009-6022-8fef-7e89-a12e-b610.ngrok-free.app'

# Mautic settings
# MAUTIC_BASE_URL = 'https://example.com'
# MAUTIC_PUBLIC_KEY = 'your_public_key'
# MAUTIC_SECRET_KEY = 'your_secret_key'
# MAUTIC_USERNAME = 'your_mautic_username'
# MAUTIC_PASSWORD = 'your_mautic_password'

# email_tracker/settings.py

# CELERY_BROKER_URL = 'redis://localhost:6379/0'
# CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
# CELERY_ACCEPT_CONTENT = ['json']
# CELERY_TASK_SERIALIZER = 'json'
# CELERY_RESULT_SERIALIZER = 'json'
# CELERY_TIMEZONE = 'Asia/Kolkata'

# settings.py

CELERY_BROKER_URL = 'sqla+sqlite:///celery.sqlite3'
CELERY_RESULT_BACKEND = 'db+sqlite:///celery.sqlite3'

CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Asia/Kolkata'


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
        'simple': {
            'format': '%(levelname)s %(message)s',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'debug.log'),
            'formatter': 'verbose',  # Use the verbose formatter
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',  # Use the verbose formatter
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'tracking': {  # Replace with your actual app name
            'handlers': ['file', 'console'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}




