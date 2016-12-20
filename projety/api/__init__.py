"""API only package."""

from flask import Blueprint

api = Blueprint('api', __name__)

from . import tokens, users, minions, tasks, ping, errors, acls, roles, jobs  # noqa
