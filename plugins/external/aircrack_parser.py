"""Aircrack-ng output parser."""
from plugins.external.base import ExternalParserBase
from typing import Dict, Any, List
import re
import os


class AircrackParser(ExternalParserBase):
    """Parse Aircrack-ng cracking output."""

    name = "aircrack"
    supported_extensions = ['.txt', '.log']
    max_file_size_mb = 10

    def parse(self, filepath: str, user_id: str) -> Dict[str, Any]:
        """Parse Aircrack-ng output file."""
        self.validate_file(filepath)

        findings = []
        metadata = {
            'filename': os.path.basename(filepath),
            'size_mb': os.path.getsize(filepath) / (1024 * 1024),
            'parser': 'aircrack'
        }

        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            # Extract cracked password
            password = self._extract_password(content)

            if password:
                findings.append({
                    'title': f"WiFi password cracked: {password}",
                    'severity': 'critical',
                    'description': (
                        f"Aircrack-ng successfully cracked the WPA/WPA2 password: **{password}**\n\n"
                        f"This demonstrates the network is vulnerable to dictionary attacks."
                    ),
                    'remediation': (
                        "Immediately change the WiFi password to a strong passphrase (20+ characters). "
                        "Avoid dictionary words. Consider upgrading to WPA3."
                    ),
                    'raw_data': {'password': password}
                })

            summary = f"Aircrack-ng analysis: password {'cracked' if password else 'not found'}"

            return {
                'findings': findings,
                'metadata': metadata,
                'summary': summary
            }

        except Exception as e:
            raise Exception(f"Aircrack-ng parsing failed: {str(e)}")

    def _extract_password(self, content: str) -> str:
        """Extract cracked password from output."""
        # Pattern: KEY FOUND! [ password ]
        match = re.search(r'KEY FOUND!\s*\[\s*(.+?)\s*\]', content, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return None
