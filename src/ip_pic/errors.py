"""Public error hierarchy for ip-pic."""


class IPPicError(ValueError):
    """Base class for deterministic input and contract failures."""


class PerformanceError(IPPicError):
    """Character performance data is invalid."""
