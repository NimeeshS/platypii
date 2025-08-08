import re
from typing import Dict, Any
from ...utils import DEFAULT_CONFIG

class Preprocessor:    
    def __init__(self, config=None):
        self.config = config if config else DEFAULT_CONFIG
        
        self.options = {
            'normalize_whitespace': True,
            'remove_extra_spaces': True,
            'fix_line_breaks': True,
            'normalize_quotes': False,
            'remove_weird_chars': True,
            'lowercase_for_detection': False
        }
        
        if self.config:
            self.options.update(self.config.get('preprocessing', {}))
    
    def process(self, text: str) -> Dict[str, Any]:
        if not text:
            return {
                'original': '',
                'processed': '',
                'changes_made': [],
                'length_change': 0
            }
        
        original_text = text
        processed_text = text
        changes_made = []
        
        if self.options.get('normalize_whitespace', True):
            new_text = self._normalize_whitespace(processed_text)
            if new_text != processed_text:
                changes_made.append('normalized_whitespace')
                processed_text = new_text
        
        if self.options.get('remove_extra_spaces', True):
            new_text = self._remove_extra_spaces(processed_text)
            if new_text != processed_text:
                changes_made.append('removed_extra_spaces')
                processed_text = new_text
        
        if self.options.get('fix_line_breaks', True):
            new_text = self._fix_line_breaks(processed_text)
            if new_text != processed_text:
                changes_made.append('fixed_line_breaks')
                processed_text = new_text
        
        if self.options.get('normalize_quotes', False):
            new_text = self._normalize_quotes(processed_text)
            if new_text != processed_text:
                changes_made.append('normalized_quotes')
                processed_text = new_text
        
        if self.options.get('remove_weird_chars', True):
            new_text = self._remove_weird_chars(processed_text)
            if new_text != processed_text:
                changes_made.append('removed_weird_chars')
                processed_text = new_text
        
        return {
            'original': original_text,
            'processed': processed_text,
            'changes_made': changes_made,
            'length_change': len(processed_text) - len(original_text)
        }
    
    def _normalize_whitespace(self, text: str) -> str:
        return re.sub(r'\s', ' ', text)
    
    def _remove_extra_spaces(self, text: str) -> str:
        return re.sub(r' +', ' ', text).strip()
    
    def _fix_line_breaks(self, text: str) -> str:
        text = re.sub(r'(?<!\n)\n(?!\n)', ' ', text)
        text = re.sub(r' +', ' ', text)
        
        return text
    
    def _normalize_quotes(self, text: str) -> str:
        replacements = {
            '"': '"',
            '"': '"',
            ''': "'",
            ''': "'",
        }
        
        for smart_quote, regular_quote in replacements.items():
            text = text.replace(smart_quote, regular_quote)
        
        return text
    
    def _remove_weird_chars(self, text: str) -> str:
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
        
        replacements = {
            '\ufeff': '',  # BOM
            '\u00a0': ' ',  # Non-breaking space
            '\u2013': '-',  # En dash
            '\u2014': '--', # Em dash
            '\u2026': '...' # Ellipsis
        }
        
        for weird_char, replacement in replacements.items():
            text = text.replace(weird_char, replacement)
        
        return text
    
    def set_option(self, option_name: str, value: bool):
        if option_name in self.options:
            self.options[option_name] = value
    
    def get_options(self) -> Dict[str, bool]:
        return self.options.copy()
    
    def quick_clean(self, text: str) -> str:
        result = self.process(text)
        return result['processed']