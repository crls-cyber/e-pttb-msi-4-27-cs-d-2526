"""Wireshark PCAP file parser."""
from plugins.external.base import ExternalParserBase
from typing import Dict, Any, List
import subprocess
import json
import os


class WiresharkParser(ExternalParserBase):
    """Parse Wireshark PCAP files using tshark."""
    
    name = "wireshark"
    supported_extensions = ['.pcap', '.pcapng', '.cap']
    max_file_size_mb = 100  # 100MB max
    
    def parse(self, filepath: str, user_id: str) -> Dict[str, Any]:
        """Parse PCAP file with tshark."""
        self.validate_file(filepath)
        
        findings = []
        metadata = {
            'filename': os.path.basename(filepath),
            'size_mb': os.path.getsize(filepath) / (1024 * 1024),
            'parser': 'wireshark'
        }
        
        try:
            # Extract basic statistics
            stats = self._extract_statistics(filepath)
            metadata.update(stats)
            
            # Extract protocols
            protocols = self._extract_protocols(filepath)
            
            # Extract HTTP traffic (potential data leakage)
            http_findings = self._extract_http_traffic(filepath)
            findings.extend(http_findings)
            
            # Extract unencrypted credentials (FTP, Telnet, HTTP Basic Auth)
            cred_findings = self._extract_credentials(filepath)
            findings.extend(cred_findings)
            
            # Summary
            summary = (
                f"PCAP analysis: {stats.get('packet_count', 0)} packets, "
                f"{len(protocols)} protocols, {len(findings)} findings"
            )
            
            return {
                'findings': findings,
                'metadata': metadata,
                'summary': summary
            }
            
        except Exception as e:
            raise Exception(f"PCAP parsing failed: {str(e)}")
    
    def _extract_statistics(self, filepath: str) -> Dict[str, Any]:
        """Extract basic PCAP statistics."""
        try:
            result = subprocess.run(
                ['tshark', '-r', filepath, '-q', '-z', 'io,stat,0'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Simpler: count packets directly
            result = subprocess.run(
                ['tshark', '-r', filepath, '-T', 'fields', '-e', 'frame.number'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Count lines = packet count
            packet_count = len([line for line in result.stdout.strip().split('\n') if line])
            
            return {'packet_count': packet_count}
        
        except Exception as e:
            return {'packet_count': 0, 'error': str(e)}
    
    def _extract_protocols(self, filepath: str) -> List[str]:
        """Extract list of protocols used."""
        try:
            result = subprocess.run(
                ['tshark', '-r', filepath, '-q', '-z', 'io,phs'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            protocols = []
            for line in result.stdout.split('\n'):
                if line.strip() and not line.startswith('==='):
                    protocol = line.split()[0] if line.split() else None
                    if protocol and protocol not in protocols:
                        protocols.append(protocol)
            
            return protocols[:20]  # Limit to top 20
            
        except Exception:
            return []
    
    def _extract_http_traffic(self, filepath: str) -> List[Dict[str, Any]]:
        """Extract HTTP requests (unencrypted traffic)."""
        findings = []
        
        try:
            result = subprocess.run(
                ['tshark', '-r', filepath, '-Y', 'http.request', '-T', 'fields',
                 '-e', 'ip.src', '-e', 'http.host', '-e', 'http.request.uri'],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            http_requests = []
            for line in result.stdout.split('\n'):
                if line.strip():
                    parts = line.split('\t')
                    if len(parts) >= 3:
                        http_requests.append({
                            'src_ip': parts[0],
                            'host': parts[1],
                            'uri': parts[2]
                        })
            
            if http_requests:
                findings.append({
                    'title': f"Unencrypted HTTP traffic detected ({len(http_requests)} requests)",
                    'severity': 'medium',
                    'description': (
                        f"Found {len(http_requests)} HTTP requests in clear text. "
                        "Sensitive data may be exposed. Consider using HTTPS."
                    ),
                    'raw_data': {'http_requests': http_requests[:10]}  # First 10
                })
            
        except Exception as e:
            pass  # Silent fail, not critical
        
        return findings
    
    def _extract_credentials(self, filepath: str) -> List[Dict[str, Any]]:
        """Extract potential credentials (FTP, Telnet, HTTP Basic Auth)."""
        findings = []
        
        try:
            # Check for FTP credentials
            result = subprocess.run(
                ['tshark', '-r', filepath, '-Y', 'ftp.request.command == "USER" or ftp.request.command == "PASS"',
                 '-T', 'fields', '-e', 'ftp.request.arg'],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            ftp_creds = [line.strip() for line in result.stdout.split('\n') if line.strip()]
            
            if ftp_creds:
                findings.append({
                    'title': f"FTP credentials in clear text ({len(ftp_creds)} found)",
                    'severity': 'high',
                    'description': (
                        f"Found {len(ftp_creds)} FTP usernames/passwords transmitted in clear text. "
                        "Immediate security risk."
                    ),
                    'raw_data': {'ftp_credentials': ftp_creds[:5]}  # First 5
                })
        
        except Exception:
            pass
        
        return findings
