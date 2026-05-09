"""Nmap plugin for network scanning."""
from core.plugins import PluginBase
from typing import Dict, Any, List
import subprocess
import xml.etree.ElementTree as ET
import tempfile
import os


class NmapPlugin(PluginBase):
    """Nmap network scanner plugin."""
    
    name = "nmap"
    version = "1.0.0"
    description = "Network discovery and security auditing with Nmap"
    capabilities = ["network_scan", "port_scan", "service_detection"]
    
    def validate_config(self) -> None:
        """Validate plugin configuration."""
        if 'targets' not in self.config and 'target' not in self.config:
            raise ValueError("Parameter 'targets' or 'target' is required")
    
    def run(self) -> Dict[str, Any]:
        """Execute Nmap scan."""
        targets = self.config.get('targets') or self.config.get('target')
        if isinstance(targets, list):
            targets = ' '.join(targets)
        
        ports = self.config.get('ports', '1-1000')
        scan_type = self.config.get('scan_type', '-sV')
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
            xml_output_path = f.name
        
        try:
            cmd = ['nmap', scan_type, '-p', ports, '-oX', xml_output_path, targets]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            
            with open(xml_output_path, 'r') as f:
                raw_output = f.read()
            
            return {
                'raw_output': raw_output,
                'artifacts': [xml_output_path],
                'metadata': {'exit_code': result.returncode, 'command': ' '.join(cmd)}
            }
            
        except subprocess.TimeoutExpired:
            raise Exception("Nmap scan timed out after 10 minutes")
        except Exception as e:
            if os.path.exists(xml_output_path):
                os.remove(xml_output_path)
            raise e
    
    def parse_output(self, raw_output: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse Nmap XML output into findings."""
        findings = []
        
        try:
            root = ET.fromstring(raw_output)
            
            for host in root.findall('host'):
                address_elem = host.find('address')
                if address_elem is None:
                    continue
                host_ip = address_elem.get('addr')
                
                hostnames = host.find('hostnames')
                hostname = None
                if hostnames is not None:
                    hostname_elem = hostnames.find('hostname')
                    if hostname_elem is not None:
                        hostname = hostname_elem.get('name')
                
                ports = host.find('ports')
                if ports is None:
                    continue
                
                for port in ports.findall('port'):
                    portid = port.get('portid')
                    protocol = port.get('protocol')
                    
                    state = port.find('state')
                    if state is None or state.get('state') != 'open':
                        continue
                    
                    service = port.find('service')
                    service_name = service.get('name', 'unknown') if service is not None else 'unknown'
                    service_product = service.get('product', '') if service is not None else ''
                    service_version = service.get('version', '') if service is not None else ''
                    
                    title = f"Open port {portid}/{protocol} on {host_ip}"
                    if hostname:
                        title += f" ({hostname})"
                    
                    description = f"Port {portid}/{protocol} is open"
                    if service_name != 'unknown':
                        description += f" running {service_name}"
                        if service_product:
                            description += f" ({service_product}"
                            if service_version:
                                description += f" {service_version}"
                            description += ")"
                    
                    severity = self._determine_severity(portid, service_name)
                    
                    findings.append({
                        'title': title,
                        'severity': severity,
                        'description': description,
                        'remediation': f"Review if port {portid} needs to be exposed. Consider firewall rules.",
                        'cvss_score': None,
                        'cve_id': None
                    })
        
        except ET.ParseError as e:
            raise Exception(f"Failed to parse Nmap XML output: {e}")
        
        return findings
    
    def _determine_severity(self, port: str, service: str) -> str:
        """Determine severity based on port and service."""
        high_risk_ports = ['22', '23', '3389', '445', '139', '21']
        medium_risk_ports = ['80', '443', '8080', '8443']
        
        if port in high_risk_ports:
            return 'high'
        elif port in medium_risk_ports:
            return 'medium'
        else:
            return 'low'
