import hashlib
from typing import List, Dict, Any
from platypii.utils import PIIMatch
from platypii.config import DEFAULT_CONFIG

class Anonymizer:
    def __init__(self, config=None):
        self.config = config if config else DEFAULT_CONFIG
        self.default_method = self.config.get('anonymization.default_strategy', 'mask')
        self.mask_char = self.config.get('anonymization.mask_character', '*')
        self.preserve_length = self.config.get('anonymization.preserve_length', True)
        self.preserve_format = self.config.get('anonymization.preserve_format', False)
        
        self.replacement_patterns = self.config.get('anonymization.replacement_patterns', {
            'email': '[EMAIL]',
            'phone': '[PHONE]',
            'ssn': '[SSN]',
            'credit_card': '[CREDIT_CARD]',
            'name': '[NAME]',
            'address': '[ADDRESS]',
            'date': '[DATE]'
        })

        self.anonymization_methods = ['mask', 'redact', 'hash', 'replace', 'synthetic']
        
        self.hash_salt = "platypii_salt_2024"
    
    def anonymize_text(self, text: str, matches: List[PIIMatch], anonymization_method: str = None) -> str:
        if not text or not matches:
            return text
        
        if not anonymization_method or anonymization_method not in self.anonymization_methods:
            anonymization_method = self.default_method
        
        sorted_matches = sorted(matches, key=lambda m: m.start, reverse=True)
        
        anonymized_text = text
        
        for match in sorted_matches:
            anonymized_value = self._anonymize_value(match, anonymization_method)
            if anonymized_value:
                anonymized_text = (anonymized_text[:match.start] + anonymized_value + anonymized_text[match.end:])

        return anonymized_text
    
    def _anonymize_value(self, match: PIIMatch, method: str) -> str:
        original_value = match.value
        pii_type = match.pii_type
        
        if method == 'mask':
            return self._mask_value(original_value, pii_type)
        elif method == 'redact':
            return self._redact_value()
        elif method == 'hash':
            return self._hash_value(original_value, pii_type)
        elif method == 'replace':
            return self._replace_value(original_value, pii_type)
        elif method == 'synthetic':
            return self._generate_synthetic(original_value, pii_type)
        else:
            return self._mask_value(original_value, pii_type)
    
    def _mask_value(self, value: str, pii_type: str) -> str:
        if self.preserve_format and pii_type in ['ssn', 'phone', 'credit_card']:
            return self._mask_with_format(value, pii_type)
        
        if self.preserve_length:
            masked = ''
            for char in value:
                if char.isspace():
                    masked += char
                elif char in '-()/@':
                    masked += char
                else:
                    masked += self.mask_char
            return masked
        else:
            return self.mask_char * 5
    
    def _mask_with_format(self, value: str, pii_type: str) -> str:
        if pii_type == 'ssn':
            if '-' in value:
                return 'XXX-XX-XXXX'
            else:
                return 'XXXXXXXXX'
        
        elif pii_type == 'phone':
            if '(' in value and ')' in value:
                return '(XXX) XXX-XXXX'
            elif '-' in value:
                parts = value.split('-')
                if len(parts) == 3:
                    return 'XXX-XXX-XXXX'
            return 'XXXXXXXXXX'
        
        elif pii_type == 'credit_card':
            if '-' in value or ' ' in value:
                return 'XXXX-XXXX-XXXX-XXXX'
            else:
                return 'XXXXXXXXXXXXXXXX'
        
        return self._mask_value(value, pii_type)
    
    def _redact_value(self) -> str:
        return '[REDACTED]'
    
    def _hash_value(self, value: str, pii_type: str) -> str:
        hash_input = (value + self.hash_salt).encode('utf-8')
        hash_object = hashlib.sha256(hash_input)
        hash_hex = hash_object.hexdigest()
        
        return f"[HASH:{hash_hex[:8]}]"
    
    def _replace_value(self, value: str, pii_type: str) -> str:
        return self.replacement_patterns.get(pii_type, value)
    
    def _generate_synthetic(self, value: str, pii_type: str) -> str:
        if pii_type == 'name':
            parts = value.split()
            if len(parts) == 2:
                return "John Smith"
        
        elif pii_type == 'email':
            return f"user@domain.com"
        
        elif pii_type == 'phone':
            if '(' in value:
                return "(123) 456-7890"
            else:
                return "123-456-7890"
        
        elif pii_type == 'ssn':
            if '-' in value:
                return "111-11-1111"
            else:
                return "111111111"
        
        elif pii_type == 'address':
            return "123 Main Street"
        
        elif pii_type == 'date':
            return '01/01/1970'
        
        else:
            return self._replace_value(value, pii_type)
    
    def anonymize_batch(self, texts: List[str], matches_list: List[List[PIIMatch]], method: str = None) -> List[str]:
        if len(texts) != len(matches_list):
            raise ValueError("texts and matches_list must be same length")
        
        results = []
        for text, matches in zip(texts, matches_list):
            anonymized = self.anonymize_text(text, matches, method)
            results.append(anonymized)
        
        return results
    
    def get_anonymization_summary(self, matches: List[PIIMatch]) -> Dict[str, Any]:
        summary = {
            'total_matches': len(matches),
            'by_type': {},
            'total_characters': 0
        }
        
        for match in matches:
            pii_type = match.pii_type
            
            if pii_type not in summary['by_type']:
                summary['by_type'][pii_type] = {
                    'count': 0,
                    'examples': [],
                    'total_length': 0
                }
            
            summary['by_type'][pii_type]['count'] += 1
            summary['by_type'][pii_type]['total_length'] += len(match.value)
            summary['total_characters'] += len(match.value)
            
            if len(summary['by_type'][pii_type]['examples']) < 3:
                summary['by_type'][pii_type]['examples'].append(match.value)
        
        return summary
    
    def set_replacement_pattern(self, pii_type: str, pattern: str):
        self.replacement_patterns[pii_type] = pattern
    
    def set_hash_salt(self, salt: str):
        self.hash_salt = salt
    
    def preview_anonymization(self, text: str, matches: List[PIIMatch], method: str = None) -> Dict[str, Any]:
        anonymized = self.anonymize_text(text, matches, method)
        
        return {
            'original': text,
            'anonymized': anonymized,
            'method_used': method or self.default_method,
            'changes_made': len(matches),
            'summary': self.get_anonymization_summary(matches)
        }