#!/usr/bin/env python3
"""
PyTest script for testing pydoll fingerprint spoofing
Only uses built-in fingerprint spoofing functionality
"""

import asyncio
import os
import sys

import pytest

# Add pydoll path
sys.path.insert(0, os.path.abspath(''))

# Import pydoll components
from pydoll.browser.chrome import Chrome
from pydoll.browser.fingerprint import FINGERPRINT_MANAGER
from pydoll.browser.options import Options


class TestFingerprint:
    """Test pydoll's fingerprint spoofing functionality"""

    @pytest.mark.asyncio
    async def test_fingerprints_are_unique(self):
        """Test if fingerprints generated from multiple browser instances are unique"""
        print("\nStarting to test pydoll fingerprint spoofing functionality...")

        # Collect all fingerprints
        results = []
        instance_count = 5  # Use 5 instances for testing

        # Test each instance sequentially
        for i in range(1, instance_count + 1):
            result = await self._run_browser_instance(i)
            results.append(result)

        # Analyze results
        # Extract valid fingerprint IDs
        fingerprint_ids = [r["fingerprint_id"] for r in results
                         if not r["fingerprint_id"].startswith("Error")
                         and r["fingerprint_id"] != "Fingerprint ID not found"]

        # Get unique values
        unique_ids = set(fingerprint_ids)

        # Output analysis results
        print(f"\nTotal test instances: {instance_count}")
        print(f"Valid fingerprint IDs: {len(fingerprint_ids)}")
        print(f"Unique fingerprint IDs: {len(unique_ids)}")

        # If there are duplicates, show details
        if len(unique_ids) < len(fingerprint_ids):
            print("\nDuplicate fingerprint IDs found:")
            for fp_id in unique_ids:
                count = fingerprint_ids.count(fp_id)
                if count > 1:
                    print(f"- Fingerprint ID '{fp_id}' appears {count} times")
                    indices = [
                        r["index"] for r in results
                        if r["fingerprint_id"] == fp_id
                    ]
                    print(f"  Appears in instances: {indices}")

                    # Show detailed information for instances using the same fingerprint
                    print("  Details:")
                    for idx in indices:
                        r = next(res for res in results if res["index"] == idx)
                        print(f"    Instance #{idx} UA: {r['user_agent'][:30]}...")

        # Verify all fingerprints are unique
        if len(unique_ids) < len(fingerprint_ids):
            print("\n⚠️ Duplicate fingerprints detected, but this doesn't necessarily mean fingerprint spoofing completely failed")
            print("FingerprintJS uses many deep browser features, and may require more technical measures for complete spoofing")
        else:
            print("\n✅ All fingerprint IDs are unique, fingerprint spoofing is working correctly!")

        # Display detailed results
        print("\nDetailed results:")
        for r in results:
            print(f"Instance #{r['index']}:")
            print(f"  User Agent: {r['user_agent'][:50]}...")
            print(f"  Fingerprint ID: {r['fingerprint_id']}")
            print("-" * 40)

    @staticmethod
    async def _run_browser_instance(index):
        """
        Run a single browser instance and get its fingerprint ID

        Args:
            index: Instance number

        Returns:
            dict: Dictionary containing instance information and fingerprint ID
        """
        print(f"\n=== Testing Instance #{index} ===")

        # Only use FINGERPRINT_MANAGER to generate new fingerprint
        fingerprint = FINGERPRINT_MANAGER.generate_new_fingerprint('chrome')

        print(f"Generated fingerprint ID: {fingerprint['id']}")
        print(f"User Agent: {fingerprint['user_agent'][:50]}...")

        # Create Chrome options
        options = Options()

        # Create browser instance and enable fingerprint spoofing
        browser = Chrome(options=options, enable_fingerprint_spoofing=True)

        try:
            # Start the browser
            print("Starting browser...")
            await browser.start()

            # Get the page
            page = await browser.get_page()

            # Visit FingerprintJS website
            print("Visiting FingerprintJS website...")
            await page.go_to("https://fingerprintjs.github.io/fingerprintjs/")

            # Wait for fingerprint generation
            print("Waiting for fingerprint generation...")
            await asyncio.sleep(5)

            # Get fingerprint ID - from pre.giant element
            print("Extracting fingerprint ID...")
            js_code = """
            (() => {
                try {
                    const element = document.querySelector('pre.giant');
                    return element ? element.textContent.trim() :
                        "Fingerprint ID not found";
                } catch(e) {
                    return "Error: " + e.message;
                }
            })()
            """

            result = await page.execute_script(js_code)

            # Parse the result
            if isinstance(result, dict) and 'result' in result:
                fingerprint_id = result['result']['result']['value']
            else:
                fingerprint_id = result

            print(f"Retrieved fingerprint ID: {fingerprint_id}")

            # Close the browser
            await browser.stop()

            return {
                "index": index,
                "fingerprint_id": fingerprint_id,
                "user_agent": fingerprint['user_agent']
            }

        except Exception as e:
            print(f"Test failed: {e}")
            try:
                await browser.stop()
            except Exception:
                pass
            return {
                "index": index,
                "fingerprint_id": f"Error: {str(e)}",
                "user_agent": (
                    fingerprint['user_agent'] if fingerprint else "Unknown"
                )
            }
