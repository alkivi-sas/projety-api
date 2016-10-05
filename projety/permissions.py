"""Manage the permissions of our API."""
import logging

from flask_principal import Permission, RoleNeed, UserNeed

logger = logging.getLogger(__name__)


class AdminPermission(Permission):
    """Admin permission."""

    def __init__(self):
        """Only one need, need to be admin."""
        need = (RoleNeed('admin'),)
        super(AdminPermission, self).__init__(*need)


class BasicPermission(Permission):
    """Basic permission."""

    def __init__(self, user_id):
        """Two needs : admin + self."""
        need = (RoleNeed('admin'), UserNeed(int(user_id)))
        super(BasicPermission, self).__init__(*need)


class AclReadPermission(BasicPermission):
    """Special to ACL."""

    pass


class AclWritePermission(AdminPermission):
    """Special to ACL."""

    pass


class RoleReadPermission(BasicPermission):
    """Special to Role."""

    pass


class RoleWritePermission(AdminPermission):
    """Special to Role."""

    pass
