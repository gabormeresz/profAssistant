"""
Shared rate-limiter instance.

Extracted into its own module to avoid circular imports between
``main.py`` (which mounts routers) and route modules (which decorate
endpoints).
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
