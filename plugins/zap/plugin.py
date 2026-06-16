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
    version = "1.1.0"
    description = "Web security scanner: spider, active scan, XSS, SQLi, CSRF detection"
    capabilities = ["web_scan", "active_scan", "vulnerability_detection"]

    required_params = ["target"]
    optional_params = ["scan_mode", "api_key", "timeout", "cookie"]

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
        scan_mode = self.config.get("scan_mode", "active")
        api_key = self.config.get("api_key", "changeme123")
        timeout = self.config.get("timeout", 600)
        cookie = self.config.get("cookie", "")

        logger.info(f"Starting ZAP {scan_mode} scan on {target}")

        zap_port = 8090
        zap_process = self._start_zap_daemon(zap_port, api_key)

        try:
            if not self._wait_for_zap(zap_port, api_key):
                raise Exception("ZAP daemon failed to start")

            # Set authenticated session if cookie provided
            if cookie:
                self._set_httpsession(target, zap_port, api_key, cookie)
                logger.info("Authenticated session configured via httpsessions")

            # Access target URL to seed ZAP context
            try:
                requests.get(
                    f"http://localhost:{zap_port}/JSON/core/action/accessUrl/",
                    params={"apikey": api_key, "url": target}
                )
            except Exception:
                pass
            spider_delay = self.config.get('spider_delay', 5)
            time.sleep(spider_delay)

            # Spider the target
            spider_id = self._spider_target(target, zap_port, api_key)
            self._wait_for_spider(spider_id, zap_port, api_key)

            # Active scan if requested
            if scan_mode == "active":
                scan_id = self._active_scan(target, zap_port, api_key)
                self._wait_for_scan(scan_id, zap_port, api_key, timeout)

            # Get alerts
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
                    "zap_version": "2.17.0",
                    "authenticated": bool(cookie)
                }
            }

        finally:
            self._stop_zap_daemon(zap_process)

    def parse_output(self, raw_output: Any) -> List[Dict[str, Any]]:
        """Parse ZAP alerts into findings."""
        findings = []

        if not isinstance(raw_output, dict):
            return findings

        alerts = raw_output.get("alerts", [])

        severity_map = {
            # Numeric format (older ZAP versions)
            "3": "critical",
            "2": "high",
            "1": "medium",
            "0": "info",
            # String format (ZAP 2.x+)
            "High": "high",
            "Medium": "medium",
            "Low": "low",
            "Informational": "info",
            "False Positive": "info",
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

    def _set_httpsession(self, target: str, port: int, api_key: str, cookie: str):
        """Configure authenticated session using ZAP httpsessions API."""
        base = f"http://localhost:{port}"
        session_name = "authenticated"

        try:
            # Parse cookie string into name=value pairs
            cookie_pairs = [c.strip() for c in cookie.split(';') if '=' in c]

            # Create empty session
            requests.get(
                f"{base}/JSON/httpsessions/action/createEmptySession/",
                params={"apikey": api_key, "site": target, "session": session_name}
            )

            # Set each cookie token in the session
            for pair in cookie_pairs:
                name, _, value = pair.partition('=')
                requests.get(
                    f"{base}/JSON/httpsessions/action/setSessionTokenValue/",
                    params={
                        "apikey": api_key,
                        "site": target,
                        "session": session_name,
                        "tokenName": name.strip(),
                        "tokenValue": value.strip()
                    }
                )
                logger.info(f"Set session token: {name.strip()}")

            # Set as active session
            requests.get(
                f"{base}/JSON/httpsessions/action/setActiveSession/",
                params={"apikey": api_key, "site": target, "session": session_name}
            )

            logger.info(f"Active session '{session_name}' configured with {len(cookie_pairs)} tokens")

        except Exception as e:
            logger.warning(f"Failed to configure httpsession: {e}")

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

        for _ in range(max_wait):
            try:
                response = requests.get(
                    f"{base_url}/JSON/core/view/version/",
                    params={"apikey": api_key},
                    timeout=2
                )
                if response.status_code == 200:
                    logger.info("ZAP daemon ready")
                    return True
            except Exception:
                pass

            time.sleep(1)

        return False

    def _spider_target(self, target: str, port: int, api_key: str) -> str:
        """Start spider scan."""
        response = requests.get(
            f"http://localhost:{port}/JSON/spider/action/scan/",
            params={"apikey": api_key, "url": target}
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
                params={"apikey": api_key, "scanId": spider_id}
            )

            status = int(response.json().get("status", "0"))
            if status >= 100:
                logger.info("Spider completed")
                break

            time.sleep(5)

    def _active_scan(self, target: str, port: int, api_key: str) -> str:
        """Start active scan."""
        response = requests.get(
            f"http://localhost:{port}/JSON/ascan/action/scan/",
            params={"apikey": api_key, "url": target}
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
                params={"apikey": api_key, "scanId": scan_id}
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
        alerts = response.json().get("alerts", [])
        # Log risk distribution for debugging
        risk_counts = {}
        for a in alerts:
            risk = str(a.get("risk", "?"))
            risk_counts[risk] = risk_counts.get(risk, 0) + 1
        logger.info(f"Alerts risk distribution: {risk_counts}")
        if alerts:
            logger.info(f"Sample alert keys: {list(alerts[0].keys())}")
            logger.info(f"Sample alert risk value: {alerts[0].get('risk')} (type: {type(alerts[0].get('risk')).__name__})")
        return alerts

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
        except Exception:
            process.kill()

        logger.info("ZAP daemon stopped")
