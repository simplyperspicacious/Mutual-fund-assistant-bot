import os
import subprocess
import sys
import time
from datetime import datetime

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')  # type: ignore
except Exception:
    pass

try:
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')  # type: ignore
except Exception:
    pass

# Add the project root to the path so we can import from phases
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

def run_command(command_list, description):
    """Run a shell command and print the outcome."""
    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] --- Executing: {description} ---")
    start_time = time.time()
    
    try:
        # Use subprocess to run the command interactively in real-time
        result = subprocess.run(
            command_list, 
            cwd=BASE_DIR, 
            stdout=sys.stdout,
            stderr=sys.stderr,
            check=True
        )
        duration = time.time() - start_time
        print(f"✅ SUCCESS: {description} completed in {duration:.2f}s")
        return True
    except subprocess.CalledProcessError as e:
        duration = time.time() - start_time
        print(f"❌ FAILURE: {description} failed after {duration:.2f}s with exit code {e.returncode}")
        return False

def main():
    print("=" * 60)
    print("  PPFAS Mutual Fund Assistant - Automated Refresh Pipeline")
    print("=" * 60)

    # Note: We use relative paths referencing BASE_DIR
    python_exec = sys.executable
    
    # ---------------------------------------------------------
    # STEP 1: Execute Phase 1 (Ingestion/Scraping)
    # ---------------------------------------------------------
    success = run_command(
        [python_exec, os.path.join("phase1_ingestion", "scraper.py")], 
        "Phase 1: Web Scraper (Playwright)"
    )
    if not success:
        print("\n🚨 PIPELINE ABORTED: Scraper failed.")
        sys.exit(1)

    # ---------------------------------------------------------
    # STEP 2: Verify Phase 1 Output
    # ---------------------------------------------------------
    success = run_command(
        [python_exec, "-m", "pytest", os.path.join("tests", "test_scraper.py"), "-v"], 
        "Data Integrity Check (test_scraper.py)"
    )
    if not success:
        print("\n🚨 PIPELINE ABORTED: Scraper extracted corrupted or missing data.")
        sys.exit(1)
        
    # ---------------------------------------------------------
    # STEP 3: Execute Phase 2 (Indexing/FAISS)
    # ---------------------------------------------------------
    success = run_command(
        [python_exec, os.path.join("phase2_indexing", "indexer.py")], 
        "Phase 2: Semantic Indexing (FAISS)"
    )
    if not success:
        print("\n🚨 PIPELINE ABORTED: Indexer failed.")
        sys.exit(1)

    # ---------------------------------------------------------
    # STEP 4: Verify Phase 2 Output
    # ---------------------------------------------------------
    success = run_command(
        [python_exec, "-m", "pytest", os.path.join("tests", "test_indexer.py"), "-v"], 
        "Vector Store Integrity Check (test_indexer.py)"
    )
    if not success:
        print("\n🚨 PIPELINE ABORTED: Vector database was built incorrectly.")
        sys.exit(1)

    # ---------------------------------------------------------
    # STEP 5: Regression Testing (Phase 3, 4, 5)
    # ---------------------------------------------------------
    success = run_command(
        [python_exec, "-m", "pytest", os.path.join("tests", "test_guardrails.py"), "-v"], 
        "Regression Test: AI Guardrails (test_guardrails.py)"
    )
    if not success:
        print("\n🚨 PIPELINE ABORTED: Guardrails failed. The prompt injection filter is broken.")
        sys.exit(1)
        
    success = run_command(
        [python_exec, "-m", "pytest", os.path.join("tests", "test_api.py"), "-v"], 
        "Regression Test: FastAPI Backend (test_api.py)"
    )
    if not success:
        print("\n🚨 PIPELINE ABORTED: FastAPI Backend failed tests.")
        sys.exit(1)
        
    print("\n" + "=" * 60)
    print(" 🎉 ALL PIPELINE STAGES COMPLETED SUCCESSFULLY 🎉 ")
    print("=" * 60)
    print("The system is now running with the latest Groww.in mutual fund data.")

if __name__ == "__main__":
    main()
