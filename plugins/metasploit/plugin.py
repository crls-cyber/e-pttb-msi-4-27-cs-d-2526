"""
Metasploit Plugin - Exploitation Framework
⚠️ Metasploit requires direct access to the host system and cannot run inside Docker.
Run msfconsole directly on Kali, then upload the log file via the upload page.
See: /en/jobs/new/metasploit for instructions.
"""
from core.plugins.base import PluginBase
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class MetasploitPlugin(PluginBase):
    """Metasploit plugin — redirects to manual execution + log upload."""

    name = "metasploit"
    version = "2.0.0"
    description = "Active exploitation via Metasploit Framework (run on Kali, upload log)"
    capabilities = ["exploitation", "payload_delivery", "session_management"]

    required_params = ["target"]
    optional_params = []

    def validate_config(self) -> None:
        """Validate plugin configuration."""
        pass

    def run(self) -> Dict[str, Any]:
        """Metasploit runs on Kali host — not inside Docker."""
        raise NotImplementedError(
            "Metasploit cannot run inside Docker. "
            "Run msfconsole directly on Kali and upload the log file. "
            "See /en/jobs/new/metasploit for step-by-step instructions."
        )

    def parse_output(self, raw_output: Any) -> List[Dict[str, Any]]:
        """Not used — parsing is done by MetasploitParser (external upload)."""
        return []
