"""
WhatWeb Plugin - Web Technology Fingerprinting
Identifies web technologies, CMS, frameworks, versions
"""
from core.plugins.base import PluginBase
from typing import Dict, Any, List
import subprocess
import json
import logging

logger = logging.getLogger(__name__)


class WhatWebPlugin(PluginBase):
    """WhatWeb web technology fingerprinting plugin."""
    
    name = "whatweb"
    version = "1.0.0"
    description = "Web technology fingerprinting (CMS, frameworks, servers)"
    capabilities = ["web_scan", "recon"]
    
    required_params = ["target"]
    optional_params = ["aggression", "plugins", "timeout"]
    
    def validate_config(self) -> None:
        """Validate plugin configuration."""
        if "target" not in self.config:
            raise ValueError("Missing required parameter: target")
        
        target = self.config["target"]
        if not isinstance(target, str) or not target:
            raise ValueError("Parameter 'target' must be a non-empty string")
        
        # Ensure target has protocol
        if not target.startswith(("http://", "https://")):
            raise ValueError(f"Target must start with http:// or https://: {target}")
    
    def run(self) -> Dict[str, Any]:
        """Execute WhatWeb."""
        target = self.config["target"]
        aggression = self.config.get("aggression", 1)  # 1=stealthy, 3=aggressive
        timeout = self.config.get("timeout", 60)
        
        logger.info(f"Running WhatWeb on target: {target}")
        
        # Build command
        cmd = [
            "whatweb",
            target,
            "--log-json=-",  # JSON to stdout (cleaner format)
            f"--aggression={aggression}",
            "--color=never",
            "--no-errors",
        ]
        
        # Add custom plugins if specified
        if "plugins" in self.config:
            plugins = self.config["plugins"]
            if isinstance(plugins, list):
                cmd.extend(["-p", ",".join(plugins)])
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False
            )
            
            logger.info(f"WhatWeb completed with return code: {result.returncode}")
            
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
            raise Exception(f"WhatWeb execution timeout after {timeout}s")
        
        except Exception as e:
            raise Exception(f"WhatWeb execution failed: {str(e)}")
    
    def parse_output(self, raw_output: Any) -> List[Dict[str, Any]]:
        """Parse WhatWeb JSON output into findings."""
        findings = []
        
        if not raw_output or not isinstance(raw_output, str):
            logger.warning("WhatWeb returned no output or invalid format")
            return findings
        
        stdout = raw_output
        
        if not stdout.strip():
            logger.warning("WhatWeb returned empty output")
            return findings
        
        # Parse JSON lines
        technologies = {}
        target_url = None
        
        for line in stdout.strip().split("\n"):
            if not line.strip() or line.strip() in ["[", "]"] or not line.strip().startswith("{"):
                continue
            
            try:
                data = json.loads(line)
                target_url = data.get("target")
                plugins_data = data.get("plugins", {})
                
                # Extract technologies
                for plugin_name, plugin_info in plugins_data.items():
                    if isinstance(plugin_info, dict):
                        version = plugin_info.get("version", [""])[0] if "version" in plugin_info else ""
                        string_match = plugin_info.get("string", [""])[0] if "string" in plugin_info else ""
                        
                        tech_info = {
                            "name": plugin_name,
                            "version": version,
                            "details": string_match
                        }
                        
                        # Categorize technology
                        category = self._categorize_tech(plugin_name)
                        
                        if category not in technologies:
                            technologies[category] = []
                        technologies[category].append(tech_info)
            
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse JSON line: {line}")
                continue
        
        if not technologies:
            logger.info("No technologies identified")
            return findings
        
        # Create findings by category
        for category, techs in technologies.items():
            description_lines = [f"**{category.upper()}**\n"]
            
            for tech in techs:
                tech_line = f"- {tech['name']}"
                if tech['version']:
                    tech_line += f" {tech['version']}"
                if tech['details']:
                    tech_line += f" ({tech['details']})"
                description_lines.append(tech_line)
            
            # Determine severity based on sensitive tech detection
            severity = "info"
            if self._is_sensitive_tech(techs):
                severity = "low"
            
            findings.append({
                "title": f"Identified {len(techs)} {category} technologies",
                "severity": severity,
                "description": "\n".join(description_lines),
                "remediation": "Review exposed technologies for known vulnerabilities. Consider hiding version information.",
                "raw_data": {"category": category, "technologies": techs}
            })
        
        # Create summary finding
        total_techs = sum(len(techs) for techs in technologies.values())
        summary_lines = [f"WhatWeb identified {total_techs} technologies on {target_url}:\n"]
        for category, techs in technologies.items():
            summary_lines.append(f"- {category.capitalize()}: {len(techs)} items")
        
        findings.insert(0, {
            "title": f"Web fingerprinting completed: {total_techs} technologies identified",
            "severity": "info",
            "description": "\n".join(summary_lines),
            "remediation": "Review all identified technologies for security implications.",
            "raw_data": {"summary": technologies}
        })
        
        logger.info(f"Created {len(findings)} findings from {total_techs} technologies")
        return findings
    
    def _categorize_tech(self, plugin_name: str) -> str:
        """Categorize technology by plugin name."""
        plugin_lower = plugin_name.lower()
        
        # CMS
        if any(cms in plugin_lower for cms in ["wordpress", "joomla", "drupal", "magento", "prestashop"]):
            return "cms"
        
        # Web servers
        if any(server in plugin_lower for server in ["apache", "nginx", "iis", "lighttpd", "tomcat"]):
            return "web_server"
        
        # Programming languages
        if any(lang in plugin_lower for lang in ["php", "python", "ruby", "java", "asp", "jsp"]):
            return "language"
        
        # JavaScript frameworks
        if any(js in plugin_lower for js in ["jquery", "react", "angular", "vue", "bootstrap"]):
            return "javascript"
        
        # Databases
        if any(db in plugin_lower for db in ["mysql", "postgresql", "mongodb", "redis"]):
            return "database"
        
        # Analytics & Tracking
        if any(analytics in plugin_lower for analytics in ["google-analytics", "analytics", "tracking"]):
            return "analytics"
        
        return "other"
    
    def _is_sensitive_tech(self, techs: List[Dict[str, str]]) -> bool:
        """Check if technologies reveal sensitive information."""
        for tech in techs:
            # Version information exposed
            if tech.get("version"):
                return True
            
            # Admin panels or login pages
            name_lower = tech["name"].lower()
            if any(sensitive in name_lower for sensitive in ["admin", "login", "phpmyadmin", "cpanel"]):
                return True
        
        return False
