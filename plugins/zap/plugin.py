"""
OWASP ZAP Plugin - Web Application Security Scanner
Performs active/passive scanning, spidering, and vulnerability detection
"""
from core.plugins.base import PluginBase
from typing import Dict, Any, List
import subprocess
import time
import requests
import logging
import os

logger = logging.getLogger(__name__)


class ZapPlugin(PluginBase):
    """OWASP ZAP web security scanner plugin."""
    
    name = "zap"
    version = "1.0.0"
    description = "Web security scanner: spider, active scan, XSS, SQLi, CSRF detection"
    capabilities = ["web_scan", "active_scan", "vulnerability_detection"]
    
    required_params = ["target"]
    optional_params = ["scan_mode", "api_key", "timeout"]
    
    def validate_config(self) -> None:
        """Validate plugin configuration."""
        if "target" not in self.config:
            raise ValueError("Missing required parameter: target (URL)")
        
        target = self.config["target"]
        if not target.startswith(("http://", "https://")):
            raise ValueError("Target must be a valid HTTP/HTTPS URL")
    
    def run(self) -> Dict[str, Any]:
        """Execute ZAP scan."""
        target = self.config["target"]
        scan_mode = self.config.get("scan_mode", "active")  # active or passive
        api_key = self.config.get("api_key", "changeme123")
        timeout = self.config.get("timeout", 600)  # 10 minutes default
        
        logger.info(f"Starting ZAP {scan_mode} scan on {target}")
        
        # Start ZAP daemon
        zap_port = 8090
        zap_process = self._start_zap_daemon(zap_port, api_key)
        
        try:
            # Wait for ZAP to be ready
            if not self._wait_for_zap(zap_port, api_key):
                raise Exception("ZAP daemon failed to start")
            
            # Spider the target
            spider_id = self._spider_target(target, zap_port, api_key)
            self._wait_for_spider(spider_id, zap_port, api_key)
            
            # Active scan if requested
            if scan_mode == "active":
                scan_id = self._active_scan(target, zap_port, api_key)
                self._wait_for_scan(scan_id, zap_port, api_key, timeout)
            
            # Get alerts (findings)
            alerts = self._get_alerts(zap_port, api_key)
            
            # Generate report
            report_path = f"/tmp/zap_report_{int(time.time())}.html"
            self._generate_report(zap_port, api_key, report_path)
            
            return {
                "raw_output": {"alerts": alerts},
                "artifacts": [report_path] if os.path.exists(report_path) else [],
                "metadata": {
                    "target": target,
                    "scan_mode": scan_mode,
                    "alerts_count": len(alerts),
                    "zap_version": "2.17.0"
                }
            }
        
        finally:
            # Stop ZAP daemon
            self._stop_zap_daemon(zap_process)
    
    def parse_output(self, raw_output: Any) -> List[Dict[str, Any]]:
        """Parse ZAP alerts into findings."""
        findings = []
        
        if not isinstance(raw_output, dict):
            return findings
        
        alerts = raw_output.get("alerts", [])
        
        severity_map = {
            "3": "critical",  # High
            "2": "high",      # Medium
            "1": "medium",    # Low
            "0": "info"       # Informational
        }
        
        for alert in alerts:
            severity = severity_map.get(str(alert.get("risk", "0")), "info")
            
            findings.append({
                "title": alert.get("alert", "Unknown vulnerability"),
                "severity": severity,
                "description": (
                    f"{alert.get('description', 'No description')}\n\n"
                    f"URL: {alert.get('url', 'N/A')}\n"
                    f"Parameter: {alert.get('param', 'N/A')}\n"
                    f"Evidence: {alert.get('evidence', 'N/A')}"
                ),
                "cve_id": alert.get("cweid"),
                "remediation": alert.get("solution", "Review security best practices"),
                "raw_data": alert
            })
        
        logger.info(f"Parsed {len(findings)} findings from ZAP alerts")
        return findings
    
    def _start_zap_daemon(self, port: int, api_key: str) -> subprocess.Popen:
        """Start ZAP in daemon mode."""
        cmd = [
            "zap.sh",
            "-daemon",
            "-port", str(port),
            "-config", f"api.key={api_key}",
            "-config", "api.addrs.addr.name=.*",
            "-config", "api.addrs.addr.regex=true"
        ]
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        logger.info(f"ZAP daemon starting on port {port}")
        return process
    
    def _wait_for_zap(self, port: int, api_key: str, max_wait: int = 60) -> bool:
        """Wait for ZAP daemon to be ready."""
        base_url = f"http://localhost:{port}"
        
        for i in range(max_wait):
            try:
                response = requests.get(
                    f"{base_url}/JSON/core/view/version/",
                    params={"apikey": api_key},
                    timeout=2
                )
                if response.status_code == 200:
                    logger.info("ZAP daemon ready")
                    return True
            except:
                pass
            
            time.sleep(1)
        
        return False
    
    def _spider_target(self, target: str, port: int, api_key: str) -> str:
        """Start spider scan."""
        response = requests.get(
            f"http://localhost:{port}/JSON/spider/action/scan/",
            params={
                "apikey": api_key,
                "url": target
            }
        )
        
        data = response.json()
        spider_id = data.get("scan", "0")
        logger.info(f"Spider started: ID {spider_id}")
        return spider_id
    
    def _wait_for_spider(self, spider_id: str, port: int, api_key: str):
        """Wait for spider to complete."""
        while True:
            response = requests.get(
                f"http://localhost:{port}/JSON/spider/view/status/",
                params={
                    "apikey": api_key,
                    "scanId": spider_id
                }
            )
            
            status = int(response.json().get("status", "0"))
            if status >= 100:
                logger.info("Spider completed")
                break
            
            time.sleep(2)
    
    def _active_scan(self, target: str, port: int, api_key: str) -> str:
        """Start active scan."""
        response = requests.get(
            f"http://localhost:{port}/JSON/ascan/action/scan/",
            params={
                "apikey": api_key,
                "url": target
            }
        )
        
        data = response.json()
        scan_id = data.get("scan", "0")
        logger.info(f"Active scan started: ID {scan_id}")
        return scan_id
    
    def _wait_for_scan(self, scan_id: str, port: int, api_key: str, timeout: int):
        """Wait for active scan to complete."""
        start_time = time.time()
        
        while True:
            if time.time() - start_time > timeout:
                logger.warning("Active scan timeout reached")
                break
            
            response = requests.get(
                f"http://localhost:{port}/JSON/ascan/view/status/",
                params={
                    "apikey": api_key,
                    "scanId": scan_id
                }
            )
            
            status = int(response.json().get("status", "0"))
            if status >= 100:
                logger.info("Active scan completed")
                break
            
            time.sleep(5)
    
    def _get_alerts(self, port: int, api_key: str) -> List[Dict]:
        """Retrieve all alerts."""
        response = requests.get(
            f"http://localhost:{port}/JSON/core/view/alerts/",
            params={"apikey": api_key}
        )
        
        return response.json().get("alerts", [])
    
    def _generate_report(self, port: int, api_key: str, output_path: str):
        """Generate HTML report."""
        response = requests.get(
            f"http://localhost:{port}/OTHER/core/other/htmlreport/",
            params={"apikey": api_key}
        )
        
        with open(output_path, 'wb') as f:
            f.write(response.content)
        
        logger.info(f"Report saved to {output_path}")
    
    def _stop_zap_daemon(self, process: subprocess.Popen):
        """Stop ZAP daemon."""
        try:
            process.terminate()
            process.wait(timeout=10)
        except:
            process.kill()
        
        logger.info("ZAP daemon stopped")
