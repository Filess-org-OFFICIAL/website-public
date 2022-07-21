# All app imports
from app import db
from app import login

# Other imports
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.dialects.mysql import BIGINT

# Import UserMixin for flask login
from flask_login import UserMixin

# migration info: https://flask-migrate.readthedocs.io/en/latest/


class User(UserMixin, db.Model):  # users for authentication
    __tablename__ = 'users'
    userId = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(320), index=True)
    passwordHash = db.Column(db.String(128))
    firstName = db.Column(db.String(255))
    lastName = db.Column(db.String(255), index=True)
    subdomain = db.Column(db.String(255), index=True, default=None)
    dateCreated = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    dateUpdated = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    totalSize = db.Column(db.Integer, index=True, default=0)

    def __repr__(self):
        return f'<User ID {self.userId} ({self.lastName}, {self.firstName})>'
    
    # Override UserMixin because we have 'userId' not 'id'
    def get_id(self):
        return self.userId

    def set_password(self, password):
        self.passwordHash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.passwordHash, password)

# User-loader function for Flask-Login
@login.user_loader
def load_user(id):
    return User.query.get(int(id))


class Files(db.Model):  # uploaded user assets
    __tablename__ = 'files'
    fileId = db.Column(db.Integer, primary_key=True)
    userId = db.Column(db.Integer, index=True)
    fileName = db.Column(db.String(320), index=True)
    fileBytes = db.Column(db.Integer, index=True)
    fileType = db.Column(db.String(320), index=True)
    fileWidth = db.Column(db.Integer, index=True)
    fileHeight = db.Column(db.Integer, index=True)
    dateCreated = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    dateUpdated = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    tag = db.Column(db.String(255), index=True)


class Plan(db.Model):
    __tablename__ = 'plan'
    ID = db.Column(db.Integer, primary_key=True)
    planId = db.Column(db.Integer, index=True)
    userId = db.Column(db.Integer, index=True)
    storageSize = db.Column(BIGINT, index=True)
    tags = db.Column(db.Integer, index=True)
    subdomains = db.Column(db.Integer, index=True)
    dateCreated = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    dateExpired = db.Column(db.DateTime, index=True)
    spent = db.Column(db.String(320), index=True)
