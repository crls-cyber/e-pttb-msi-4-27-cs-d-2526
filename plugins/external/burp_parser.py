"""Burp Suite XML report parser."""
from plugins.external.base import ExternalParserBase
from typing import Dict, Any, List
import xml.etree.ElementTree as ET
import os
import logging

logger = logging.getLogger(__name__)


class BurpParser(ExternalParserBase):
    """Parse Burp Suite XML export files."""

    name = "burp"
    supported_extensions = ['.xml']
    max_file_size_mb = 50  # 50MB max

    # Severity mapping from Burp to our system
    SEVERITY_MAP = {
        'high': 'high',
        'medium': 'medium',
        'low': 'low',
        'information': 'info',
        'info': 'info',
        'false positive': 'info',
    }

    def parse(self, filepath: str, user_id: str) -> Dict[str, Any]:
        """Parse Burp Suite XML export file."""
        self.validate_file(filepath)

        findings = []
        metadata = {
            'filename': os.path.basename(filepath),
            'size_mb': round(os.path.getsize(filepath) / (1024 * 1024), 2),
            'parser': 'burp'
        }

        try:
            tree = ET.parse(filepath)
            root = tree.getroot()

            # Support both <issues> and <OWASPZAPReport> root elements
            # Burp exports use <issues> as root
            if root.tag != 'issues':
                raise ValueError(
                    f"Invalid Burp Suite XML format. Expected root element <issues>, got <{root.tag}>. "
                    "Export from Burp Suite: Target → Site map → right-click → Issues → Report issues → XML"
                )

            # Get Burp version and export time from attributes
            burp_version = root.get('burpVersion', 'unknown')
            export_time = root.get('exportTime', 'unknown')
            metadata['burp_version'] = burp_version
            metadata['export_time'] = export_time

            # Parse each issue
            issues = root.findall('issue')
            metadata['total_issues'] = len(issues)

            logger.info(f"Parsing {len(issues)} Burp Suite issues from {metadata['filename']}")

            severity_counts = {'high': 0, 'medium': 0, 'low': 0, 'info': 0}

            for issue in issues:
                finding = self._parse_issue(issue)
                if finding:
                    findings.append(finding)
                    sev = finding['severity']
                    if sev in severity_counts:
                        severity_counts[sev] += 1

            # Build summary
            summary = (
                f"Burp Suite scan: {len(issues)} issues found — "
                f"{severity_counts['high']} High, "
                f"{severity_counts['medium']} Medium, "
                f"{severity_counts['low']} Low, "
                f"{severity_counts['info']} Info"
            )
            metadata['severity_counts'] = severity_counts

            return {
                'findings': findings,
                'metadata': metadata,
                'summary': summary
            }

        except ET.ParseError as e:
            raise ValueError(f"Invalid XML file: {str(e)}")
        except Exception as e:
            raise Exception(f"Burp Suite parsing failed: {str(e)}")

    def _parse_issue(self, issue: ET.Element) -> Dict[str, Any]:
        """Parse a single Burp Suite issue into a finding."""
        try:
            # Extract basic fields
            name = self._get_text(issue, 'name') or 'Unknown vulnerability'
            severity_raw = self._get_text(issue, 'severity') or 'information'
            severity = self.SEVERITY_MAP.get(severity_raw.lower(), 'info')
            confidence = self._get_text(issue, 'confidence') or 'Tentative'

            # Extract host and path
            host_el = issue.find('host')
            host = host_el.text if host_el is not None else 'unknown'
            host_ip = host_el.get('ip', '') if host_el is not None else ''
            path = self._get_text(issue, 'path') or '/'

            # Build URL
            url = f"{host}{path}" if path != '/' else host

            # Extract descriptions
            issue_background = self._get_text(issue, 'issueBackground') or ''
            issue_detail = self._get_text(issue, 'issueDetail') or ''
            remediation = self._get_text(issue, 'remediationBackground') or \
                         self._get_text(issue, 'remediationDetail') or \
                         'Review Burp Suite documentation for remediation guidance.'

            # Clean HTML tags from descriptions
            issue_background = self._strip_html(issue_background)
            issue_detail = self._strip_html(issue_detail)
            remediation = self._strip_html(remediation)

            # Build description
            description_parts = []
            if issue_detail:
                description_parts.append(issue_detail)
            if issue_background:
                description_parts.append(f"\nBackground:\n{issue_background}")
            description_parts.append(f"\nURL: {url}")
            description_parts.append(f"Confidence: {confidence}")
            if host_ip:
                description_parts.append(f"IP: {host_ip}")

            description = '\n'.join(description_parts) if description_parts else f"Vulnerability detected at {url}"

            # Extract issue type ID (Burp internal ID)
            issue_type = self._get_text(issue, 'type') or ''

            return {
                'title': f"{name} — {url}",
                'severity': severity,
                'description': description,
                'remediation': remediation,
                'metadata': {
                    'burp_issue_type': issue_type,
                    'host': host,
                    'path': path,
                    'confidence': confidence,
                    'url': url
                }
            }

        except Exception as e:
            logger.warning(f"Failed to parse Burp issue: {str(e)}")
            return None

    def _get_text(self, element: ET.Element, tag: str) -> str:
        """Safely get text content of a child element."""
        child = element.find(tag)
        if child is not None and child.text:
            return child.text.strip()
        return ''

    def _strip_html(self, text: str) -> str:
        """Remove basic HTML tags from text."""
        if not text:
            return ''
        import re
        # Remove HTML tags
        clean = re.sub(r'<[^>]+>', ' ', text)
        # Remove multiple spaces
        clean = re.sub(r'\s+', ' ', clean).strip()
        # Decode common HTML entities
        clean = clean.replace('&lt;', '<').replace('&gt;', '>') \
                     .replace('&amp;', '&').replace('&quot;', '"') \
                     .replace('&#39;', "'").replace('&nbsp;', ' ')
        return clean
