from typing import List, Dict, Any, Callable
from dataclasses import dataclass
import time
import logging
from platypii.config import DEFAULT_CONFIG

logger = logging.getLogger(__name__)

@dataclass
class PipelineStep:
    name: str
    function: Callable
    enabled: bool = True
    config: Dict[str, Any] = None

class PIIPipeline:
    def __init__(self, config=None):
        self.config = config if config else DEFAULT_CONFIG
        self.steps = []
        self.results = {}
        self.timing = {}
        self._setup_default_steps()
    
    def _setup_default_steps(self):
        self.steps = [
            PipelineStep("preprocess", self._preprocess_step),
            PipelineStep("detect", self._detect_step), 
            PipelineStep("validate", self._validate_step),
            PipelineStep("postprocess", self._postprocess_step)
        ]
    
    def add_step(self, name: str, function: Callable, enabled: bool = True):
        step = PipelineStep(name, function, enabled)
        self.steps.append(step)
        logger.info(f"Added step '{name}' to pipeline")
    
    def remove_step(self, name: str):
        self.steps = [step for step in self.steps if step.name != name]
        logger.info(f"Removed step '{name}' from pipeline")
    
    def enable_step(self, name: str):
        for step in self.steps:
            if step.name == name:
                step.enabled = True
                break
    
    def disable_step(self, name: str):
        for step in self.steps:
            if step.name == name:
                step.enabled = False
                break
    
    def process(self, text: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Run the text through the entire pipeline
        
        Args:
            text: Text to process
            context: Additional context/config for processing
            
        Returns:
            Final results after all steps
        """
        if not text:
            return {'error': 'No text provided'}
        
        processing_context = {
            'original_text': text,
            'current_text': text,
            'matches': [],
            'metadata': {},
            'step_results': {}
        }
        
        if context:
            processing_context.update(context)
        
        logger.info(f"Starting pipeline processing for text of length {len(text)}")
        
        for step in self.steps:
            if not step.enabled:
                logger.debug(f"Skipping disabled step: {step.name}")
                continue
            
            start_time = time.time()
            
            try:
                logger.debug(f"Running step: {step.name}")
                processing_context = step.function(processing_context)
                
                elapsed = time.time() - start_time
                self.timing[step.name] = elapsed
                
                logger.debug(f"Step {step.name} completed in {elapsed:.3f}s")
                
            except Exception as e:
                logger.error(f"Error in step {step.name}: {str(e)}")
                processing_context['error'] = f"Pipeline failed at step {step.name}: {str(e)}"
                break
        
        self.results = processing_context
        
        return processing_context
    
    def _preprocess_step(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Basic text preprocessing
        Not doing much here but could add text cleaning, normalization etc.
        """
        text = context['current_text']
        
        cleaned_text = ' '.join(text.split())
        
        context['current_text'] = cleaned_text
        context['metadata']['preprocessing'] = {
            'original_length': len(text),
            'cleaned_length': len(cleaned_text),
            'changes_made': text != cleaned_text
        }
        
        return context
    
    def _detect_step(self, context: Dict[str, Any]) -> Dict[str, Any]:
        from .detector import PIIDetector
        
        detector = PIIDetector(config=self.config)
        matches = detector.detect(context['current_text'])
        
        context['matches'] = matches
        context['metadata']['detection'] = {
            'matches_found': len(matches),
            'detector_used': 'PIIDetector'
        }
        
        return context
    
    def _validate_step(self, context: Dict[str, Any]) -> Dict[str, Any]:
        matches = context['matches']
        original_count = len(matches)
        
        confidence_threshold = 0.7
        if self.config:
            confidence_threshold = self.config.get('detection.confidence_threshold', 0.7)
        
        filtered_matches = [m for m in matches if m.confidence >= confidence_threshold]
        
        context['matches'] = filtered_matches
        context['metadata']['validation'] = {
            'original_matches': original_count,
            'filtered_matches': len(filtered_matches),
            'confidence_threshold': confidence_threshold
        }
        
        return context
    
    def _postprocess_step(self, context: Dict[str, Any]) -> Dict[str, Any]:
        matches = context['matches']
        
        sorted_matches = sorted(matches, key=lambda m: m.start)
        
        unique_matches = []
        seen = set()
        
        for match in sorted_matches:
            match_key = (match.pii_type, match.start, match.end, match.value)
            if match_key not in seen:
                unique_matches.append(match)
                seen.add(match_key)
        
        context['matches'] = unique_matches
        context['metadata']['postprocessing'] = {
            'sorted': True,
            'deduplicated': len(sorted_matches) != len(unique_matches),
            'final_count': len(unique_matches)
        }
        
        return context
    
    def get_step_names(self) -> List[str]:
        return [step.name for step in self.steps]
    
    def get_enabled_steps(self) -> List[str]:
        return [step.name for step in self.steps if step.enabled]
    
    def get_timing_info(self) -> Dict[str, float]:
        return self.timing.copy()
    
    def reset(self):
        self.results = {}
        self.timing = {}
        logger.info("Pipeline state reset")