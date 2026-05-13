"""Metasploit log file parser."""
from plugins.external.base import ExternalParserBase
from typing import Dict, Any, List
import re
import os


class MetasploitParser(ExternalParserBase):
    """Parse Metasploit console logs."""
    
    name = "metasploit"
    supported_extensions = ['.log', '.txt']
    max_file_size_mb = 50  # 50MB max
    
    def parse(self, filepath: str, user_id: str) -> Dict[str, Any]:
        """Parse Metasploit log file."""
        self.validate_file(filepath)
        
        findings = []
        metadata = {
            'filename': os.path.basename(filepath),
            'size_mb': os.path.getsize(filepath) / (1024 * 1024),
            'parser': 'metasploit'
        }
        
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Extract successful exploits
            exploits = self._extract_exploits(content)
            
            # Extract opened sessions
            sessions = self._extract_sessions(content)
            
            # Extract vulnerabilities discovered
            vulns = self._extract_vulnerabilities(content)
            
            # Create findings
            if exploits:
                findings.append({
                    'title': f"Successful exploits ({len(exploits)})",
                    'severity': 'critical',
                    'description': f"Metasploit successfully exploited {len(exploits)} targets.",
                    'raw_data': {'exploits': exploits}
                })
            
            if sessions:
                findings.append({
                    'title': f"Active sessions opened ({len(sessions)})",
                    'severity': 'high',
                    'description': f"Metasploit opened {len(sessions)} shell/meterpreter sessions.",
                    'raw_data': {'sessions': sessions}
                })
            
            if vulns:
                findings.append({
                    'title': f"Vulnerabilities identified ({len(vulns)})",
                    'severity': 'medium',
                    'description': f"Metasploit identified {len(vulns)} potential vulnerabilities.",
                    'raw_data': {'vulnerabilities': vulns}
                })
            
            summary = (
                f"Metasploit log analysis: {len(exploits)} exploits, "
                f"{len(sessions)} sessions, {len(vulns)} vulnerabilities"
            )
            
            return {
                'findings': findings,
                'metadata': metadata,
                'summary': summary
            }
            
        except Exception as e:
            raise Exception(f"Metasploit log parsing failed: {str(e)}")
    
    def _extract_exploits(self, content: str) -> List[Dict[str, str]]:
        """Extract successful exploit attempts."""
        exploits = []
        
        # Pattern: [*] exploit/... succeeded
        pattern = r'\[\*\]\s+(exploit/[\w/]+).*?succeeded'
        matches = re.finditer(pattern, content, re.IGNORECASE)
        
        for match in matches:
            exploits.append({
                'module': match.group(1),
                'status': 'succeeded'
            })
        
        return exploits
    
    def _extract_sessions(self, content: str) -> List[Dict[str, str]]:
        """Extract opened sessions."""
        sessions = []
        
        # Pattern: [*] Command shell session X opened
        # Pattern: [*] Meterpreter session X opened
        pattern = r'\[\*\]\s+(Command shell|Meterpreter) session (\d+) opened'
        matches = re.finditer(pattern, content, re.IGNORECASE)
        
        for match in matches:
            sessions.append({
                'type': match.group(1),
                'session_id': match.group(2)
            })
        
        return sessions
    
    def _extract_vulnerabilities(self, content: str) -> List[Dict[str, str]]:
        """Extract identified vulnerabilities."""
        vulns = []
        
        # Pattern: [+] Vulnerable to CVE-XXXX-XXXX
        pattern = r'\[\+\].*?(CVE-\d{4}-\d{4,7})'
        matches = re.finditer(pattern, content, re.IGNORECASE)
        
        for match in matches:
            vulns.append({
                'cve': match.group(1)
            })
        
        return vulns
