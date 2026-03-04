import os
import pickle
import pytest

try:
    import faiss     # type: ignore
except ImportError:
    pytest.skip("FAISS is not installed, skipping test_indexer.py", allow_module_level=True)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FAISS_DB_DIR = os.path.join(BASE_DIR, "phase2_indexing", "faiss_db")
INDEX_PATH = os.path.join(FAISS_DB_DIR, "ppfas_index.faiss")
METADATA_PATH = os.path.join(FAISS_DB_DIR, "ppfas_metadata.pkl")

def test_indexer_files_exist():
    assert os.path.exists(INDEX_PATH), f"FAISS Index missing: {INDEX_PATH}"
    assert os.path.exists(METADATA_PATH), f"FAISS Metadata missing: {METADATA_PATH}"

def test_indexer_dimensions_match():
    # 1. Load the FAISS C++ Index
    index = faiss.read_index(INDEX_PATH)
    
    # 2. Load the Python Metadata Dict
    with open(METADATA_PATH, "rb") as f:
        metadata = pickle.load(f)
        
    # The count of semantic matrices in FAISS must exactly equal the count of metadata chunks
    assert index.ntotal == len(metadata), \
        f"CRITICAL CORRUPTION: FAISS has {index.ntotal} vectors but Metadata has {len(metadata)} chunks!"
        
    # The MiniLM-L6-v2 model must ALWAYS output 384 dimensions
    assert index.d == 384, f"Index expected 384 dimensions, found {index.d}!"
