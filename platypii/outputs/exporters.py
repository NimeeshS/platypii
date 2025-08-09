import os
from typing import List, Dict, Any
from pathlib import Path
from platypii.utils import PIIMatch
from platypii.config import DEFAULT_CONFIG
from .formatters import ReportFormatter

class DataExporter:    
    def __init__(self, config=None):
        self.config = config if config else DEFAULT_CONFIG
        self.formatter = ReportFormatter()
        
        
        self.export_settings = {
            'default_format': 'json',
            'include_timestamp': True,
            'create_directories': True,
            'overwrite_existing': True
        }
    
    def export_to_file(self, matches: List[PIIMatch], file_path: str, format_type: str = None, stats: Dict[str, Any] = None) -> bool:
        try:
            if not format_type:
                format_type = self._detect_format_from_path(file_path)
            
            if self.export_settings['create_directories']:
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            if os.path.exists(file_path) and not self.export_settings['overwrite_existing']:
                print(f"File {file_path} already exists. Set overwrite_existing=True to overwrite.")
                return False
            
            report_content = self.formatter.format_report(matches, stats, format_type)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(report_content)
            
            print(f"Exported {len(matches)} matches to {file_path}")
            return True
            
        except Exception as e:
            print(f"Error exporting to file: {e}")
            return False
    
    def export_multiple_formats(self, matches: List[PIIMatch], base_path: str, formats: List[str] = None, stats: Dict[str, Any] = None) -> Dict[str, bool]:
        if not formats:
            formats = ['json', 'html', 'txt']
        
        results = {}
        base_name = os.path.splitext(base_path)[0]
        
        for fmt in formats:
            file_path = f"{base_name}.{fmt}"
            
            success = self.export_to_file(matches, file_path, fmt, stats)
            results[fmt] = success
        
        return results
    
    def _detect_format_from_path(self, file_path: str) -> str:
        extension = Path(file_path).suffix.lower()
        
        format_map = {
            '.json': 'json',
            '.html': 'html',
            '.htm': 'html',
            '.txt': 'txt',
        }
        
        return format_map.get(extension, self.export_settings['default_format'])
    
    def get_export_formats(self) -> List[str]:
        return ['json', 'html', 'text', 'xml']