"""API only package."""

from flask import Blueprint

api = Blueprint('api', __name__)

from . import tokens, users, keys, tasks, ping, async_ping  # noqa
