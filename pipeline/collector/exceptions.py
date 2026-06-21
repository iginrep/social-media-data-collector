class CollectorNotConfigured(RuntimeError):
    """Collector requires credentials, target URLs, or approved access before it can run."""


class CollectorStopped(RuntimeError):
    """Collector hit a safety stop condition: auth wall, forbidden, rate limit, or captcha wall."""
