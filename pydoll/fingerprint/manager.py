"""
Browser fingerprint management module.

This module provides the FingerprintManager class which coordinates fingerprint
generation, storage, and application to browser instances.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional

from .generator import FingerprintGenerator
from .injector import FingerprintInjector
from .models import Fingerprint, FingerprintConfig


class FingerprintManager:
    """
    Manages browser fingerprint generation and application.

    This class coordinates the entire fingerprint spoofing process, from
    generation to injection into browser instances.
    """

    def __init__(self, config: Optional[FingerprintConfig] = None):
        """
        Initialize the fingerprint manager.

        Args:
            config: Configuration for fingerprint generation. Uses default if None.
        """
        self.config = config or FingerprintConfig()
        self.generator = FingerprintGenerator(self.config)
        self.current_fingerprint: Optional[Fingerprint] = None
        self.injector: Optional[FingerprintInjector] = None

        # Storage directory for fingerprints
        self.storage_dir = Path.home() / '.pydoll' / 'fingerprints'
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def generate_new_fingerprint(
        self, browser_type: str = 'chrome', force: bool = False
    ) -> Fingerprint:
        """
        Generate a new browser fingerprint.

        Args:
            browser_type: Type of browser ('chrome' or 'edge').
            force: Whether to force generation of a new fingerprint even if one exists.

        Returns:
            The generated fingerprint.
        """
        if self.current_fingerprint and not force:
            return self.current_fingerprint

        # Update config with browser type
        self.config.browser_type = browser_type
        self.generator.config.browser_type = browser_type

        # Generate new fingerprint
        self.current_fingerprint = self.generator.generate()

        # Create injector for this fingerprint
        self.injector = FingerprintInjector(self.current_fingerprint)

        return self.current_fingerprint

    def get_current_fingerprint(self) -> Optional[Fingerprint]:
        """
        Get the current active fingerprint.

        Returns:
            The current fingerprint or None if none has been generated.
        """
        return self.current_fingerprint

    def get_fingerprint_js(self) -> str:
        """
        Get JavaScript injection code for the current fingerprint.

        Returns:
            JavaScript code as a string.

        Raises:
            ValueError: If no fingerprint has been generated.
        """
        if not self.injector:
            raise ValueError(
                "No fingerprint has been generated. Call generate_new_fingerprint() first."
            )

        return self.injector.generate_script()

    def get_fingerprint_arguments(self, browser_type: str = 'chrome') -> List[str]:
        """
        Get command line arguments for fingerprint spoofing.

        Args:
            browser_type: Type of browser ('chrome' or 'edge').

        Returns:
            List of command line arguments.

        Raises:
            ValueError: If no fingerprint has been generated.
        """
        if not self.current_fingerprint:
            raise ValueError(
                "No fingerprint has been generated. Call generate_new_fingerprint() first."
            )

        args = []

        # User agent
        args.append(f'--user-agent={self.current_fingerprint.user_agent}')

        # Language settings
        args.append(f'--lang={self.current_fingerprint.language}')

        # Window size
        args.append(
            f'--window-size={self.current_fingerprint.viewport_width},'
            f'{self.current_fingerprint.viewport_height}'
        )

        # Hardware concurrency (for Chrome)
        if browser_type == 'chrome':
            args.append(
                f'--force-cpu-count={self.current_fingerprint.hardware_concurrency}'
            )

        # Disable automation features
        args.extend([
            '--disable-blink-features=AutomationControlled',
            '--exclude-switches=enable-automation',
            '--disable-extensions-except',
            '--disable-plugins-discovery',
            '--no-first-run',
            '--no-service-autorun',
            '--password-store=basic',
            '--use-mock-keychain',
        ])

        return args

    def save_fingerprint(self, name: str, fingerprint: Optional[Fingerprint] = None) -> str:
        """
        Save a fingerprint to disk for later reuse.

        Args:
            name: Name to save the fingerprint under.
            fingerprint: Fingerprint to save. Uses current if None.

        Returns:
            Path where the fingerprint was saved.

        Raises:
            ValueError: If no fingerprint is provided and none is current.
        """
        fp = fingerprint or self.current_fingerprint
        if not fp:
            raise ValueError("No fingerprint provided and no current fingerprint exists.")

        # Create filename
        filename = f"{name}.json"
        filepath = self.storage_dir / filename

        # Save fingerprint
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(fp.to_dict(), f, indent=2, ensure_ascii=False)

        return str(filepath)

    def load_fingerprint(self, name: str) -> Fingerprint:
        """
        Load a saved fingerprint from disk.

        Args:
            name: Name of the fingerprint to load.

        Returns:
            The loaded fingerprint.

        Raises:
            FileNotFoundError: If the fingerprint file doesn't exist.
            ValueError: If the fingerprint file is invalid.
        """
        filename = f"{name}.json"
        filepath = self.storage_dir / filename

        if not filepath.exists():
            raise FileNotFoundError(f"Fingerprint '{name}' not found at {filepath}")

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            fingerprint = Fingerprint.from_dict(data)

            # Set as current fingerprint and create injector
            self.current_fingerprint = fingerprint
            self.injector = FingerprintInjector(fingerprint)

            return fingerprint

        except (json.JSONDecodeError, TypeError, KeyError) as e:
            raise ValueError(f"Invalid fingerprint file '{name}': {e}")

    def list_saved_fingerprints(self) -> List[str]:
        """
        List all saved fingerprints.

        Returns:
            List of fingerprint names.
        """
        fingerprints = []
        for filepath in self.storage_dir.glob("*.json"):
            fingerprints.append(filepath.stem)
        return sorted(fingerprints)

    def delete_fingerprint(self, name: str) -> bool:
        """
        Delete a saved fingerprint.

        Args:
            name: Name of the fingerprint to delete.

        Returns:
            True if deleted successfully, False if file didn't exist.
        """
        filename = f"{name}.json"
        filepath = self.storage_dir / filename

        if filepath.exists():
            filepath.unlink()
            return True
        return False

    def clear_current_fingerprint(self):
        """Clear the current fingerprint and injector."""
        self.current_fingerprint = None
        self.injector = None

    def get_fingerprint_summary(self, fingerprint: Optional[Fingerprint] = None) -> Dict[str, str]:
        """
        Get a human-readable summary of a fingerprint.

        Args:
            fingerprint: Fingerprint to summarize. Uses current if None.

        Returns:
            Dictionary with fingerprint summary information.

        Raises:
            ValueError: If no fingerprint is provided and none is current.
        """
        fp = fingerprint or self.current_fingerprint
        if not fp:
            raise ValueError("No fingerprint provided and no current fingerprint exists.")

        return {
            'Browser': f"{fp.browser_type.title()} {fp.browser_version}",
            'User Agent': fp.user_agent,
            'Platform': fp.platform,
            'Language': fp.language,
            'Screen': f"{fp.screen_width}x{fp.screen_height}",
            'Viewport': f"{fp.viewport_width}x{fp.viewport_height}",
            'WebGL Vendor': fp.webgl_vendor,
            'WebGL Renderer': fp.webgl_renderer,
            'Hardware Concurrency': str(fp.hardware_concurrency),
            'Device Memory': f"{fp.device_memory}GB" if fp.device_memory else "Not set",
            'Timezone': fp.timezone,
            'Canvas Fingerprint': fp.canvas_fingerprint[:32] + "...",
        }
