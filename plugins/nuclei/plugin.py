"""
Nuclei plugin - Fast web vulnerability scanner
"""
import json
import subprocess
import tempfile
import os
from typing import Dict, List, Any
from core.plugins.base import PluginBase


class NucleiPlugin(PluginBase):
    """Nuclei vulnerability scanner plugin"""

    name = "nuclei"
    version = "1.0.0"
    description = "Web vulnerability scanner using Nuclei templates"
    capabilities = ["web_scan", "vulnerability_detection", "cve_detection"]

    def validate_config(self) -> None:
        """Validate plugin configuration"""
        if 'target' not in self.config:
            raise ValueError("Missing required parameter: target (URL)")

        target = self.config['target']
        if not target.startswith(('http://', 'https://')):
            raise ValueError("Target must be a valid URL (http:// or https://)")

    def run(self) -> Dict[str, Any]:
        """Execute Nuclei scan"""
        target = self.config['target']
        severity = self.config.get('severity', 'critical,high,medium')
        templates = self.config.get('templates', '')

        # Temporary file for JSON output
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
            json_output = tmp.name

        try:
            # Build Nuclei command
            cmd = [
                'nuclei',
                '-target', target,
                '-severity', severity,
                '-jsonl',
                '-o', json_output,
                '-silent'
            ]

            if templates and templates.strip():
                cmd.extend(['-t', '/root/nuclei-templates/'])
                cmd.extend(['-tags', templates])

            # Execute Nuclei (timeout 10 minutes)
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600
            )

            # Read JSON output
            if os.path.exists(json_output) and os.path.getsize(json_output) > 0:
                with open(json_output, 'r') as f:
                    json_content = '[' + ','.join(f.read().strip().split('\n')) + ']'
            else:
                json_content = '[]'

            return {
                'raw_output': json_content,
                'artifacts': [json_output],
                'metadata': {
                    'target': target,
                    'severity_filter': severity,
                    'exit_code': result.returncode
                }
            }

        except subprocess.TimeoutExpired:
            raise Exception("Nuclei scan timed out after 10 minutes")
        except Exception as e:
            if os.path.exists(json_output):
                os.remove(json_output)
            raise Exception(f"Nuclei execution failed: {str(e)}")

    def parse_output(self, raw_output: str, metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Parse Nuclei JSON output into findings with deduplication."""
        findings = []
        # Deduplication dict: key = (template-id, matched-at)
        deduplicated = {}

        try:
            results = json.loads(raw_output)

            for item in results:
                if not item:
                    continue

                template_id = item.get('template-id', 'unknown')
                template_name = item.get('info', {}).get('name', 'Unknown vulnerability')
                severity = item.get('info', {}).get('severity', 'info').lower()
                description = item.get('info', {}).get('description', 'No description available')
                matched_at = item.get('matched-at', item.get('host', (metadata or {}).get('target', 'Unknown')))

                cve_ids = item.get('info', {}).get('classification', {}).get('cve-id', [])
                cwe_ids = item.get('info', {}).get('classification', {}).get('cwe-id', [])

                severity_map = {
                    'critical': 'critical', 'high': 'high',
                    'medium': 'medium', 'low': 'low', 'info': 'info'
                }
                mapped_severity = severity_map.get(severity, 'info')

                references = item.get('info', {}).get('reference', [])
                remediation = "Review the vulnerability details and apply security patches."
                if references:
                    remediation += f"\n\nReferences:\n" + "\n".join(f"- {ref}" for ref in references[:3])

                # Deduplication key
                dedup_key = (template_id, matched_at)

                # Extract meta info (credentials, extracted results)
                meta = item.get('meta', {})
                extracted = item.get('extracted-results', [])

                if dedup_key in deduplicated:
                    # Merge: add credentials/extracted results to existing finding
                    existing = deduplicated[dedup_key]
                    if meta:
                        existing['_meta_list'].append(meta)
                    if extracted:
                        existing['_extracted_list'].extend(extracted)
                else:
                    # New finding
                    deduplicated[dedup_key] = {
                        'title': f"{template_name} - {matched_at}",
                        'severity': mapped_severity,
                        'description': description,
                        'remediation': remediation,
                        '_meta_list': [meta] if meta else [],
                        '_extracted_list': extracted if extracted else [],
                        'metadata': {
                            'template_id': template_id,
                            'matched_at': matched_at,
                            'cve_ids': cve_ids,
                            'cwe_ids': cwe_ids
                        }
                    }

            # Build final findings with enriched descriptions
            for finding in deduplicated.values():
                meta_list = finding.pop('_meta_list', [])
                extracted_list = finding.pop('_extracted_list', [])

                full_description = finding['description']

                # Add CVE/CWE info
                cve_ids = finding['metadata'].get('cve_ids', [])
                cwe_ids = finding['metadata'].get('cwe_ids', [])
                if cve_ids:
                    full_description += f"\n\nCVE IDs: {', '.join(cve_ids)}"
                if cwe_ids:
                    full_description += f"\nCWE IDs: {', '.join(cwe_ids)}"

                # Enrich with credentials found (Option C)
                if meta_list:
                    creds = []
                    for m in meta_list:
                        if 'username' in m and 'password' in m:
                            creds.append(f"{m['username']}/{m['password']}")
                        elif 'usernames' in m and 'password' in m:
                            creds.append(f"{m['usernames']}/{m['password']}")
                        elif 'usernames' in m and 'passwords' in m:
                            creds.append(f"{m['usernames']}/{m['passwords']}")
                    if creds:
                        full_description += f"\n\n🔑 Credentials found ({len(creds)}):\n"
                        full_description += "\n".join(f"  • {c}" for c in creds)

                # Enrich with extracted results
                if extracted_list:
                    unique_extracted = list(dict.fromkeys(extracted_list))
                    full_description += f"\n\n📋 Extracted data:\n"
                    full_description += "\n".join(f"  • {e}" for e in unique_extracted[:10])

                finding['description'] = full_description
                findings.append(finding)

        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse Nuclei JSON output: {str(e)}")
        except Exception as e:
            raise Exception(f"Error parsing Nuclei results: {str(e)}")

        return findings
