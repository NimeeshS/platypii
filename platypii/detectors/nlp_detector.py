import re
from typing import List, Optional
import spacy
from platypii.utils import PIIMatch
from platypii.config import DEFAULT_CONFIG

class NLPDetector:    
    def __init__(self, config=None, model_name="en_core_web_sm"):
        self.config = config if config else DEFAULT_CONFIG
        self.model_name = model_name
        self.nlp = None
        try:
            self.nlp = spacy.load(model_name)
            print(f"Loaded spaCy model: {model_name}")
        except OSError:
            print(f"spaCy model '{model_name}' not found. Download it with:")
            print(f"python -m spacy download {model_name}")
            self.nlp = None
        
        self.pii_entity_map = {
            'PERSON': 'name',
            'ORG': 'name',
            'GPE': 'address',
            'DATE': 'date',
        }
        
        self.context_patterns = {
            'email_context': r'(?:email|e-mail|contact)[:.\s]*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
            'phone_context': r'(?:phone|call|tel|mobile)[:.\s]*([0-9\-\.\s\(\)]{10,})',
            'ssn_context': r'(?:ssn|social security|social security number)[:.\s]*(\d{3}[-.]?\d{2}[-.]?\d{4})',
            'date_context': r'(?:day|date|time|month|week)[:.\s]*([0-9]{1,2}[-/][0-9]{1,2}[-/][0-9]{4}|[A-Za-z]+ [0-9]{1,2},? [0-9]{4})'
        }
    
    def detect(self, text: str) -> List[PIIMatch]:
        if not text:
            return []
        
        matches = []
        
        if self.nlp:
            spacy_matches = self._detect_with_spacy(text)
            matches.extend(spacy_matches)
        
        return matches
    
    def _detect_with_spacy(self, text: str) -> List[PIIMatch]:
        matches = []
        
        doc = self.nlp(text)
        
        for ent in doc.ents:
            pii_type = self.pii_entity_map.get(ent.label_)
            
            if pii_type:
                confidence = self._calculate_confidence(ent, pii_type)
                
                if self._validate_entity(ent, pii_type):
                    match = PIIMatch(
                        pii_type=pii_type,
                        value=ent.text,
                        start=ent.start_char,
                        end=ent.end_char,
                        confidence=confidence,
                        detector_name="spacy_nlp"
                    )
                    matches.append(match)
        
        linguistic_matches = self._detect_linguistic_patterns(doc)
        matches.extend(linguistic_matches)
        
        return matches
    
    def _detect_linguistic_patterns(self, doc) -> List[PIIMatch]:
        matches = []
        
        for token in doc:
            if (token.pos_ == "PROPN" and len(token.text) > 1 and token.ent_type_ == ""):
                
                name_sequence = self._extract_name_sequence(token, doc)
                if name_sequence and len(name_sequence.split()) >= 2:
                    
                    start_char = token.idx if len(name_sequence.split()) == 1 else None
                    if start_char is None:
                        text_span = str(doc)
                        start_char = text_span.find(name_sequence)
                    
                    if start_char != -1:
                        match = PIIMatch(
                            pii_type='name',
                            value=name_sequence,
                            start=start_char,
                            end=start_char + len(name_sequence),
                            confidence=0.6,
                            detector_name="spacy_propn"
                        )
                        matches.append(match)
        
        address_matches = self._detect_addresses_linguistic(doc)
        matches.extend(address_matches)
        
        return matches
    
    def _extract_name_sequence(self, token, doc) -> Optional[str]:
        name_tokens = [token.text]
        
        i = token.i + 1
        while i < len(doc) and doc[i].pos_ == "PROPN":
            name_tokens.append(doc[i].text)
            i += 1
        
        i = token.i - 1
        while i >= 0 and doc[i].pos_ == "PROPN":
            name_tokens.insert(0, doc[i].text)
            i -= 1
        
        name_sequence = " ".join(name_tokens)
        
        if 4 <= len(name_sequence) <= 50:
            return name_sequence
        
        return None
    
    def _detect_addresses_linguistic(self, doc) -> List[PIIMatch]:
        matches = []
        
        for i, token in enumerate(doc):
            if (token.like_num and 
                i + 1 < len(doc) and 
                doc[i + 1].pos_ in ["NOUN", "PROPN"]):
                
                address_tokens = [token.text]
                j = i + 1
                
                while j < len(doc):
                    next_token = doc[j]
                    if (next_token.pos_ in ["NOUN", "PROPN", "ADJ"] or
                        next_token.text.lower() in ["street", "st", "avenue", "ave", "road", "rd", "drive", "dr", "lane", "ln"]):
                        address_tokens.append(next_token.text)
                        j += 1
                    else:
                        break
                
                address_text = " ".join(address_tokens)
                
                if (len(address_text) > 10 and
                    any(street_word in address_text.lower() for street_word in 
                        ["street", "st", "avenue", "ave", "road", "rd", "drive", "dr", "lane", "ln"])):
                    
                    start_char = token.idx
                    match = PIIMatch(
                        pii_type='address',
                        value=address_text,
                        start=start_char,
                        end=start_char + len(address_text),
                        confidence=0.7,
                        detector_name="spacy_linguistic"
                    )
                    matches.append(match)
        
        return matches
    
    def _calculate_confidence(self, ent, pii_type: str) -> float:
        base_confidence = {
            'name': 0.8,
            'organization': 0.6,
            'location': 0.7,
            'date': 0.8,
        }.get(pii_type, 0.5)
        
        length_factor = min(len(ent.text) / 10, 1.0)
        
        capitalization_factor = 1.0
        if pii_type == 'name' and ent.text.istitle():
            capitalization_factor = 1.1
        
        final_confidence = base_confidence * length_factor * capitalization_factor
        return min(final_confidence, 0.95)
    
    def _validate_entity(self, ent, pii_type: str) -> bool:
        text = ent.text.strip()
        
        if pii_type == 'name':
            return (2 <= len(text) <= 50 and len(text.split()) <= 4)
        
        elif pii_type == 'date':
            return len(text) >= 4 and any(char.isdigit() for char in text)
        
        elif pii_type == 'number':
            digits_only = ''.join(c for c in text if c.isdigit())
            return len(digits_only) >= 4
        
        return True
    
    def add_custom_entity_mapping(self, spacy_label: str, pii_type: str):
        self.pii_entity_map[spacy_label] = pii_type
    
    def get_available_models(self) -> List[str]:        
        try:
            import subprocess
            result = subprocess.run(['python', '-m', 'spacy', 'info'], 
                                  capture_output=True, text=True)
            return result.stdout.splitlines()
        except:
            return ['en_core_web_sm']
    
    def switch_model(self, model_name: str) -> bool:        
        try:
            self.nlp = spacy.load(model_name)
            self.model_name = model_name
            print(f"Switched to spaCy model: {model_name}")
            return True
        except OSError:
            print(f"Could not load model: {model_name}")
            return False