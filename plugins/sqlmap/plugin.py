"""SQLmap plugin for SQL injection detection and exploitation."""
import os
import json
import subprocess
import tempfile
from typing import Dict, Any, List
from core.plugins.base import PluginBase


class SQLmapPlugin(PluginBase):
    """SQLmap plugin for automated SQL injection testing."""
    
    name = "sqlmap"
    version = "1.0.0"
    description = "Automated SQL injection detection and exploitation"
    capabilities = ["web_scan", "sql_injection", "database_exploitation"]
    
    def validate_config(self) -> None:
        """Validate plugin configuration."""
        if 'target' not in self.config:
            raise ValueError("Missing required config: 'target' (URL)")
        
        target = self.config['target']
        if not target.startswith(('http://', 'https://')):
            raise ValueError("Target must be a valid HTTP/HTTPS URL")
        
        # Validate mode
        mode = self.config.get('mode', 'detect')
        valid_modes = ['detect', 'exploit', 'dump']
        if mode not in valid_modes:
            raise ValueError(f"Invalid mode. Must be one of: {valid_modes}")
        
        # Validate level and risk
        level = self.config.get('level', 1)
        risk = self.config.get('risk', 1)
        
        if not (1 <= level <= 5):
            raise ValueError("Level must be between 1 and 5")
        if not (1 <= risk <= 3):
            raise ValueError("Risk must be between 1 and 3")
    
    def run(self) -> Dict[str, Any]:
        """Execute SQLmap scan."""
        target = self.config['target']
        mode = self.config.get('mode', 'detect')
        level = self.config.get('level', 1)
        risk = self.config.get('risk', 1)
        
        # Create temporary output directory
        output_dir = tempfile.mkdtemp(prefix='sqlmap_')
        
        # Build SQLmap command
        cmd = [
            'sqlmap',
            '-u', target,
            '--batch',  # Non-interactive
            '--output-dir', output_dir,
            '--level', str(level),
            '--risk', str(risk),
            '--random-agent',
            '--answers', 'crack=N',  # Don't crack hashes
            '--technique', 'BEUSTQ',  # All techniques
            # '--cookie', 'PHPSESSID=b7iksjtet7c6hv0fu04siv9vn5;security=low',   # DVWA cookie
            # '-p', 'id',  # Force test on 'id' parameter only
        ]
        
        # Mode-specific flags
        if mode == 'detect':
            # Just detect, don't exploit
            pass
        elif mode == 'exploit':
            cmd.extend(['--dump-all', '--exclude-sysdbs'])
        elif mode == 'dump':
            cmd.extend(['--dump', '--exclude-sysdbs'])
        
        # Execute SQLmap
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600  # 10 minutes max
            )
            
            raw_output = result.stdout + "\n" + result.stderr
            
            # Find the log file
            log_file = self._find_log_file(output_dir)
            
            return {
                'raw_output': raw_output,
                'log_file': log_file,
                'output_dir': output_dir,
                'exit_code': result.returncode,
                'metadata': {
                    'target': target,
                    'mode': mode,
                    'level': level,
                    'risk': risk
                },
                'artifacts': [log_file] if log_file else []
            }
            
        except subprocess.TimeoutExpired:
            return {
                'raw_output': 'SQLmap execution timed out after 600 seconds',
                'metadata': {'target': target, 'mode': mode},
                'artifacts': []
            }
    
    def parse_output(self, raw_output: Any, metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Parse SQLmap output to extract findings."""
        # Extract metadata from raw_output if it's a dict
        if isinstance(raw_output, dict):
            metadata = raw_output.get("metadata", {})
            output_text = raw_output.get("raw_output", "")
        else:
            metadata = {}
            output_text = str(raw_output) if raw_output else ""
        
        findings = []

        if not output_text:
            return findings

        # Parse SQLmap output (text-based)
        lines = output_text.split('\n')
        
        target = metadata.get('target', 'unknown')
        
        # Detect injectable parameters
        injectable_params = []
        current_param = None
        injection_type = None
        
        for line in lines:
            line_lower = line.lower()
            
            # Detect parameter
            if 'parameter:' in line_lower:
                parts = line.split('Parameter:')
                if len(parts) > 1:
                    current_param = parts[1].strip().split()[0]
            
            # Detect injection type
            if 'type:' in line_lower and current_param:
                parts = line.split('Type:')
                if len(parts) > 1:
                    injection_type = parts[1].strip()
            
            # Detect vulnerability confirmation
            if current_param and ('is vulnerable' in line_lower or 'injectable' in line_lower):
                injectable_params.append({
                    'parameter': current_param,
                    'type': injection_type or 'Unknown'
                })
                current_param = None
                injection_type = None
        
        # Create findings for each injectable parameter
        for param_info in injectable_params:
            severity = 'critical'  # SQL injection is always critical
            
            finding = {
                'title': f"SQL Injection in parameter '{param_info['parameter']}'",
                'severity': severity,
                'description': (
                    f"The parameter '{param_info['parameter']}' is vulnerable to SQL injection.\n"
                    f"Injection type: {param_info['type']}\n\n"
                    f"An attacker can manipulate SQL queries to:\n"
                    f"- Extract sensitive data from the database\n"
                    f"- Modify or delete database records\n"
                    f"- Bypass authentication mechanisms\n"
                    f"- Execute administrative operations on the database"
                ),
                'remediation': (
                    "1. Use parameterized queries (prepared statements)\n"
                    "2. Implement input validation and sanitization\n"
                    "3. Use ORM frameworks with built-in protection\n"
                    "4. Apply principle of least privilege for database accounts\n"
                    "5. Disable detailed error messages in production"
                ),
                'metadata': {
                    'parameter': param_info['parameter'],
                    'injection_type': param_info['type'],
                    'target': target,
                    'sqlmap_version': '1.9.6'
                }
            }
            
            findings.append(finding)
        
        # If no specific injections found but SQLmap indicates vulnerability
        if not findings and 'vulnerable' in raw_output.lower():
            findings.append({
                'title': f"Potential SQL Injection detected on {target}",
                'severity': 'high',
                'description': (
                    "SQLmap detected potential SQL injection vulnerabilities, "
                    "but could not identify specific vulnerable parameters. "
                    "Manual verification recommended."
                ),
                'remediation': (
                    "Review application code for SQL injection vulnerabilities. "
                    "Use parameterized queries and input validation."
                ),
                'metadata': {
                    'target': target,
                    'status': 'potential'
                }
            })
        
        return findings
    
    def _find_log_file(self, output_dir: str) -> str:
        """Find the SQLmap log file in output directory."""
        try:
            for root, dirs, files in os.walk(output_dir):
                for file in files:
                    if file.endswith('.log'):
                        return os.path.join(root, file)
        except Exception:
            pass
        return None
