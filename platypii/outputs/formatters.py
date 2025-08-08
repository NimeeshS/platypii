import json
from typing import List, Dict, Any
from datetime import datetime
from ...utils import PIIMatch

class ReportFormatter:
    def __init__(self, config=None):
        self.config = config
        
        self.report_settings = {
            'include_confidence': True,
            'include_context': True,
            'include_position': True,
            'sort_by': 'position',
            'show_stats': True,
            'highlight_high_confidence': True
        }
        
        if config:
            for key, value in config.get('output', {}).items():
                if key in self.report_settings:
                    self.report_settings[key] = value
    
    def format_report(self, matches: List[PIIMatch], stats: Dict[str, Any] = None, format_type: str = 'json') -> str:
        if not matches and not stats:
            return self._empty_report(format_type)
        
        sorted_matches = self._sort_matches(matches)
        
        format_methods = {
            'json': self._format_json,
            'html': self._format_html,
            'text': self._format_text,
            'summary': self._format_summary
        }
        
        formatter = format_methods.get(format_type.lower(), self._format_json)
        return formatter(sorted_matches, stats)
    
    def _sort_matches(self, matches: List[PIIMatch]) -> List[PIIMatch]:
        sort_key = self.report_settings['sort_by']
        
        if sort_key == 'confidence':
            return sorted(matches, key=lambda m: m.confidence, reverse=True)
        elif sort_key == 'pii_type':
            return sorted(matches, key=lambda m: m.pii_type)
        else:
            return sorted(matches, key=lambda m: m.start)
    
    def _format_json(self, matches: List[PIIMatch], stats: Dict[str, Any] = None) -> str:
        report = {
            'timestamp': datetime.now().isoformat(),
            'total_matches': len(matches),
            'matches': [],
            'statistics': stats or {}
        }
        
        for match in matches:
            match_dict = {
                'pii_type': match.pii_type,
                'value': match.value,
                'detector': match.detector_name
            }
            
            if self.report_settings['include_confidence']:
                match_dict['confidence'] = match.confidence
            
            if self.report_settings['include_position']:
                match_dict['start'] = match.start
                match_dict['end'] = match.end
                match_dict['length'] = match.end - match.start
            
            if self.report_settings['include_context'] and match.context:
                match_dict['context'] = match.context
            
            report['matches'].append(match_dict)
        
        return json.dumps(report, indent=2)
    
    def _format_html(self, matches: List[PIIMatch], stats: Dict[str, Any] = None) -> str:
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>PII Detection Report</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .header { background: #f0f0f0; padding: 10px; border-radius: 5px; }
                .summary { margin: 20px 0; }
                .match { border: 1px solid #ddd; margin: 10px 0; padding: 10px; border-radius: 3px; }
                .high-confidence { border-left: 5px solid #ff6b6b; }
                .medium-confidence { border-left: 5px solid #ffd93d; }
                .low-confidence { border-left: 5px solid #6bcf7f; }
                .pii-type { font-weight: bold; color: #333; }
                .confidence { color: #666; font-size: 0.9em; }
                .context { background: #f9f9f9; padding: 5px; margin-top: 5px; font-family: monospace; }
            </style>
        </head>
        <body>
        """
        
        html += f"""
        <div class="header">
            <h1>PII Detection Report</h1>
            <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p>Total matches found: {len(matches)}</p>
        </div>
        """
        
        if stats and self.report_settings['show_stats']:
            html += "<div class='summary'><h2>Summary</h2><ul>"
            for pii_type, count in stats.get('by_type', {}).items():
                html += f"<li>{pii_type.title()}: {count}</li>"
            html += "</ul></div>"
        
        html += "<h2>Detected PII</h2>"
        
        for match in matches:
            conf_class = 'low-confidence'
            if match.confidence >= 0.8:
                conf_class = 'high-confidence'
            elif match.confidence >= 0.6:
                conf_class = 'medium-confidence'
            
            html += f"""
            <div class="match {conf_class}">
                <div class="pii-type">{match.pii_type.upper()}: {match.value}</div>
            """
            
            if self.report_settings['include_confidence']:
                html += f"<div class='confidence'>Confidence: {match.confidence:.2%}</div>"
            
            if self.report_settings['include_position']:
                html += f"<div class='confidence'>Position: {match.start}-{match.end}</div>"
            
            html += f"<div class='confidence'>Detector: {match.detector_name}</div>"
            
            if self.report_settings['include_context'] and match.context:
                html += f"<div class='context'>{match.context}</div>"
            
            html += "</div>"
        
        html += "</body></html>"
        return html
    
    def _format_text(self, matches: List[PIIMatch], stats: Dict[str, Any] = None) -> str:
        lines = []
        lines.append("PII DETECTION REPORT")
        lines.append("=" * 50)
        lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"Total matches: {len(matches)}")
        lines.append("")
        
        if stats and self.report_settings['show_stats']:
            lines.append("SUMMARY:")
            lines.append("-" * 20)
            for pii_type, count in stats.get('by_type', {}).items():
                lines.append(f"  {pii_type.title()}: {count}")
            lines.append("")
        
        lines.append("DETECTED PII:")
        lines.append("-" * 20)
        
        for i, match in enumerate(matches, 1):
            lines.append(f"{i}. {match.pii_type.upper()}: {match.value}")
            
            if self.report_settings['include_confidence']:
                lines.append(f"   Confidence: {match.confidence:.2%}")
            
            if self.report_settings['include_position']:
                lines.append(f"   Position: {match.start}-{match.end}")
            
            lines.append(f"   Detector: {match.detector_name}")
            
            if self.report_settings['include_context'] and match.context:
                lines.append(f"   Context: {match.context}")
            
            lines.append("")
        
        return "\n".join(lines)
    
    def _format_summary(self, matches: List[PIIMatch], stats: Dict[str, Any] = None) -> str:
        if not matches:
            return "No PII detected."
        
        summary = f"Found {len(matches)} PII items:\n"
        
        by_type = {}
        for match in matches:
            if match.pii_type not in by_type:
                by_type[match.pii_type] = []
            by_type[match.pii_type].append(match)
        
        for pii_type, type_matches in by_type.items():
            high_conf = [m for m in type_matches if m.confidence >= 0.8]
            summary += f"  • {pii_type.title()}: {len(type_matches)} ({len(high_conf)} high confidence)\n"
        
        return summary
    
    def _empty_report(self, format_type: str) -> str:
        if format_type == 'json':
            return json.dumps({
                'timestamp': datetime.now().isoformat(),
                'total_matches': 0,
                'matches': [],
                'statistics': {}
            }, indent=2)
        elif format_type == 'html':
            return "<html><body><h1>No PII detected</h1></body></html>"
        else:
            return "No PII detected."
    
    def update_settings(self, **kwargs):
        for key, value in kwargs.items():
            if key in self.report_settings:
                self.report_settings[key] = value
    
    def get_settings(self) -> Dict[str, Any]:
        return self.report_settings.copy()