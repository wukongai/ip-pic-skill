class CustomIPIllustrationError(Exception):
    """Base error for deterministic compilation failures."""


class ValidationError(CustomIPIllustrationError):
    """Input data does not satisfy the public contract."""


class UnsupportedPlatformError(ValidationError):
    """The current platform cannot provide the required secure filesystem APIs."""


class SecurityError(CustomIPIllustrationError):
    """A path, preference, or release file violates a safety boundary."""


class CredentialError(CustomIPIllustrationError):
    """Credential configuration is invalid without exposing its value."""


class RenderError(CustomIPIllustrationError):
    """A remote image rendering request could not be completed."""
