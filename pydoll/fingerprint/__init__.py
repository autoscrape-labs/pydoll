"""
Browser fingerprint spoofing module for pydoll.

This module provides comprehensive browser fingerprinting protection by generating
random but realistic browser fingerprints and injecting them into the browser.
"""

from .generator import FingerprintGenerator
from .injector import FingerprintInjector
from .manager import FingerprintManager
from .models import Fingerprint, FingerprintConfig

# Global fingerprint manager instance
FINGERPRINT_MANAGER = FingerprintManager()

__all__ = [
    'FingerprintGenerator',
    'FingerprintInjector',
    'FingerprintManager',
    'Fingerprint',
    'FingerprintConfig',
    'FINGERPRINT_MANAGER',
]
