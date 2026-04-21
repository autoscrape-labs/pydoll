import asyncio
import os
import shutil
from pathlib import Path
import pytest
from pydoll.browser.chromium import Chrome
from pydoll.decorators import debug_snapshot

# Define a temporary snapshot directory for testing
TEST_SNAPSHOT_DIR = Path("test_debug_snapshots")

@pytest.fixture(autouse=True)
def cleanup_snapshots():
    """Cleanup test snapshots after each test."""
    if TEST_SNAPSHOT_DIR.exists():
        shutil.rmtree(TEST_SNAPSHOT_DIR)
    yield
    if TEST_SNAPSHOT_DIR.exists():
        shutil.rmtree(TEST_SNAPSHOT_DIR)

@debug_snapshot(save_dir=TEST_SNAPSHOT_DIR)
async def failing_task(tab):
    """A task that navigates and then fails."""
    await tab.go_to("https://example.com")
    await asyncio.sleep(1)
    raise ValueError("Deliberate failure for testing")

@pytest.mark.asyncio
async def test_debug_snapshot_generation(ci_chrome_options):
    """Verify that debug_snapshot decorator generates all required files on failure."""
    
    async with Chrome(options=ci_chrome_options) as browser:
        tab = await browser.start()
        
        # We expect the exception to be re-raised
        with pytest.raises(ValueError, match="Deliberate failure for testing"):
            await failing_task(tab)
            
    # Verify that the snapshot folder was created
    assert TEST_SNAPSHOT_DIR.exists(), "Snapshot directory was not created"
    
    # Find the most recently created subfolder (should be only one)
    folders = list(TEST_SNAPSHOT_DIR.iterdir())
    assert len(folders) == 1, f"Expected 1 snapshot folder, found {len(folders)}"
    
    snapshot_path = folders[0]
    assert snapshot_path.name.startswith("failing_task_")
    
    # Check for required files
    mhtml_file = snapshot_path / "bundle.mhtml"
    har_file = snapshot_path / "network.har"
    log_file = snapshot_path / "traceback.log"
    
    assert mhtml_file.exists(), "bundle.mhtml is missing"
    assert har_file.exists(), "network.har is missing"
    assert log_file.exists(), "traceback.log is missing"
    
    # Verify file content basic checks
    assert mhtml_file.stat().st_size > 0, "bundle.mhtml is empty"
    assert har_file.stat().st_size > 0, "network.har is empty"
    
    with open(log_file, "r") as f:
        log_content = f.read()
        assert "ValueError: Deliberate failure for testing" in log_content
        assert "failing_task" in log_content

    print(f"Integration test passed! Snapshot captured in {snapshot_path}")
