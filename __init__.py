"""
PlatyPII - A comprehensive PII detection, masking, and redaction library.

This package provides tools for:
- Detecting personally identifiable information (PII) in text
- Masking or redacting sensitive information
- Generating reports on PII findings
- Customizable detection rules and patterns
"""

__version__ = "0.1.0"
__description__ = "A comprehensive PII detection and redaction library"

# Import main classes for easy access
from platypii.core import PIIDetector
from platypii.core import PIIEngine
from platypii.core import PIIEngine
from .processors.anonymizer import Anonymizer
from .outputs.formatters import ReportFormatter

# Define what gets imported with "from platypii import *"
__all__ = [
    "PIIDetector",
    "PIIEngine", 
    "Anonymizer",
    "ReportFormatter",
    "__version__",
]

# Convenience function for quick detection
def detect_pii(text, config=None):
    """
    Quick PII detection function for simple use cases.
    
    Args:
        text (str): Text to analyze for PII
        config (dict, optional): Configuration options
        
    Returns:
        dict: Detection results
    """
    detector = PIIDetector(config=config)
    return detector.detect(text)

def mask_pii(text, mask_char="*", config=None):
    """
    Quick PII masking function for simple use cases.
    
    Args:
        text (str): Text to mask PII in
        mask_char (str): Character to use for masking
        config (dict, optional): Configuration options
        
    Returns:
        str: Text with PII masked
    """
    detector = PIIDetector(config=config)
    anonymizer = Anonymizer(mask_char=mask_char)
    detections = detector.detect(text)
    return anonymizer.mask(text, detections)