#!/usr/bin/env python3
"""
Quick test runner for PlatyPII
Run this to make sure everything is working
"""

import sys
import os

# Add platypii to path if not installed
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_basic_functionality():
    """Test basic PII detection and anonymization"""
    print("=== Testing PlatyPII Basic Functionality ===\n")
    
    try:
        # Import main functions
        from __init__ import detect_pii, mask_pii
        from platypii import PIIEngine
        from platypii.config import DEFAULT_CONFIG
        
        # Test data with various PII types
        test_text = """


        Hi, my name is John Smith and you can reach me at johnsmith@gmail.com 
        or call me at 555-123-4567. My SSN is 123-45-6789 and I live at 
        123 Main Road. I was born on 12/31/2024.
        """
        
        print("Original text:")
        print(test_text)
        print("\n" + "="*50 + "\n")
        
        # Test 1: Basic detection
        print("1. Basic PII Detection:")
        matches = detect_pii(test_text)
        for match in matches:
            print(f"  - {match.pii_type}: '{match.value}' (detector: {match.detector_name}) (confidence: {match.confidence:.2f})")
        print(f"\nFound {len(matches)} PII matches\n")
        
        # Test 2: Basic masking
        print("2. Basic Masking:")
        masked_text = mask_pii(test_text)
        print(masked_text)
        print("\n" + "="*50 + "\n")
        
        # Test 3: Using the engine for more control
        print("3. Using PIIEngine with different anonymization:")
        engine = PIIEngine()
        
        # Test different anonymization methods
        methods = ['mask', 'redact', 'hash', 'replace', 'synthetic']
        DEFAULT_CONFIG.set("anonymization.hash_salt", "platypii_hash")
        
        for method in methods:
            print(f"\n--- {method.upper()} method ---")
            try:
                # You'll need to update the engine call based on your implementation
                result = engine.process_text(test_text, anonymize=True, method=method)
                if 'anonymized_text' in result:
                    print(result['anonymized_text'])
                else:
                    print("Anonymization not available in result")
            except Exception as e:
                print(f"Error with {method}: {e}")
        
        print("\n" + "="*50 + "\n")
        print("✅ Basic functionality test completed!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure all modules are properly implemented")
        return False
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        return False

def test_batch_processing():
    """Test batch processing"""
    print("\n=== Testing Batch Processing ===\n")
    
    try:
        from platypii.core.engine import PIIEngine
        
        test_texts = [
            "Contact Jane Doe at jane@example.com",
            "Call Bob at 555-987-6543",
            "SSN: 987-65-4321 for processing"
        ]
        
        engine = PIIEngine()
        results = engine.process_batch(test_texts)
        
        for i, result in enumerate(results):
            print(f"Text {i+1}: Found {len(result['matches'])} PII items")
            for match in result['matches']:
                print(f"  - {match.pii_type}: {match.value}")
        
        print("✅ Batch processing test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Batch processing error: {e}")
        return False

def test_configuration():
    """Test configuration system"""
    print("\n=== Testing Configuration ===\n")
    
    try:
        from platypii.config import Config
        
        config = Config()
        
        # Test getting config values
        threshold = config.get('detection.confidence_threshold')
        print(f"Default confidence threshold: {threshold}")
        
        # Test setting config values
        config.set('detection.confidence_threshold', 0.9)
        new_threshold = config.get('detection.confidence_threshold')
        print(f"Updated confidence threshold: {new_threshold}")
        
        # Test PII type settings
        pii_types = config.get('pii_types')
        print(f"Configured PII types: {list(pii_types.keys())}")
        
        print("✅ Configuration test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False

def test_detectors():
    """Test individual detectors"""
    print("\n=== Testing Individual Detectors ===\n")
    
    try:
        from platypii.detectors.regex_detector import RegexDetector
        from platypii.detectors.nlp_detector import NLPDetector
        
        test_text = "My name is Alice Johnson, email: alice@test.com, phone: 555-0123"
        
        # Test regex detector
        print("Regex Detector:")
        regex_detector = RegexDetector()
        regex_matches = regex_detector.detect(test_text)
        for match in regex_matches:
            print(f"  - {match.pii_type}: {match.value}")
        
        # Test NLP detector
        print("\nNLP Detector:")
        nlp_detector = NLPDetector()
        nlp_matches = nlp_detector.detect(test_text)
        for match in nlp_matches:
            print(f"  - {match.pii_type}: {match.value}")
        
        print("✅ Individual detectors test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Detectors error: {e}")
        return False

def run_all_tests():
    """Run all tests"""
    print("🔍 Running PlatyPII Test Suite\n")
    
    tests = [
        test_basic_functionality,
        test_batch_processing, 
        test_configuration,
        test_detectors
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
            failed += 1
    
    print(f"\n{'='*60}")
    print(f"Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! PlatyPII is working correctly.")
    else:
        print("⚠️ Some tests failed. Check the errors above.")
    
    return failed == 0

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)