class BlackboardAPIError(RuntimeError):
    """Base exception for the Blackboard client."""


class AuthenticationError(BlackboardAPIError):
    pass


class QuotaExhaustedError(BlackboardAPIError):
    """The quota reported by Blackboard is exactly zero."""


class TransportError(BlackboardAPIError):
    pass


class ResponseFormatError(BlackboardAPIError):
    """The Blackboard response has an unexpected format."""


class NotFoundError(BlackboardAPIError):
    """Blackboard could not find the requested resource."""


class WriteNotEnabledError(BlackboardAPIError):
    """The operation is blocked because writes are not enabled."""
