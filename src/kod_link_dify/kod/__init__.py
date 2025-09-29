"""
kod_link_dify - Python client for Kod & Dify API
"""

from . import config
from .api import KodClient

__all__ = [
    "config",
    "KodClient",
]
