"""SQLmap plugin for SQL injection detection and exploitation."""
import os
import re
import subprocess
import tempfile
from typing import Dict, Any, List
from core.plugins.base import PluginBase


class SQLmapPlugin(PluginBase):
    """SQLmap plugin for automated SQL injection testing."""

    name = "sqlmap"
    version = "1.1.0"
    description = "Automated SQL injection detection and exploitation"
    capabilities = ["web_scan", "sql_injection", "database_exploitation"]

    def validate_config(self) -> None:
        """Validate plugin configuration."""
        if 'target' not in self.config:
            raise ValueError("Missing required config: 'target' (URL)")

        target = self.config['target']
        if not target.startswith(('http://', 'https://')):
            raise ValueError("Target must be a valid HTTP/HTTPS URL")

        mode = self.config.get('mode', 'detect')
        valid_modes = ['detect', 'exploit', 'dump']
        if mode not in valid_modes:
            raise ValueError(f"Invalid mode. Must be one of: {valid_modes}")

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

        output_dir = tempfile.mkdtemp(prefix='sqlmap_')

        cmd = [
            'sqlmap',
            '-u', target,
            '--batch',
            '--output-dir', output_dir,
            '--level', str(level),
            '--risk', str(risk),
            '--random-agent',
            '--answers', 'crack=N',
            '--technique', 'BEUSTQ',
        ]

        # Optional cookie
        if self.config.get('cookie'):
            cmd.extend(['--cookie', self.config['cookie']])

        # Optional parameter
        if self.config.get('parameter'):
            cmd.extend(['-p', self.config['parameter']])

        # Optional headers
        if self.config.get('headers'):
            cmd.extend(['-H', self.config['headers']])

        # Scan forms
        if self.config.get('scan_forms'):
            cmd.append('--forms')

        # Tor
        if self.config.get('tor'):
            cmd.append('--tor')

        # Mode-specific flags
        if mode == 'exploit':
            cmd.extend(['--dump-all', '--exclude-sysdbs'])
        elif mode == 'dump':
            if self.config.get('database'):
                cmd.extend(['-D', self.config['database']])
            if self.config.get('table'):
                cmd.extend(['-T', self.config['table']])
            cmd.extend(['--dump', '--exclude-sysdbs'])

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600
            )

            raw_output = result.stdout + "\n" + result.stderr
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
        # Save original raw_output before overwriting
        original_raw = raw_output if isinstance(raw_output, dict) else {}

        if isinstance(raw_output, dict):
            metadata = raw_output.get("metadata", {})
            output_text = raw_output.get("raw_output", "")
        else:
            metadata = metadata or {}
            output_text = str(raw_output) if raw_output else ""

        findings = []
        if not output_text:
            return findings

        # Get target from metadata or original raw_output
        target = (metadata.get('target') or
                  original_raw.get('metadata', {}).get('target') or
                  self.config.get('target', 'unknown'))
        lines = output_text.split('\n')

        # --- Robust parser ---
        injectable_params = []
        current_param = None
        injection_types = []

        for line in lines:
            line_stripped = line.strip()
            line_lower = line_stripped.lower()

            # Detect "Parameter: id (GET)" inside injection block
            if line_stripped.startswith('Parameter:'):
                current_param = line_stripped.split('Parameter:')[1].strip().split()[0]
                injection_types = []

            # Detect injection type inside injection block
            if line_stripped.startswith('Type:') and current_param:
                injection_types.append(line_stripped.split('Type:')[1].strip())

            # Detect end of injection block
            if current_param and injection_types and line_stripped == '---':
                injectable_params.append({
                    'parameter': current_param,
                    'types': list(injection_types)
                })
                current_param = None
                injection_types = []

        # Fallback: detect via "GET parameter 'x' is vulnerable"
        if not injectable_params:
            matches = re.findall(
                r"(?:GET|POST|Cookie) parameter ['\"]?(\w+)['\"]? is vulnerable",
                output_text,
                re.IGNORECASE
            )
            types_found = re.findall(r"Type: (.+)", output_text)
            for param in matches:
                injectable_params.append({
                    'parameter': param,
                    'types': types_found[:4] if types_found else ['SQL Injection']
                })

        # Fallback: detect via "identified the following injection point"
        if not injectable_params and 'identified the following injection point' in output_text.lower():
            params = re.findall(r"Parameter: (\S+)", output_text)
            types_found = re.findall(r"Type: (.+)", output_text)
            if params:
                injectable_params.append({
                    'parameter': params[0],
                    'types': types_found[:4] if types_found else ['SQL Injection']
                })

        # Build findings
        for param_info in injectable_params:
            types_str = '\n'.join(f"  • {t}" for t in param_info.get('types', ['Unknown']))
            finding = {
                'title': f"SQL Injection in parameter '{param_info['parameter']}' — {target}",
                'severity': 'critical',
                'description': (
                    f"The parameter '{param_info['parameter']}' is vulnerable to SQL injection.\n\n"
                    f"Injection types confirmed:\n{types_str}\n\n"
                    f"An attacker can:\n"
                    f"  • Extract sensitive data from the database\n"
                    f"  • Modify or delete database records\n"
                    f"  • Bypass authentication mechanisms\n"
                    f"  • Execute administrative operations on the database"
                ),
                'remediation': (
                    "1. Use parameterized queries (prepared statements)\n"
                    "2. Implement strict input validation and sanitization\n"
                    "3. Use ORM frameworks with built-in SQL injection protection\n"
                    "4. Apply principle of least privilege for database accounts\n"
                    "5. Disable detailed error messages in production"
                ),
                'metadata': {
                    'parameter': param_info['parameter'],
                    'injection_types': param_info.get('types', []),
                    'target': target,
                }
            }
            findings.append(finding)

        # Last fallback: SQLmap ran but parser missed something
        if not findings and 'vulnerable' in output_text.lower():
            findings.append({
                'title': f"Potential SQL Injection detected — {target}",
                'severity': 'high',
                'description': (
                    "SQLmap detected potential SQL injection vulnerabilities "
                    "but could not identify specific parameters automatically. "
                    "Manual verification is recommended.\n\n"
                    "Review the raw SQLmap output for details."
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
