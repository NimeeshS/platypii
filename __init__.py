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
from platypii.core import PIIDetector, PIIEngine, PIIPipeline
from platypii.detectors import RegexDetector, NLPDetector
from platypii.outputs import DataExporter, ReportFormatter
from platypii.processors import Anonymizer, Preprocessor, Postprocessor

_all__ = [
    "PIIDetector",
    "PIIEngine",
    "PIIPipeline",
    "RegexDetector",
    "NLPDetector",
    "DataExporter",
    "ReportFormatter",
    "Anonymizer",
    "PreProcessor",
    "PostProcessor"
    "__version__"
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

def mask_pii(text, config=None):
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
    anonymizer = Anonymizer()
    detections = detector.detect(text)
    return anonymizer.anonymize_text(text, detections)