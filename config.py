# TODO: Add a BaseConfig class for DB and other services.
# Also add a production configuration for releases.
import os


class TestConfig:
    # Basic configuration options
    FLASK_ENV = 'development'
    TEMPLATES_AUTO_RELOAD = True
    TESTING = True
    DEBUG = True

    # SQL Alchemy configuration options
    # SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(os.getcwd(), 'filess.db')
    SQLALCHEMY_DATABASE_URI = ''
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # REMEMBER TO CHANGE BACK TO "filess.org" FOR PROD!!! Use filess.org:5000 for local testing of subdomains
    # SERVER_NAME = 'filess.org'

    # Flask configuration
    SECRET_KEY = ''


class ProdConfig:
    # Basic configuration options
    FLASK_ENV = 'production'
    TESTING = False
    DEBUG = False

    # SQL Alchemy configuration options
    SQLALCHEMY_DATABASE_URI = ''
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SERVER_NAME = 'filess.org'

    # Flask configuration
    SECRET_KEY = ''
