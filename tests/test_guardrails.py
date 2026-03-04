import sys
import os

# Add root to sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from phase3_guardrails.controller import QueryGuardrail

def test_pii_blocking():
    print("Testing PII Blocking...")
    queries = [
        "My phone number is 9876543210",
        "My email is test@example.com",
        "My PAN is ABCDE1234F"
    ]
    for q in queries:
        res = QueryGuardrail.validate_query(q)
        assert not res["is_valid"], f"Should have blocked: {q}"
        assert "Personal financial information" in res["message"]
    print("✅ PII Blocking passed.")

def test_advisory_blocking():
    print("Testing Advisory Blocking...")
    queries = [
        "Should I invest in Parag Parikh Flexi Cap?",
        "Is this fund good for me?",
        "suggest some mutual funds"
    ]
    for q in queries:
        res = QueryGuardrail.validate_query(q)
        if res["is_valid"]:
            print(f"FAILED: '{q}' should have been blocked.")
            assert not res["is_valid"]
        if "factual information" not in res["message"]:
             print(f"FAILED: '{q}' message missing advisory disclaimer. Got: {res['message']}")
             assert "factual information" in res["message"]
    print("✅ Advisory Blocking passed.")

def test_valid_queries():
    print("Testing Valid Queries...")
    queries = [
        "What is the exit load of the Liquid Fund?",
        "What is the minimum SIP?",
        "Tell me about the expense ratio"
    ]
    for q in queries:
        res = QueryGuardrail.validate_query(q)
        assert res["is_valid"], f"Should have allowed: {q}"
    print("✅ Valid Queries passed.")

if __name__ == "__main__":
    try:
        test_pii_blocking()
        test_advisory_blocking()
        test_valid_queries()
        print("\n🎉 Guardrail Unit Tests Passed!")
    except AssertionError as e:
        print(f"\n❌ Test Failed: {e}")
        sys.exit(1)
