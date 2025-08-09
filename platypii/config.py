import yaml
from typing import Dict, Any, Optional
from pathlib import Path

class Config:
    """Configuration manager for PlatyPII."""
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize configuration.
        
        Args:
            config_file (str, optional): Path to custom config file
        """
        self.config = self._load_default_config()
        
        if config_file:
            self.load_config(config_file)
    
    def _load_default_config(self) -> Dict[str, Any]:
        """Load default configuration settings."""
        return {
            # Detection settings
            "detection": {
                "enabled_detectors": [
                    "regex",
                    "nlp"
                ],
                "confidence_threshold": 0.4,
                "case_sensitive": False,
                "context_window": 50,  # Characters around detected PII
            },
            
            # PII types to detect
            "pii_types": {
                "email": {"enabled": True, "confidence": 0.9},
                "phone": {"enabled": True, "confidence": 0.8},
                "ssn": {"enabled": True, "confidence": 0.95},
                "credit_card": {"enabled": True, "confidence": 0.9},
                "ip_address": {"enabled": True, "confidence": 0.8},
                "name": {"enabled": True, "confidence": 0.7},
                "address": {"enabled": True, "confidence": 0.6},
                "date": {"enabled": True, "confidence": 0.8},
                "passport": {"enabled": False, "confidence": 0.9},
                "license_plate": {"enabled": False, "confidence": 0.8},
            },
            
            # Masking/anonymization settings
            "anonymization": {
                "default_strategy": "mask",  # mask, redact, replace, hash
                "mask_character": "*",
                "preserve_length": True,
                "preserve_format": False,  # Keep structure like XXX-XX-XXXX for SSN
                "replacement_patterns": {
                    "email": "[EMAIL]",
                    "phone": "[PHONE]", 
                    "ssn": "[SSN]",
                    "credit_card": "[CREDIT_CARD]",
                    "ip_address": "[IP_ADDRESS]",
                    "name": "[NAME]",
                    "address": "[ADDRESS]",
                    "date": "[DATE]",
                    "passport": "[PASSPORT]",
                    "license_plate": "[LICENSE_PLATE]"
                }
            },
            
            # Output and reporting
            "output": {
                "format": "json",  # json, csv, xml, text
                "include_confidence": True,
                "include_context": True,
                "include_position": True,
                "sort_by": "position",  # position, confidence, pii_type
            },
            
            # Regional compliance settings
            "compliance": {
                "region": "US",  # US, EU, CA, etc.
                "gdpr_mode": False,
                "ccpa_mode": False,
                "strict_mode": False,  # More conservative detection
            },
            
            # Performance settings
            "performance": {
                "batch_size": 1000,
                "max_text_length": 1000000,  # 1MB limit
                "timeout_seconds": 30,
                "use_cache": True,
                "cache_size": 1000,
            },
            
            # Logging
            "logging": {
                "level": "INFO",
                "log_detections": True,
                "log_file": None,  # If None, logs to console
            }
        }
    
    def load_config(self, config_file: str) -> None:
        """
        Load configuration from YAML file.
        
        Args:
            config_file (str): Path to configuration file
        """
        config_path = Path(config_file)
        
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_file}")
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                custom_config = yaml.safe_load(f)
            
            # Deep merge custom config with defaults
            self.config = self._deep_merge(self.config, custom_config)
            
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in config file: {e}")
        except Exception as e:
            raise ValueError(f"Error loading config file: {e}")
    
    def _deep_merge(self, default: Dict, custom: Dict) -> Dict:
        """
        Deep merge two dictionaries.
        
        Args:
            default (dict): Default configuration
            custom (dict): Custom configuration to merge
            
        Returns:
            dict: Merged configuration
        """
        result = default.copy()
        
        for key, value in custom.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation.
        
        Args:
            key (str): Configuration key (e.g., 'detection.confidence_threshold')
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        keys = key.split('.')
        value = self.config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any) -> None:
        """
        Set configuration value using dot notation.
        
        Args:
            key (str): Configuration key (e.g., 'detection.confidence_threshold')  
            value: Value to set
        """
        keys = key.split('.')
        config = self.config
        
        # Navigate to the parent of the final key
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # Set the final value
        config[keys[-1]] = value
    
    def save(self, file_path: str) -> None:
        """
        Save current configuration to YAML file.
        
        Args:
            file_path (str): Path to save configuration
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                yaml.dump(self.config, f, default_flow_style=False, indent=2)
        except Exception as e:
            raise ValueError(f"Error saving config file: {e}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Return configuration as dictionary."""
        return self.config.copy()

# Global default configuration instance
DEFAULT_CONFIG = Config()