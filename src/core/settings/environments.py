from os import getenv, path
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent

load_dotenv(path.join(BASE_DIR, ".env"))
SECRET_KEY = getenv("SECRET_KEY")

channel = getenv("CHANNEL")
DEBUG = getenv("DEBUG", "False") == "True"
PREFIX_KEY = getenv('PREFIX_KEY')

DB_USERNAME = getenv("DB_USER")
DB_NAME = getenv("DB_NAME")
DB_PASSWORD = getenv("DB_PASSWORD")

EMAIL_HOST = getenv("EMAIL_HOST")
EMAIL_HOST_USER = getenv("EMAIL_USER")
EMAIL_HOST_PASSWORD = getenv("EMAIL_PASSWORD")
EMAIL_PORT = getenv("EMAIL_PORT")

STRIPE_SECRET_KEY = getenv('STRIPE_SECRET_KEY')
STRIPE_PUBLISHABLE_KEY = getenv('STRIPE_PUBLISHABLE_KEY')
ENDPOINT_SECRET = getenv('ENDPOINT_SECRET')

FONEPAY_KEY = getenv('FONEPAY_KEY')
FONEPAY_USERNAME = getenv('FONEPAY_USERNAME')
FONEPAY_PASSWORD = getenv('FONEPAY_PASSWORD')
FONEPAY_MERCHANT_CODE = getenv('FONEPAY_MERCHANT_CODE')

EMAIL_HOST = getenv('EMAIL_HOST')
EMAIL_PORT = getenv('EMAIL_PORT')
EMAIL_HOST_USER = getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = getenv('EMAIL_HOST_PASSWORD')
DEPLOY_URL = getenv('DEPLOY_URL')

DOCKER = getenv('DOCKER')

EMAIL_USE_TLS = True
EMAIL_USE_SSL = False
