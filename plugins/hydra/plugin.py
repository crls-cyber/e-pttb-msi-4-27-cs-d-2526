"""
Hydra Plugin - Network login brute-force
Supports SSH, FTP, HTTP, RDP, SMB and 50+ protocols

⚠️ LEGAL WARNING:
Only use on systems you own or have explicit written permission to test.
Unauthorized brute-force attacks are illegal.
"""
from core.plugins.base import PluginBase
from typing import Dict, Any, List
import subprocess
import re
import logging

logger = logging.getLogger(__name__)


class HydraPlugin(PluginBase):
    """Hydra brute-force plugin."""
    
    name = "hydra"
    version = "1.0.0"
    description = "Network login brute-force: SSH, FTP, HTTP, RDP, SMB, etc."
    capabilities = ["brute_force", "password_cracking", "authentication_testing"]
    
    required_params = ["target", "service"]
    optional_params = ["username", "userlist", "password", "passlist", "port", "threads"]
    
    def validate_config(self) -> None:
        """Validate plugin configuration."""
        if "target" not in self.config:
            raise ValueError("Missing required parameter: target (IP or hostname)")
        
        if "service" not in self.config:
            raise ValueError("Missing required parameter: service (ssh, ftp, http-post-form, etc.)")
        
        # Must have either username or userlist
        if "username" not in self.config and "userlist" not in self.config:
            raise ValueError("Must provide either 'username' or 'userlist'")
        
        # Must have either password or passlist
        if "password" not in self.config and "passlist" not in self.config:
            raise ValueError("Must provide either 'password' or 'passlist'")
        
        # Validate service
        valid_services = [
            'ssh', 'ftp', 'http-get', 'http-post', 'http-post-form',
            'https-get', 'https-post', 'https-post-form',
            'smb', 'rdp', 'telnet', 'mysql', 'postgres', 'mssql'
        ]
        service = self.config["service"]
        if service not in valid_services:
            logger.warning(f"Service '{service}' not in common list. Hydra supports 50+ protocols.")
    
    def run(self) -> Dict[str, Any]:
        """Execute Hydra brute-force."""
        target = self.config["target"]
        service = self.config["service"]
        port = self.config.get("port")
        threads = self.config.get("threads", 4)
        
        logger.info(f"Starting Hydra brute-force: {service}://{target}")
        
        # Build command
        cmd = ["hydra", "-t", str(threads)]
        
        # Username(s)
        if "username" in self.config:
            cmd.extend(["-l", self.config["username"]])
        else:
            cmd.extend(["-L", self.config["userlist"]])
        
        # Password(s)
        if "password" in self.config:
            cmd.extend(["-p", self.config["password"]])
        else:
            cmd.extend(["-P", self.config["passlist"]])
        
        # Port
        if port:
            cmd.extend(["-s", str(port)])
        
        # Output format
        cmd.extend(["-o", "/tmp/hydra_output.txt", "-f"])  # -f = stop on first success
        
        # Target and service
        cmd.append(f"{service}://{target}")
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes max
            )
            
            return {
                "raw_output": result.stdout + result.stderr,
                "artifacts": ["/tmp/hydra_output.txt"],
                "metadata": {
                    "exit_code": result.returncode,
                    "command": ' '.join(cmd),
                    "target": target,
                    "service": service
                }
            }
        
        except subprocess.TimeoutExpired:
            raise Exception("Hydra brute-force timed out after 5 minutes")
        except Exception as e:
            raise Exception(f"Hydra execution failed: {str(e)}")
    
    def parse_output(self, raw_output: Any) -> List[Dict[str, Any]]:
        """Parse Hydra output into findings."""
        findings = []
        
        if isinstance(raw_output, dict):
            output_text = raw_output.get("raw_output", "")
            metadata = raw_output.get("metadata", {})
        else:
            output_text = str(raw_output) if raw_output else ""
            metadata = {}
        
        # Pattern: [PORT][SERVICE] host: IP   login: USER   password: PASS
        pattern = r'\[(\d+)\]\[(\w+)\]\s+host:\s+(\S+)\s+login:\s+(\S+)\s+password:\s+(\S+)'
        matches = re.finditer(pattern, output_text, re.IGNORECASE)
        
        credentials_found = []
        for match in matches:
            port, service, host, login, password = match.groups()
            credentials_found.append({
                'port': port,
                'service': service,
                'host': host,
                'login': login,
                'password': password
            })
        
        if credentials_found:
            for cred in credentials_found:
                findings.append({
                    'title': f"Valid credentials found: {cred['login']}@{cred['host']}",
                    'severity': 'critical',
                    'description': (
                        f"Hydra successfully brute-forced credentials:\n\n"
                        f"Service: {cred['service']}\n"
                        f"Host: {cred['host']}:{cred['port']}\n"
                        f"Username: {cred['login']}\n"
                        f"Password: {cred['password']}\n\n"
                        f"These credentials were guessed through brute-force attack."
                    ),
                    'remediation': (
                        "Immediately change the compromised password. "
                        "Enforce strong password policy (min 12 chars, complexity). "
                        "Implement account lockout after failed attempts. "
                        "Use SSH keys instead of passwords. "
                        "Enable multi-factor authentication (MFA)."
                    ),
                    'raw_data': cred
                })
        else:
            # Check for common error messages
            if "0 valid password" in output_text.lower():
                findings.append({
                    'title': "No valid credentials found",
                    'severity': 'info',
                    'description': (
                        f"Hydra brute-force completed but found no valid credentials.\n\n"
                        f"Target: {metadata.get('target', 'N/A')}\n"
                        f"Service: {metadata.get('service', 'N/A')}\n\n"
                        f"This suggests the service has strong passwords or effective brute-force protection."
                    ),
                    'remediation': "Continue using strong passwords and monitoring for brute-force attempts.",
                    'raw_data': metadata
                })
            else:
                findings.append({
                    'title': "Brute-force attack completed",
                    'severity': 'info',
                    'description': (
                        f"Hydra brute-force scan completed.\n\n"
                        f"Check raw output for details."
                    ),
                    'remediation': "Review attack logs and ensure brute-force protection is enabled.",
                    'raw_data': metadata
                })
        
        logger.info(f"Parsed {len(findings)} findings from Hydra output")
        return findings
