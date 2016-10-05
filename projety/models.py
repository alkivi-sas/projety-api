"""Manage the models in our app."""

import time

from flask import abort, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import (TimedJSONWebSignatureSerializer
                          as Serializer, BadSignature, SignatureExpired)

from . import db
from .utils import timestamp, url_for


class Acl(db.Model):
    """The Acl model."""

    __tablename__ = 'acls'
    __table_args__ = (db.UniqueConstraint('minions', 'functions', 'user_id'),)

    id = db.Column(db.Integer, primary_key=True)
    minions = db.Column(db.String(256), nullable=False)
    functions = db.Column(db.String(256), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    def to_dict(self):
        """Export user to a dictionary."""
        return {
            'id': self.id,
            'minions': self.minions,
            'functions': self.functions,
            'user_id': self.user_id,
            '_links': {
                'self': url_for('api.get_acl',
                                user_id=self.user_id,
                                acl_id=self.id),
                'user': url_for('api.get_user', id=self.user_id),
            }
        }


class Role(db.Model):
    """The Role model."""

    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    def to_dict(self):
        """Export user to a dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'user_id': self.user_id,
            '_links': {
                'self': url_for('api.get_role',
                                user_id=self.user_id,
                                role_id=self.id),
                'user': url_for('api.get_user', id=self.user_id),
            }
        }


class User(db.Model):
    """The User model."""

    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.Integer, default=timestamp)
    updated_at = db.Column(db.Integer, default=timestamp, onupdate=timestamp)
    last_seen_at = db.Column(db.Integer, default=timestamp)
    nickname = db.Column(db.String(32), nullable=False, unique=True)
    password_hash = db.Column(db.String(256), nullable=False)
    acls = db.relationship('Acl', backref='users')
    roles = db.relationship('Role', backref='users')

    @property
    def password(self):
        """We don't want getter on password."""
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        """For basic_auth check."""
        return check_password_hash(self.password_hash, password)

    def generate_auth_token(self, expiration=600):
        """Generate a token on the fly."""
        s = Serializer(current_app.config['SECRET_KEY'], expires_in=expiration)
        expiration_date = int(time.time()) + expiration
        token = s.dumps({'id': self.id, 'expiration': expiration_date})
        return token

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
        except SignatureExpired:
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

    def get_salt_acl(self):
        """
        Export user acl to a dictionary.

        Will need to be update later on.
        """
        data = []
        dict_data = {}
        for acl in self.acls:
            minions = str(acl.minions)
            functions = str(acl.functions)
            if minions == '.*':
                data.append(functions)
            else:
                if minions not in dict_data:
                    dict_data[minions] = []
                dict_data[minions].append(functions)

        for minion, functions in dict_data.iteritems():
            data.append({minion: functions})
        return data

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
                'acls': url_for('api.get_acls', user_id=self.id),
                'tokens': url_for('api.new_token')
            }
        }
