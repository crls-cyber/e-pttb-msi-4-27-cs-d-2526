"""Hydra plugin for controlled brute-force attacks."""
from core.plugins import PluginBase
from typing import Dict, Any, List
import subprocess
import re
import tempfile
import os


class HydraPlugin(PluginBase):
    """Hydra brute-force plugin with security controls."""
    
    name = "hydra"
    version = "1.0.0"
    description = "Controlled brute-force testing (SSH, FTP, HTTP) - Lab use only"
    capabilities = ["brute_force", "password_cracking"]
    
    # Security limits
    MAX_ATTEMPTS = 100
    MAX_THREADS = 4
    TIMEOUT_SECONDS = 300  # 5 minutes max
    
    def validate_config(self) -> None:
        """Validate plugin configuration."""
        if 'target' not in self.config:
            raise ValueError("Parameter 'target' is required")
        
        if 'service' not in self.config:
            raise ValueError("Parameter 'service' is required (ssh, ftp, http-get, etc.)")
        
        # Require explicit confirmation
        if not self.config.get('confirmed', False):
            raise ValueError(
                "SECURITY: Brute-force attacks require explicit confirmation. "
                "Set 'confirmed': true in config after reading warnings."
            )
        
        # Validate wordlists
        if 'username_list' in self.config:
            if not os.path.exists(self.config['username_list']):
                raise ValueError(f"Username wordlist not found: {self.config['username_list']}")
        
        if 'password_list' in self.config:
            if not os.path.exists(self.config['password_list']):
                raise ValueError(f"Password wordlist not found: {self.config['password_list']}")
    
    def run(self) -> Dict[str, Any]:
        """Execute Hydra brute-force attack."""
        target = self.config['target']
        service = self.config['service']
        port = self.config.get('port', self._default_port(service))
        threads = min(self.config.get('threads', 4), self.MAX_THREADS)
        
        # Prepare credentials
        username = self.config.get('username')
        password = self.config.get('password')
        username_list = self.config.get('username_list')
        password_list = self.config.get('password_list')
        
        # Build Hydra command
        cmd = ['hydra', '-t', str(threads), '-w', '10']
        
        # Add credentials
        if username and password:
            cmd.extend(['-l', username, '-p', password])
        elif username and password_list:
            cmd.extend(['-l', username, '-P', password_list])
        elif username_list and password:
            cmd.extend(['-L', username_list, '-p', password])
        elif username_list and password_list:
            cmd.extend(['-L', username_list, '-P', password_list])
        else:
            raise ValueError("Must provide username/password or wordlist paths")
        
        # Add service and target
        cmd.extend(['-s', str(port), f'{service}://{target}'])
        
        # Add verbose output
        cmd.append('-V')
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.TIMEOUT_SECONDS
            )
            
            return {
                'raw_output': result.stdout + '\n' + result.stderr,
                'artifacts': [],
                'metadata': {
                    'exit_code': result.returncode,
                    'command': ' '.join(cmd),
                    'target': target,
                    'service': service,
                    'threads': threads
                }
            }
            
        except subprocess.TimeoutExpired:
            raise Exception(f"Hydra attack timed out after {self.TIMEOUT_SECONDS} seconds")
        except Exception as e:
            raise Exception(f"Hydra execution failed: {str(e)}")
    
    def parse_output(self, raw_output: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse Hydra output into findings."""
        findings = []
        
        # Extract successful credentials
        # Pattern: [port][service] host: IP   login: USER   password: PASS
        pattern = r'\[(\d+)\]\[(\w+)\]\s+host:\s+([\d.]+)\s+login:\s+(\S+)\s+password:\s+(\S+)'
        matches = re.finditer(pattern, raw_output, re.IGNORECASE)
        
        credentials_found = []
        for match in matches:
            credentials_found.append({
                'port': match.group(1),
                'service': match.group(2),
                'host': match.group(3),
                'username': match.group(4),
                'password': match.group(5)
            })
        
        if credentials_found:
            findings.append({
                'title': f"Valid credentials found ({len(credentials_found)})",
                'severity': 'critical',
                'description': (
                    f"Hydra successfully brute-forced {len(credentials_found)} "
                    f"credential(s) on {metadata['service']}. "
                    "Weak passwords detected."
                ),
                'raw_data': {'credentials': credentials_found}
            })
        else:
            # Check if attack completed without success
            if 'valid password found' not in raw_output.lower():
                findings.append({
                    'title': 'No valid credentials found',
                    'severity': 'info',
                    'description': (
                        f"Hydra brute-force completed on {metadata['service']} "
                        "but found no valid credentials. Service may be hardened."
                    )
                })
        
        return findings
    
    def _default_port(self, service: str) -> int:
        """Get default port for service."""
        ports = {
            'ssh': 22,
            'ftp': 21,
            'telnet': 23,
            'http-get': 80,
            'https-get': 443,
            'mysql': 3306,
            'postgres': 5432,
            'rdp': 3389,
            'smb': 445
        }
        return ports.get(service, 0)
