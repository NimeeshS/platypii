import re
from typing import List, Dict, Any, Tuple
from platypii.utils import PIIMatch
from platypii.config import DEFAULT_CONFIG

class Postprocessor:
    """
    Handles post-processing after anonymization
    Cleans up formatting issues and validates results
    """
    
    def __init__(self, config=None):
        self.config = config if config else DEFAULT_CONFIG
        
        self.options = {
            'fix_spacing': True,
            'normalize_replacements': True,
            'validate_anonymization': True,
            'clean_formatting': True,
            'remove_empty_lines': False 
        }
        
        if self.config:
            self.options.update(self.config.get('postprocessing', {}))
    
    def process(self, text: str, original_matches: List[PIIMatch] = None) -> Dict[str, Any]:
        if not text:
            return {
                'processed_text': '',
                'issues_found': [],
                'fixes_applied': [],
                'validation_passed': True
            }
        
        processed_text = text
        fixes_applied = []
        issues_found = []
        
        if self.options.get('fix_spacing', True):
            new_text, fixed = self._fix_spacing_issues(processed_text)
            if fixed:
                fixes_applied.append('fixed_spacing')
                processed_text = new_text
        
        if self.options.get('normalize_replacements', True):
            new_text, fixed = self._normalize_replacements(processed_text)
            if fixed:
                fixes_applied.append('normalized_replacements')
                processed_text = new_text
        
        if self.options.get('clean_formatting', True):
            new_text, fixed = self._clean_formatting(processed_text)
            if fixed:
                fixes_applied.append('cleaned_formatting')
                processed_text = new_text
        
        if self.options.get('remove_empty_lines', False):
            new_text, fixed = self._remove_empty_lines(processed_text)
            if fixed:
                fixes_applied.append('removed_empty_lines')
                processed_text = new_text
        
        validation_passed = True
        if self.options.get('validate_anonymization', True):
            validation_results = self._validate_anonymization(processed_text, original_matches)
            if validation_results['issues']:
                issues_found.extend(validation_results['issues'])
                validation_passed = False
        
        return {
            'processed_text': processed_text,
            'issues_found': issues_found,
            'fixes_applied': fixes_applied,
            'validation_passed': validation_passed
        }
    
    def _fix_spacing_issues(self, text: str) -> Tuple[str, bool]:
        original_text = text
        
        text = re.sub(r' +', ' ', text)
        text = re.sub(r' +([,.!?;:])', r'\1', text)
        text = re.sub(r'([,.!?;:])([A-Za-z])', r'\1 \2', text)
        text = re.sub(r' +\)', ')', text)
        text = re.sub(r'\( +', '(', text)
        text = re.sub(r' +\]', ']', text)
        text = re.sub(r'\[ +', '[', text)
        
        text = text.strip()
        
        return text, text != original_text
    
    def _normalize_replacements(self, text: str) -> Tuple[str, bool]:
        original_text = text
        
        replacements = {
            r'\[EMAIL\]\s*\[EMAIL\]': '[EMAIL]',
            r'\[PHONE\]\s*\[PHONE\]': '[PHONE]',
            r'\[NAME\]\s*\[NAME\]': '[NAME]',
            
            r'\[\s*EMAIL\s*\]': '[EMAIL]',
            r'\[\s*PHONE\s*\]': '[PHONE]',
            r'\[\s*NAME\s*\]': '[NAME]',
            r'\[\s*REDACTED\s*\]': '[REDACTED]',
            
            r'\[HASH:\s*([a-f0-9]+)\s*\]': r'[HASH:\1]',
        }
        
        for pattern, replacement in replacements.items():
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        
        return text, text != original_text
    
    def _clean_formatting(self, text: str) -> Tuple[str, bool]:
        original_text = text
        
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
        text = re.sub(r'"\s*\[([A-Z]+)\]\s*"', r'[\1]', text)
        
        return text, text != original_text
    
    def _remove_empty_lines(self, text: str) -> Tuple[str, bool]:
        original_text = text
        lines = text.split('\n')
        non_empty_lines = [line for line in lines if line.strip()]
        text = '\n'.join(non_empty_lines)
        
        return text, text != original_text
    
    def _validate_anonymization(self, text: str, original_matches: List[PIIMatch] = None) -> Dict[str, Any]:
        issues = []
        
        validation_patterns = {
            'potential_email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'potential_phone': r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b',
            'potential_ssn': r'\b\d{3}[-.]?\d{2}[-.]?\d{4}\b',
            'potential_credit_card': r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'
        }
        
        for issue_type, pattern in validation_patterns.items():
            matches = re.findall(pattern, text)
            if matches:
                real_matches = []
                for match in matches:
                    if not self._is_safe_replacement(match):
                        real_matches.append(match)
                
                if real_matches:
                    issues.append({
                        'type': issue_type,
                        'count': len(real_matches),
                        'examples': real_matches[:3]
                    })
        
        incomplete_patterns = [
            r'\[EMAIL$',
            r'\[REDACTED$',
            r'EMAIL\]',
            r'REDACTED\]'
        ]
        
        for pattern in incomplete_patterns:
            if re.search(pattern, text):
                issues.append({
                    'type': 'incomplete_replacement',
                    'description': f'Found incomplete replacement matching: {pattern}'
                })
        
        return {
            'issues': issues,
            'total_issues': len(issues),
            'validation_passed': len(issues) == 0
        }
    
    def _is_safe_replacement(self, value: str) -> bool:
        safe_patterns = [
            r'123-456-7890',
            r'111-11-1111',
            r'\(123\) 456-7890',
            r'user@domain\.com',
            r'john\.smith',
            r'jane\.doe',
            r'123 Main Street',
        ]
        
        value_lower = value.lower()
        
        for pattern in safe_patterns:
            if re.search(pattern, value_lower):
                return True
        
        return False
    
    def quick_clean(self, text: str) -> str:
        result = self.process(text)
        return result['processed_text']
    
    def validate_only(self, text: str, original_matches: List[PIIMatch] = None) -> Dict[str, Any]:
        return self._validate_anonymization(text, original_matches)
    
    def set_option(self, option_name: str, value: bool):
        if option_name in self.options:
            self.options[option_name] = value
    
    def get_options(self) -> Dict[str, bool]:
        return self.options.copy()