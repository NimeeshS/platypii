import re
from typing import List, Dict, Any
from platypii.utils import PIIMatch, TextProcessor, merge_overlapping_matches
from platypii.config import DEFAULT_CONFIG
from platypii.detectors import NLPDetector, RegexDetector

class PIIDetector:    
    def __init__(self, config=None):
        self.config = config if config else DEFAULT_CONFIG
        self.text_processor = TextProcessor()
        self.regex_detector = RegexDetector(config)
        self.nlp_detector = NLPDetector(config)
    
    def detect(self, text: str) -> List[PIIMatch]:
        if not text or len(text.strip()) == 0:
            return []
        
        matches = []
        matches.extend(self.regex_detector.detect(text))
        matches.extend(self.nlp_detector.detect(text))
        
        filtered_matches = merge_overlapping_matches(matches)
        
        threshold = self.config.get('detection.confidence_threshold', 0.6)
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