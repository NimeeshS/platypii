import re
from typing import List, Dict
from ...utils import PIIMatch, Validator, DEFAULT_CONFIG

class RegexDetector:    
    def __init__(self, config=None):
        self.config = config if config else DEFAULT_CONFIG
        self.validator = Validator()
        
        self.patterns = {
            'email': {
                'pattern': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
                'confidence': 0.9,
                'validate': True
            },
            'phone': {
                'pattern': r'\b(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b',
                'confidence': 0.8,
                'validate': True
            },
            'ssn': {
                'pattern': r'\b\d{3}[-.]?\d{2}[-.]?\d{4}\b',
                'confidence': 0.95,
                'validate': True
            },
            'credit_card': {
                'pattern': r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
                'confidence': 0.85,
                'validate': True
            },
            'ip_address': {
                'pattern': r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b',
                'confidence': 0.8,
                'validate': True
            },
            'name': {
                'pattern': r'\b[A-Z][a-z]{1,15}\s+[A-Z][a-z]{1,15}\b',
                'confidence': 0.6,
                'validate': False
            },
            'address': {
                'pattern': r'\b\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Lane|Ln|Boulevard|Blvd|Apartment|Apt)\b',
                'confidence': 0.7,
                'validate': False
            },
            'date': {
                'pattern': r'\b(?:0[1-9]|1[0-2])[-/](?:0[1-9]|[12]\d|3[01])[-/](?:19|20)\d{2}\b',
                'confidence': 0.8,
                'validate': False
            },
            'driver_license': {
                'pattern': r'\b[A-Z]\d{7,8}\b|\b\d{8,9}\b',
                'confidence': 0.5,
                'validate': False
            },
            'passport': {
                'pattern': r'\b[A-Z]{1,2}\d{6,9}\b',
                'confidence': 0.7,
                'validate': False
            }
        }
    
    def detect(self, text: str) -> List[PIIMatch]:
        if not text:
            return []
        
        matches = []
        
        for pii_type, pattern_info in self.patterns.items():
            if self.config and not self.config.get(f'pii_types.{pii_type}.enabled', True):
                continue
            
            pattern_matches = self._find_pattern_matches(text, pii_type, pattern_info)
            matches.extend(pattern_matches)
        
        return matches
    
    def _find_pattern_matches(self, text: str, pii_type: str, pattern_info: Dict) -> List[PIIMatch]:
        matches = []
        pattern = pattern_info['pattern']
        confidence = pattern_info['confidence']
        should_validate = pattern_info.get('validate', False)
        
        regex_matches = re.finditer(pattern, text, re.IGNORECASE)
        
        for match in regex_matches:
            value = match.group().strip()
            
            if len(value) < 2:
                continue
            
            if should_validate and not self._validate_match(pii_type, value):
                continue
            
            pii_match = PIIMatch(
                pii_type=pii_type,
                value=value,
                start=match.start(),
                end=match.end(),
                confidence=confidence,
                detector_name="regex"
            )
            
            matches.append(pii_match)
        
        return matches
    
    def _validate_match(self, pii_type: str, value: str) -> bool:
        validation_map = {
            'email': self.validator.validate_email,
            'phone': self.validator.validate_phone,
            'ssn': self.validator.validate_ssn,
            'credit_card': self.validator.validate_credit_card,
            'ip_address': self._validate_ip
        }
        
        validator_func = validation_map.get(pii_type)
        if validator_func:
            return validator_func(value)
        
        return True
    
    def _validate_ip(self, ip: str) -> bool:
        try:
            parts = ip.split('.')
            return len(parts) == 4 and all(0 <= int(part) <= 255 for part in parts)
        except (ValueError, AttributeError):
            return False
    
    def add_custom_pattern(self, pii_type: str, pattern: str, confidence: float = 0.5, validate: bool = False):
        self.patterns[pii_type] = {
            'pattern': pattern,
            'confidence': confidence,
            'validate': validate
        }
    
    def remove_pattern(self, pii_type: str):
        if pii_type in self.patterns:
            del self.patterns[pii_type]
    
    def update_pattern_confidence(self, pii_type: str, confidence: float):
        if pii_type in self.patterns:
            self.patterns[pii_type]['confidence'] = confidence
    
    def get_pattern_info(self, pii_type: str = None) -> Dict:
        if pii_type:
            return self.patterns.get(pii_type, {})
        return self.patterns.copy()
    
    def test_pattern(self, pattern: str, test_text: str) -> List[str]:
        matches = re.findall(pattern, test_text, re.IGNORECASE)
        return matches