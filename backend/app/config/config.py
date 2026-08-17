# app/config/config.py

import os
from dotenv import load_dotenv
from datetime import timedelta

load_dotenv()


class Config:
    """Base configuration."""
    SECRET_KEY = os.getenv(
        'FLASK_SECRET_KEY', '54f62f33325c40a77adb0ce2a304d7e7a6de')

    # SQLALCHEMY
    SQLALCHEMY_TRACK_MODIFICATIONS = os.getenv(
        'SQLALCHEMY_TRACK_MODIFICATIONS', 'False') == 'True'

    # Grab the DB URL from the environment (Render default or fallback)
    # Render natively populates "DATABASE_URL"
    if os.getenv('FLASK_ENV') == "production":
        database_url = os.getenv('DATABASE_URL')
    else:
        database_url = os.getenv('SQLALCHEMY_DATABASE_URI')

    # Crucial Fix: Convert 'postgres://' to 'postgresql://' for production compatibility
    if database_url and database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)

    SQLALCHEMY_DATABASE_URI = database_url

    # Redis Integration Config
    if os.getenv('FLASK_ENV') == "production":
        redis_url = os.getenv('REDIS_URL')
    else:
        redis_url = os.getenv('LOCAL_REDIS_URL')

    REDIS_URL = redis_url

    # Ratelimt Storage Config
    RATELIMIT_STORAGE_URI = REDIS_URL

    # JWT needs a secret key
    JWT_SECRET_KEY = os.getenv(
        'JWT_SECRET_KEY', '54f62f33325c40a77adb0ce2a304d7e7a6de')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(seconds=int(
        os.getenv('JWT_ACCESS_TOKEN_EXPIRES', 900)))
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(seconds=int(
        os.getenv('JWT_REFRESH_TOKEN_EXPIRES', 2592000)))

    CLOUD_NAME = os.getenv("CLOUD_NAME")
    CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY")
    CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET")


class DevelopmentConfig(Config):
    """Development configurations."""
    DEBUG = True


class ProductionConfig(Config):
    """Production configurations."""
    DEBUG = False

    # ADD THESE ENGINE OPTIONS TO FIX THE SSL TIMEOUT
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_size": 10,          # Maximum steady connections
        "max_overflow": 5,        # Temporary extra connections allowed
        "pool_recycle": 280,      # Automatically refresh connections every 4.5 minutes
        # CRITICAL: Validates the connection before running any SQL queries
        "pool_pre_ping": True,
    }
