"""API Exceptions."""


class ValidationError(ValueError):
    """Exception for validation."""

    pass


class SaltError(ValueError):
    """Exception for wrong salt return."""

    pass


class ACLError(ValueError):
    """Exception when not allowed."""

    pass
