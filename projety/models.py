"""Manage the models in our app."""

from flask import abort, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import (TimedJSONWebSignatureSerializer
                          as Serializer, BadSignature, SignatureExpired)

from . import db
from .utils import timestamp, url_for


class User(db.Model):
    """The User model."""

    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.Integer, default=timestamp)
    updated_at = db.Column(db.Integer, default=timestamp, onupdate=timestamp)
    last_seen_at = db.Column(db.Integer, default=timestamp)
    nickname = db.Column(db.String(32), nullable=False, unique=True)
    password_hash = db.Column(db.String(256), nullable=False)
    token = db.Column(db.String(64), nullable=True, unique=True)

    @property
    def password(self):
        """We don't want getter on password."""
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)
        self.token = None  # if user is changing passwords, also revoke token

    def verify_password(self, password):
        """For basic_auth check."""
        return check_password_hash(self.password_hash, password)

    def generate_auth_token(self, expiration=600):
        """Generate a token on the fly."""
        s = Serializer(current_app.config['SECRET_KEY'], expires_in=expiration)
        self.token = s.dumps({'id': self.id})
        return self.token

    @staticmethod
    def verify_auth_token(token):
        """
        Check is the token given is valid.

        In case where the token raise SignatureExpired, null the token
        property for the user.
        """
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except SignatureExpired as e:
            # If we have a token for the user, null it
            user = User.query.get(e.payload['id'])
            if user.token:
                user.token = None
            return None  # valid token, but expired
        except BadSignature:
            return None  # invalid token
        user = User.query.get(data['id'])
        return user

    @staticmethod
    def create(data):
        """Create a new user."""
        user = User()
        user.from_dict(data, partial_update=False)
        return user

    def from_dict(self, data, partial_update=True):
        """Import user data from a dictionary."""
        for field in ['nickname', 'password']:
            try:
                setattr(self, field, data[field])
            except KeyError:
                if not partial_update:
                    abort(400)

    def to_dict(self):
        """Export user to a dictionary."""
        return {
            'id': self.id,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'nickname': self.nickname,
            'last_seen_at': self.last_seen_at,
            '_links': {
                'self': url_for('api.get_user', id=self.id),
                'tokens': url_for('api.new_token')
            }
        }
