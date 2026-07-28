class IpPicError(Exception):
    """Base error for deterministic compilation failures."""


class ValidationError(IpPicError):
    """Input data does not satisfy the public contract."""


class UnsupportedPlatformError(ValidationError):
    """The current platform cannot provide the required secure filesystem APIs."""


class SecurityError(IpPicError):
    """A path, preference, or release file violates a safety boundary."""


class CredentialError(IpPicError):
    """Credential configuration is invalid without exposing its value."""


class RenderError(IpPicError):
    """A remote image rendering request could not be completed."""
