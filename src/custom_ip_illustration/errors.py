class CustomIPIllustrationError(Exception):
    """Base error for deterministic compilation failures."""


class ValidationError(CustomIPIllustrationError):
    """Input data does not satisfy the public contract."""


class SecurityError(CustomIPIllustrationError):
    """A path, preference, or release file violates a safety boundary."""
