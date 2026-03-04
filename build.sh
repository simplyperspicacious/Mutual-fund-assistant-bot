#!/usr/bin/env bash
# exit on error
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Rebuild the FAISS index from structured data
echo "Rebuilding FAISS index..."
python phase2_indexing/indexer.py

echo "Build complete."
