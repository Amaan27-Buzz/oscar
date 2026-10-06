"""Legacy import compatibility. Active mobile implementation lives in oscar.mobile."""

from .mobile import Mobile as Sunday
from .mobile import MobileServer as SundayServer

__all__ = ["Sunday", "SundayServer"]
