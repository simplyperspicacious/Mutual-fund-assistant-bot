import os
import sys

# Add root to path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

try:
    from phase4_rag.rag_engine import RAGEngine
    print("Successfully imported RAGEngine")
    
    rag = RAGEngine()
    print("Successfully initialized RAGEngine")
    
    result = rag.generate_answer("What is the exit load for the Liquid Fund?")
    print("\nTest Result:")
    print(f"Answer: {result['answer']}")
    print(f"Sources: {result['sources']}")
    
except Exception as e:
    print(f"\nCaught Exception: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
