"""Ettercap log parser."""
from plugins.external.base import ExternalParserBase
from typing import Dict, Any, List
import re
import os


class EttercapParser(ExternalParserBase):
    """Parse Ettercap MITM logs."""

    name = "ettercap"
    supported_extensions = ['.log', '.txt']
    max_file_size_mb = 20

    def parse(self, filepath: str, user_id: str) -> Dict[str, Any]:
        """Parse Ettercap log file."""
        self.validate_file(filepath)

        findings = []
        metadata = {
            'filename': os.path.basename(filepath),
            'size_mb': os.path.getsize(filepath) / (1024 * 1024),
            'parser': 'ettercap'
        }

        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            # Extract credentials
            credentials = self._extract_credentials(content)
            metadata['credentials_count'] = len(credentials)

            # Extract ARP poisoning info
            arp_info = self._extract_arp_info(content)
            metadata.update(arp_info)

            # Create findings for credentials
            for cred in credentials:
                findings.append({
                    'title': f"Credentials captured: {cred['username']}",
                    'severity': 'critical',
                    'description': (
                        f"Ettercap captured plaintext credentials:\n\n"
                        f"Username: {cred['username']}\n"
                        f"Password: {cred['password']}\n"
                        f"Protocol: {cred.get('protocol', 'Unknown')}\n"
                        f"Target: {cred.get('target', 'N/A')}"
                    ),
                    'remediation': (
                        "Use encrypted protocols (HTTPS, SSH, SFTP). "
                        "Disable FTP, Telnet, and HTTP Basic Auth."
                    ),
                    'raw_data': cred
                })

            # Create finding for ARP poisoning
            if arp_info.get('targets'):
                findings.append({
                    'title': "ARP poisoning attack successful",
                    'severity': 'high',
                    'description': (
                        f"Ettercap performed ARP poisoning on targets:\n\n"
                        f"{', '.join(arp_info['targets'])}\n\n"
                        f"Network is vulnerable to MITM attacks."
                    ),
                    'remediation': (
                        "Enable Dynamic ARP Inspection on switches. "
                        "Use static ARP entries for critical hosts."
                    ),
                    'raw_data': arp_info
                })

            summary = f"Ettercap analysis: {len(credentials)} credentials, {len(arp_info.get('targets', []))} targets"

            return {
                'findings': findings,
                'metadata': metadata,
                'summary': summary
            }

        except Exception as e:
            raise Exception(f"Ettercap parsing failed: {str(e)}")

    def _extract_credentials(self, content: str) -> List[Dict[str, str]]:
        """Extract credentials from Ettercap log."""
        credentials = []

        # Pattern: USER: admin  PASS: password123  INFO: ftp://192.168.1.100
        pattern = r'USER:\s*(\S+)\s+PASS:\s*(\S+)(?:\s+INFO:\s*(\S+))?'
        
        matches = re.finditer(pattern, content, re.IGNORECASE)
        for match in matches:
            target = match.group(3) if match.group(3) else 'unknown'
            cred = {
                'username': match.group(1),
                'password': match.group(2),
                'target': target,
                'protocol': self._detect_protocol(target)
            }
            credentials.append(cred)

        return credentials

    def _extract_arp_info(self, content: str) -> Dict[str, Any]:
        """Extract ARP poisoning information."""
        info = {'targets': []}

        # Extract target IPs
        ip_pattern = r'ARP.*?(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
        matches = re.finditer(ip_pattern, content, re.IGNORECASE)
        
        for match in matches:
            ip = match.group(1)
            if ip not in info['targets']:
                info['targets'].append(ip)

        return info

    def _detect_protocol(self, target: str) -> str:
        """Detect protocol from target string."""
        target_lower = target.lower()
        
        if 'ftp://' in target_lower:
            return 'FTP'
        elif 'http://' in target_lower:
            return 'HTTP'
        elif 'telnet' in target_lower:
            return 'Telnet'
        elif ':22' in target or 'ssh' in target_lower:
            return 'SSH'
        else:
            return 'Unknown'
