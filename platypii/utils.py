"""
Utility functions for PlatyPII.

This module contains helper functions used throughout the library.
"""

import re
import hashlib
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class PIIMatch:
    """Data structure for PII detection results."""
    pii_type: str
    value: str
    start: int
    end: int
    confidence: float
    context: str = ""
    detector_name: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "pii_type": self.pii_type,
            "value": self.value,
            "start": self.start,
            "end": self.end,
            "confidence": self.confidence,
            "context": self.context,
            "detector_name": self.detector_name,
            "length": self.end - self.start
        }

class TextProcessor:    
    @staticmethod
    def extract_context(text: str, start: int, end: int, window: int = 50) -> str:
        """
        Extract context around a detected PII match.
        
        Args:
            text (str): Full text
            start (int): Start position of match
            end (int): End position of match  
            window (int): Characters to include on each side
            
        Returns:
            str: Context string
        """
        context_start = max(0, start - window)
        context_end = min(len(text), end + window)
        
        context = text[context_start:context_end]
        
        # Add ellipsis if truncated
        if context_start > 0:
            context = "..." + context
        if context_end < len(text):
            context = context + "..."
            
        return context

class Validator:
    """Validation utilities for PII patterns."""
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """
        Validate email address format.
        
        Args:
            email (str): Email to validate
            
        Returns:
            bool: True if valid format
        """
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod  
    def validate_phone(phone: str) -> bool:
        """
        Validate phone number format (US/international).
        
        Args:
            phone (str): Phone number to validate
            
        Returns:
            bool: True if valid format
        """
        # Remove common separators
        clean_phone = re.sub(r'[-.\s()+]', '', phone)
        
        # Check for valid phone patterns
        patterns = [
            r'^\d{10}$',  # US 10-digit
            r'^1\d{10}$',  # US with country code
            r'^\+1\d{10}$',  # US with +1
            r'^\+\d{10,15}$',  # International
        ]
        
        return any(re.match(pattern, clean_phone) for pattern in patterns)
    
    @staticmethod
    def validate_ssn(ssn: str) -> bool:
        """
        Validate SSN format and basic rules.
        
        Args:
            ssn (str): SSN to validate
            
        Returns:
            bool: True if valid format
        """
        # Remove separators
        clean_ssn = re.sub(r'[-\s]', '', ssn)
        
        # Check format
        if not re.match(r'^\d{9}$', clean_ssn):
            return False
        
        # Basic validation rules
        area = clean_ssn[:3]
        group = clean_ssn[3:5]
        serial = clean_ssn[5:9]
        
        # Invalid area numbers
        if area in ['000', '666'] or area.startswith('9'):
            return False
        
        # Invalid group/serial
        if group == '00' or serial == '0000':
            return False
            
        return True
    
    @staticmethod
    def validate_credit_card(cc: str) -> bool:
        """
        Validate credit card using Luhn algorithm.
        
        Args:
            cc (str): Credit card number
            
        Returns:
            bool: True if passes Luhn check
        """
        # Remove spaces and dashes
        clean_cc = re.sub(r'[-\s]', '', cc)
        
        # Check if all digits and reasonable length
        if not clean_cc.isdigit() or len(clean_cc) < 13 or len(clean_cc) > 19:
            return False
        
        # Luhn algorithm
        def luhn_check(card_num):
            total = 0
            reverse_digits = card_num[::-1]
            
            for i, digit in enumerate(reverse_digits):
                n = int(digit)
                if i % 2 == 1:  # Every second digit from the right
                    n *= 2
                    if n > 9:
                        n = n // 10 + n % 10
                total += n
                
            return total % 10 == 0
        
        return luhn_check(clean_cc)

class HashGenerator:
    """Generate hashes for PII anonymization."""
    
    @staticmethod
    def hash_pii(value: str, salt: str = "platypii", algorithm: str = "sha256") -> str:
        """
        Generate hash for PII value.
        
        Args:
            value (str): PII value to hash
            salt (str): Salt for hashing
            algorithm (str): Hash algorithm
            
        Returns:
            str: Hashed value
        """
        hasher = hashlib.new(algorithm)
        hasher.update((value + salt).encode('utf-8'))
        return hasher.hexdigest()
    
    @staticmethod
    def generate_replacement(pii_type: str, preserve_format: bool = True, original: str = "") -> str:
        """
        Generate replacement value for PII.
        
        Args:
            pii_type (str): Type of PII
            preserve_format (bool): Whether to preserve original format
            original (str): Original value for format reference
            
        Returns:
            str: Replacement value
        """
        if not preserve_format:
            return f"[{pii_type.upper()}]"
        
        # Format-preserving replacements
        format_map = {
            "ssn": "XXX-XX-XXXX" if "-" in original else "XXXXXXXXX",
            "phone": "XXX-XXX-XXXX" if "-" in original else "XXXXXXXXXX", 
            "credit_card": "XXXX-XXXX-XXXX-XXXX" if "-" in original else "XXXXXXXXXXXXXXXX",
            "email": "user@domain.com",
            "date": "XX/XX/XXXX" if "/" in original else "XXXXXXXX"
        }
        
        return format_map.get(pii_type, f"[{pii_type.upper()}]")

class Performance:
    """Performance monitoring utilities."""
    
    def __init__(self):
        self.start_time = None
        self.metrics = {}
    
    def start_timer(self, name: str) -> None:
        """Start timing an operation."""
        self.metrics[name] = {"start": datetime.now()}
    
    def end_timer(self, name: str) -> float:
        """End timing and return duration in seconds."""
        if name not in self.metrics:
            return 0.0
        
        end_time = datetime.now()
        duration = (end_time - self.metrics[name]["start"]).total_seconds()
        self.metrics[name]["duration"] = duration
        self.metrics[name]["end"] = end_time
        
        return duration
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get all performance metrics."""
        return self.metrics.copy()

def setup_logging(level: str = "INFO", log_file: Optional[str] = None) -> None:
    """
    Setup logging configuration.
    
    Args:
        level (str): Logging level
        log_file (str, optional): Log file path
    """
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    if log_file:
        logging.basicConfig(
            level=getattr(logging, level.upper()),
            format=log_format,
            filename=log_file,
            filemode='a'
        )
    else:
        logging.basicConfig(
            level=getattr(logging, level.upper()),
            format=log_format
        )

def merge_overlapping_matches(matches: List[PIIMatch]) -> List[PIIMatch]:
    """
    Merge overlapping PII matches, keeping the highest confidence.
    
    Args:
        matches (List[PIIMatch]): List of PII matches
        
    Returns:
        List[PIIMatch]: Merged matches
    """
    if not matches:
        return []
    
    # Sort by position
    sorted_matches = sorted(matches, key=lambda m: m.start)
    merged = [sorted_matches[0]]
    
    for current in sorted_matches[1:]:
        last = merged[-1]
        
        # Check for overlap
        if current.start <= last.end:
            # Keep match with higher confidence
            if current.confidence > last.confidence:
                merged[-1] = current
        else:
            merged.append(current)
    
    return merged