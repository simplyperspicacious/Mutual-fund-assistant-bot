import subprocess
import sys
import os

def run_script(path):
    print(f"\n--- Running: {path} ---")
    result = subprocess.run([sys.executable, path], capture_output=False)
    if result.returncode != 0:
        print(f"FAILED: {path}")
        return False
    return True

if __name__ == "__main__":
    scripts = [
        "tests/test_guardrails.py",
        "test_rag.py",
        "tests/test_api.py"
    ]
    
    all_passed = True
    for s in scripts:
        if not run_script(s):
            all_passed = False
            
    if all_passed:
        print("\n✅ ALL TESTS PASSED!")
    else:
        print("\n❌ SOME TESTS FAILED.")
        sys.exit(1)
