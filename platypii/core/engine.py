from typing import List, Dict, Any
from .detector import PIIDetector
from ..processors.anonymizer import Anonymizer
from ..outputs.formatters import ReportFormatter
from ...utils import PIIMatch
from ...config import DEFAULT_CONFIG
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PIIEngine:
    
    def __init__(self, config=None):
        self.config = config if config else DEFAULT_CONFIG
        self.detector = PIIDetector(config=self.config)
        self.anonymizer = None
        self.formatter = None
        self.last_results = None
        
        logger.info("PII Engine initialized")
    
    def process_text(self, text: str, anonymize: bool = False, generate_report: bool = True) -> Dict[str, Any]:
        """
        Main processing method
        
        Args:
            text: The text to process
            anonymize: Whether to anonymize the PII
            generate_report: Whether to create a report
            
        Returns:
            Dictionary with all the results
        """
        if not text:
            logger.warning("Empty text provided")
            return self._empty_result()
        
        logger.info(f"Processing text of length {len(text)}")
        
        matches = self.detector.detect(text)
        logger.info(f"Found {len(matches)} PII matches")
        
        result = {
            'original_text': text,
            'matches': matches,
            'anonymized_text': None,
            'report': None,
            'stats': self.detector.get_stats(matches)
        }
        
        if anonymize and matches:
            if not self.anonymizer:
                self.anonymizer = Anonymizer(config=self.config)
            
            anonymized = self.anonymizer.anonymize_text(text, matches)
            result['anonymized_text'] = anonymized
            logger.info("Text anonymized")
        
        if generate_report:
            if not self.formatter:
                self.formatter = ReportFormatter(config=self.config)
            
            report = self.formatter.format_report(matches, result['stats'])
            result['report'] = report
            logger.info("Report generated")
        
        self.last_results = result
        
        return result
    
    def process_batch(self, texts: List[str], anonymize: bool = False) -> List[Dict[str, Any]]:
        results = []
        
        logger.info(f"Processing batch of {len(texts)} texts")
        
        for i, text in enumerate(texts):
            logger.info(f"Processing text {i+1}/{len(texts)}")
            result = self.process_text(text, anonymize=anonymize, generate_report=False)
            results.append(result)
        
        return results
    
    def detect_only(self, text: str) -> List[PIIMatch]:
        return self.detector.detect(text)
    
    def anonymize_only(self, text: str) -> str:
        matches = self.detector.detect(text)
        if not matches:
            return text
        
        if not self.anonymizer:
            self.anonymizer = Anonymizer(config=self.config)
        
        return self.anonymizer.anonymize_text(text, matches)
    
    def _empty_result(self) -> Dict[str, Any]:
        return {
            'original_text': '',
            'matches': [],
            'anonymized_text': None,
            'report': None,
            'stats': {'total': 0, 'by_type': {}}
        }
    
    def get_supported_pii_types(self) -> List[str]:
        return list(self.detector.patterns.keys())
    
    def update_config(self, new_config: Dict[str, Any]):
        for key, value in new_config.items():
            self.config.set(key, value)
        
        self.detector = PIIDetector(config=self.config)
        self.anonymizer = None
        self.formatter = None
        
        logger.info("Configuration updated")
    
    def add_custom_pattern(self, pii_type: str, pattern: str, confidence: float = 0.5):
        self.detector.add_pattern(pii_type, pattern, confidence)
        logger.info(f"Added custom pattern for {pii_type}")
    
    def export_results(self, format_type: str = 'json') -> str:
        if not self.last_results:
            logger.warning("No results to export - run process_text first")
            return ""
        
        if not self.formatter:
            self.formatter = ReportFormatter(config=self.config)
        
        if format_type.lower() == 'json':
            import json
            exportable = self.last_results.copy()
            exportable['matches'] = [match.to_dict() for match in exportable['matches']]
            return json.dumps(exportable, indent=2)
        
        elif format_type.lower() == 'csv':
            if not self.last_results['matches']:
                return "No PII found"
            
            lines = ["pii_type,value,start,end,confidence"]
            for match in self.last_results['matches']:
                lines.append(f"{match.pii_type},{match.value},{match.start},{match.end},{match.confidence}")
            
            return "\n".join(lines)
        
        else:
            logger.warning(f"Unsupported export format: {format_type}")
            return ""