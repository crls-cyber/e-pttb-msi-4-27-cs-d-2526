"""theHarvester plugin for OSINT reconnaissance."""
from core.plugins import PluginBase
from typing import Dict, Any, List
import subprocess
import json
import tempfile
import os


class TheHarvesterPlugin(PluginBase):
    """theHarvester OSINT reconnaissance plugin."""

    name = "theharvester"
    version = "1.0.0"
    description = "OSINT reconnaissance: emails, subdomains, IPs (theHarvester 4.6.0)"
    capabilities = ["osint", "reconnaissance", "email_gathering", "subdomain_enum"]

    def validate_config(self) -> None:
        """Validate plugin configuration."""
        if 'domain' not in self.config and 'target' not in self.config:
            raise ValueError("Parameter 'domain' or 'target' is required")

        # Validate source
        valid_sources = [
            'anubis', 'baidu', 'bing', 'bingapi', 'certspotter', 'crtsh',
            'dnsdumpster', 'duckduckgo', 'github-code', 'hackertarget',
            'hunter', 'intelx', 'otx', 'rapiddns', 'sublist3r', 'threatminer',
            'virustotal', 'yahoo', 'all'
        ]
        source = self.config.get('source', 'all')
        if source not in valid_sources:
            raise ValueError(f"Invalid source. Must be one of: {', '.join(valid_sources)}")

    def run(self) -> Dict[str, Any]:
        """Execute theHarvester reconnaissance."""
        domain = self.config.get('domain') or self.config.get('target')
        source = self.config.get('source', 'all')
        limit = self.config.get('limit', 500)

        # Create temporary files for output
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json_output_path = f.name.replace('.json', '')  # theHarvester adds extensions

        try:
            cmd = [
                'theHarvester',
                '-d', domain,
                '-b', source,
                '-l', str(limit),
                '-f', json_output_path
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes max
            )

            # Read JSON output
            json_file = f"{json_output_path}.json"
            xml_file = f"{json_output_path}.xml"

            raw_output = result.stdout

            # Try to parse JSON if exists
            findings_data = {}
            if os.path.exists(json_file):
                with open(json_file, 'r') as f:
                    findings_data = json.load(f)

            artifacts = []
            if os.path.exists(json_file):
                artifacts.append(json_file)
            if os.path.exists(xml_file):
                artifacts.append(xml_file)

            return {
                'raw_output': raw_output,
                'findings_data': findings_data,
                'artifacts': artifacts,
                'metadata': {
                    'exit_code': result.returncode,
                    'command': ' '.join(cmd),
                    'domain': domain,
                    'source': source
                }
            }

        except subprocess.TimeoutExpired:
            raise Exception("theHarvester reconnaissance timed out after 5 minutes")
        except Exception as e:
            raise Exception(f"theHarvester execution failed: {str(e)}")

    def parse_output(self, raw_output: Any) -> List[Dict[str, Any]]:
        """Parse theHarvester output into findings."""
        findings = []

        # Extract findings_data from raw_output dict
        if isinstance(raw_output, dict):
            findings_data = raw_output.get('findings_data', {})
            raw_text = raw_output.get('raw_output', '')
        else:
            findings_data = {}
            raw_text = str(raw_output) if raw_output else ''

        # Parse emails
        emails = findings_data.get('emails', [])
        if emails:
            findings.append({
                'title': f"Email addresses discovered ({len(emails)})",
                'severity': 'info',
                'description': f"Found {len(emails)} email addresses: {', '.join(emails[:5])}{'...' if len(emails) > 5 else ''}",
                'raw_data': {'emails': emails},
                'remediation': 'Review exposed email addresses. Consider email protection services to prevent harvesting.'
            })

        # Parse hosts/subdomains
        hosts = findings_data.get('hosts', [])
        if hosts:
            findings.append({
                'title': f"Subdomains/hosts discovered ({len(hosts)})",
                'severity': 'info',
                'description': f"Found {len(hosts)} hosts/subdomains",
                'raw_data': {'hosts': hosts},
                'remediation': 'Review exposed subdomains. Ensure unused subdomains are removed from DNS.'
            })

        # Parse IPs
        ips = findings_data.get('ips', [])
        if ips:
            findings.append({
                'title': f"IP addresses discovered ({len(ips)})",
                'severity': 'low',
                'description': f"Found {len(ips)} IP addresses associated with target",
                'raw_data': {'ips': ips},
                'remediation': 'Verify that all exposed IP addresses are intentional and properly secured.'
            })

        # Fallback: parse from raw stdout
        if not findings and raw_text:
            lines = raw_text.split('\n')
            email_count = sum(1 for line in lines if '@' in line and '.' in line)
            if email_count > 0:
                findings.append({
                    'title': f"OSINT reconnaissance completed",
                    'severity': 'info',
                    'description': f"theHarvester found approximately {email_count} email addresses and other OSINT data. Check artifacts for details.",
                    'remediation': 'Review the complete output file for detailed findings.'
                })

        return findings if findings else [{
            'title': 'OSINT reconnaissance completed',
            'severity': 'info',
            'description': 'theHarvester scan completed. Check raw output for results.',
            'remediation': 'Review the scan output for any exposed information.'
        }]
