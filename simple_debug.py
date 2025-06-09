print("Starting debug...")

try:
    print("Step 1: Basic imports...")
    import sys
    import os
    print(f"Python version: {sys.version}")
    print(f"Working directory: {os.getcwd()}")
    
    print("Step 2: Testing pydoll import...")
    import pydoll
    print("✓ Pydoll imported")
    
    print("Step 3: Testing fingerprint import...")
    from pydoll.fingerprint.browser import Chrome
    print("✓ Chrome imported")
    
    print("Step 4: Creating Chrome instance...")
    chrome = Chrome()
    print("✓ Chrome created")
    
    print("All steps completed successfully!")
    
except ImportError as e:
    print(f"Import error: {e}")
    import traceback
    traceback.print_exc()
except Exception as e:
    print(f"Other error: {e}")
    import traceback
    traceback.print_exc()

print("Debug script finished.") 