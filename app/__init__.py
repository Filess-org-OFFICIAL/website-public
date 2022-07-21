# Load configuration
import config

# Load flask imports
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate

# import dependencies
import click
from flask.cli import with_appcontext
import stripe


# run $ flask create_tables to recreate all tables in postgres database
@click.command(name='create_tables')
@with_appcontext
def create_tables():
    db.create_all()


# Setup main flask application
app = Flask(__name__)
app.config.from_object(config.ProdConfig)

# Strip API keys for payment
stripe_keys = {
    "secret_key": "",
    "publishable_key": "",
    "endpoint_secret": "",
}

stripe.api_key = stripe_keys["secret_key"]

# Setup SQL alchemy
db = SQLAlchemy(app)

# migration info: https://flask-migrate.readthedocs.io/en/latest/
migrate = Migrate(app, db)  # use $flask db migrate then $flask db upgrade for updating any tables
# try $heroku pg:killall DATABASE_URL if hanging

# Set up cli command
app.cli.add_command(create_tables)

# Login manager setup
login = LoginManager(app)
login.login_view = 'login'

# Load routes
from app import routes


# Route error handlers to their pages
app.register_error_handler(404, routes.page_not_found)
