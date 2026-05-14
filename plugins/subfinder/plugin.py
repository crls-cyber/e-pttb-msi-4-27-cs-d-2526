"""
Subfinder Plugin - DNS Subdomain Enumeration
Discovers subdomains using passive sources
"""
from core.plugins.base import PluginBase
from typing import Dict, Any, List
import subprocess
import json
import logging

logger = logging.getLogger(__name__)


class SubfinderPlugin(PluginBase):
    """Subfinder passive subdomain enumeration plugin."""
    
    name = "subfinder"
    version = "1.0.0"
    description = "Passive subdomain enumeration using multiple sources"
    capabilities = ["osint", "recon"]
    
    required_params = ["domain"]
    optional_params = ["sources", "timeout", "max_results"]
    
    def validate_config(self) -> None:
        """Validate plugin configuration."""
        if "domain" not in self.config:
            raise ValueError("Missing required parameter: domain")

        domain = self.config["domain"]
        
        if not isinstance(domain, str) or not domain:
            raise ValueError("Parameter 'domain' must be a non-empty string")
        
        # Basic domain validation
        if not self._is_valid_domain(domain):
            raise ValueError(f"Invalid domain format: {domain}")
    
    def run(self) -> Dict[str, Any]:
        """Execute Subfinder."""
        domain = self.config["domain"]
        timeout = self.config.get("timeout", 300)
        max_results = self.config.get("max_results", 1000)
        
        logger.info(f"Running Subfinder on domain: {domain}")
        
        # Build command
        cmd = [
            "subfinder",
            "-d", domain,
            "-json",  # JSON output
            "-silent",  # Suppress banner
            "-max-time", str(timeout),
        ]
        
        # Add sources if specified
        if "sources" in self.config:
            sources = self.config["sources"]
            if isinstance(sources, list):
                cmd.extend(["-sources", ",".join(sources)])
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False
            )
            
            logger.info(f"Subfinder completed with return code: {result.returncode}")
            
            return {
                "raw_output": result.stdout,
                "artifacts": [],
                "metadata": {
                    "stderr": result.stderr,
                    "return_code": result.returncode,
                    "command": " ".join(cmd)
                }
            }
        
        except subprocess.TimeoutExpired:
            raise Exception(f"Subfinder execution timeout after {timeout}s")
        
        except Exception as e:
            raise Exception(f"Subfinder execution failed: {str(e)}")
    
    def parse_output(self, raw_output: Any) -> List[Dict[str, Any]]:
        """Parse Subfinder JSON output into findings."""
        findings = []
    
        # raw_output is already a string (stdout from run())
        if not raw_output or not isinstance(raw_output, str):
            logger.warning("Subfinder returned no output or invalid format")
            return findings
    
        stdout = raw_output
        
        # Parse JSON lines
        subdomains = []
        for line in stdout.strip().split("\n"):
            if not line.strip():
                continue
            
            try:
                data = json.loads(line)
                subdomain = data.get("host")
                source = data.get("source", "unknown")
                
                if subdomain:
                    subdomains.append({"subdomain": subdomain, "source": source})
            
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse JSON line: {line}")
                continue
        
        if not subdomains:
            logger.info("No subdomains found")
            return findings
        
        # Group by source
        sources_summary = {}
        for item in subdomains:
            source = item["source"]
            sources_summary[source] = sources_summary.get(source, 0) + 1
        
        # Create findings
        findings.append({
            "title": f"Discovered {len(subdomains)} subdomains",
            "severity": "info",
            "description": (
                f"Subfinder discovered {len(subdomains)} unique subdomains:\n\n"
                f"Sources breakdown:\n" +
                "\n".join([f"- {src}: {count} subdomains" for src, count in sources_summary.items()]) +
                f"\n\nSubdomains:\n" +
                "\n".join([f"- {item['subdomain']} (via {item['source']})" for item in subdomains[:50]])
            ),
            "remediation": "Review discovered subdomains for unintended exposure or forgotten assets.",
            "raw_data": subdomains
        })
        
        logger.info(f"Created {len(findings)} findings from {len(subdomains)} subdomains")
        return findings
    
    def _is_valid_domain(self, domain: str) -> bool:
        """Check if string is a valid domain."""
        import re
        # Basic domain regex (not exhaustive)
        pattern = r'^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$'
        return bool(re.match(pattern, domain))
