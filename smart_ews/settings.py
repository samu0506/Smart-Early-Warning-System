"""
Django settings for smart_ews project.
Clean login redirect + stable authentication behavior
"""

from pathlib import Path

# -------------------------------
# BASE DIRECTORY
# -------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent


# -------------------------------
# SECURITY SETTINGS
# -------------------------------
SECRET_KEY = 'django-insecure-change-me'

DEBUG = True

ALLOWED_HOSTS = ['127.0.0.1', 'localhost']


# -------------------------------
# APPLICATIONS
# -------------------------------
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'students',
]


# -------------------------------
# MIDDLEWARE
# -------------------------------
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',

    # IMPORTANT → keeps login state correct
    'django.middleware.common.CommonMiddleware',

    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


# -------------------------------
# URL CONFIG
# -------------------------------
ROOT_URLCONF = 'smart_ews.urls'


# -------------------------------
# TEMPLATES
# -------------------------------
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]


# -------------------------------
# WSGI
# -------------------------------
WSGI_APPLICATION = 'smart_ews.wsgi.application'


# -------------------------------
# DATABASE
# -------------------------------
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# -------------------------------
# PASSWORD VALIDATION
# -------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# =====================================================
# 🔥 AUTHENTICATION REDIRECTS (MAIN FIX)
# =====================================================

# Where login_required sends users
LOGIN_URL = 'students:student_login'

# After login DO NOTHING automatic
# (we redirect manually in views.py)
LOGIN_REDIRECT_URL = 'students:student_login'

# After logout → back to login page
LOGOUT_REDIRECT_URL = 'students:student_login'

# Session expires when browser closes (prevents auto dashboard open)
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# Optional but recommended
SESSION_COOKIE_AGE = 3600  # 1 hour


# -------------------------------
# EMAIL CONFIGURATION (FOR PARENT ALERT)
# -------------------------------
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'yourcollege@gmail.com'
EMAIL_HOST_PASSWORD = 'your_app_password'
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER


# -------------------------------
# INTERNATIONALIZATION
# -------------------------------
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True


# -------------------------------
# STATIC FILES
# -------------------------------
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'


# MEDIA (profile images etc future use)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'


# -------------------------------
# DEFAULT PRIMARY KEY FIELD TYPE
# -------------------------------
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
