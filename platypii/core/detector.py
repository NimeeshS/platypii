import re
from typing import List, Dict, Any
from ...utils import PIIMatch, TextProcessor, merge_overlapping_matches
from ...config import DEFAULT_CONFIG

class PIIDetector:    
    def __init__(self, config=None):
        self.config = config if config else DEFAULT_CONFIG
        self.text_processor = TextProcessor()
        
        self.patterns = {
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'phone': r'\b(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b',
            'ssn': r'\b\d{3}[-.]?\d{2}[-.]?\d{4}\b',
            'credit_card': r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
            'ip_address': r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b',
        }
        
        self.confidence_scores = {
            'email': 0.9,
            'phone': 0.8, 
            'ssn': 0.95,
            'credit_card': 0.85,
            'ip_address': 0.8,
        }
    
    def detect(self, text: str) -> List[PIIMatch]:
        if not text or len(text.strip()) == 0:
            return []
        
        cleaned_text = self.text_processor.clean_text(text)
        
        matches = []
        
        for pii_type, pattern in self.patterns.items():
            if not self.config.get(f'pii_types.{pii_type}.enabled', True):
                continue
                
            regex_matches = re.finditer(pattern, cleaned_text, re.IGNORECASE)
            
            for match in regex_matches:
                if self._is_valid_match(pii_type, match.group()):
                    confidence = self.confidence_scores.get(pii_type, 0.5)
                    
                    context = self.text_processor.extract_context(
                        cleaned_text, 
                        match.start(), 
                        match.end(),
                        window=self.config.get('detection.context_window', 50)
                    )
                    
                    pii_match = PIIMatch(
                        pii_type=pii_type,
                        value=match.group(),
                        start=match.start(),
                        end=match.end(),
                        confidence=confidence,
                        context=context,
                        detector_name="regex"
                    )
                    
                    matches.append(pii_match)
        
        filtered_matches = merge_overlapping_matches(matches)
        
        threshold = self.config.get('detection.confidence_threshold', 0.7)
        final_matches = [m for m in filtered_matches if m.confidence >= threshold]
        
        return final_matches
    
    def _is_valid_match(self, pii_type: str, value: str) -> bool:
        clean_value = value.strip()
        
        if pii_type == 'email':
            return '@' in clean_value and '.' in clean_value.split('@')[-1]
        
        elif pii_type == 'phone':
            digits = re.sub(r'[^\d]', '', clean_value)
            return 10 <= len(digits) <= 11
        
        elif pii_type == 'ssn':
            digits = re.sub(r'[^\d]', '', clean_value)
            return len(digits) == 9 and digits != '000000000'
        
        elif pii_type == 'credit_card':
            digits = re.sub(r'[^\d]', '', clean_value)
            return 13 <= len(digits) <= 16
        
        elif pii_type == 'ip_address':
            parts = clean_value.split('.')
            if len(parts) != 4:
                return False
            try:
                return all(0 <= int(part) <= 255 for part in parts)
            except ValueError:
                return False
        
        return True
    
    def detect_batch(self, texts: List[str]) -> List[List[PIIMatch]]:
        results = []
        for text in texts:
            matches = self.detect(text)
            results.append(matches)
        return results
    
    def add_pattern(self, pii_type: str, pattern: str, confidence: float = 0.5):
        self.patterns[pii_type] = pattern
        self.confidence_scores[pii_type] = confidence
    
    def get_stats(self, matches: List[PIIMatch]) -> Dict[str, Any]:
        if not matches:
            return {'total': 0, 'by_type': {}}
        
        stats = {
            'total': len(matches),
            'by_type': {},
            'avg_confidence': sum(m.confidence for m in matches) / len(matches)
        }
        
        for match in matches:
            if match.pii_type not in stats['by_type']:
                stats['by_type'][match.pii_type] = 0
            stats['by_type'][match.pii_type] += 1
        
        return stats