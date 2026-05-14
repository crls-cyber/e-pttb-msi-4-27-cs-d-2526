"""
Aircrack-ng Plugin - WiFi Security Auditing
Captures WiFi packets and cracks WPA/WPA2 passwords

⚠️ PREREQUISITES:
- WiFi adapter with monitor mode support (e.g., Alfa AWUS036ACH)
- Adapter must be passed through to the VM or running on native Linux
- aircrack-ng suite installed

⚠️ LEGAL WARNING:
Only test on networks you own or have explicit written permission to audit.
Unauthorized WiFi cracking is illegal in most jurisdictions.
"""
from core.plugins.base import PluginBase
from typing import Dict, Any, List
import subprocess
import os
import re
import logging

logger = logging.getLogger(__name__)


class AircrackPlugin(PluginBase):
    """Aircrack-ng WiFi auditing plugin."""
    
    name = "aircrack"
    version = "1.0.0"
    description = "WiFi security auditing: capture handshakes and crack WPA/WPA2"
    capabilities = ["wireless", "password_cracking"]
    
    required_params = ["interface", "target_bssid"]
    optional_params = ["channel", "wordlist", "timeout", "capture_time"]
    
    def validate_config(self) -> None:
        """Validate plugin configuration."""
        if "interface" not in self.config:
            raise ValueError("Missing required parameter: interface (e.g., wlan0)")
        
        if "target_bssid" not in self.config:
            raise ValueError("Missing required parameter: target_bssid (e.g., AA:BB:CC:DD:EE:FF)")
        
        interface = self.config["interface"]
        bssid = self.config["target_bssid"]
        
        # Validate BSSID format
        if not self._is_valid_bssid(bssid):
            raise ValueError(f"Invalid BSSID format: {bssid}")
        
        # Check if interface exists
        if not os.path.exists(f"/sys/class/net/{interface}"):
            raise ValueError(
                f"WiFi interface '{interface}' not found. "
                f"Prerequisites: WiFi adapter with monitor mode support required."
            )
    
    def run(self) -> Dict[str, Any]:
        """Execute Aircrack-ng WiFi audit."""
        interface = self.config["interface"]
        target_bssid = self.config["target_bssid"]
        channel = self.config.get("channel", None)
        wordlist = self.config.get("wordlist", "/usr/share/wordlists/rockyou.txt")
        capture_time = self.config.get("capture_time", 300)  # 5 minutes default
        
        logger.info(f"Running Aircrack-ng on interface: {interface}, target: {target_bssid}")
        
        artifacts = []
        metadata = {}
        
        try:
            # Step 1: Enable monitor mode
            monitor_iface = self._enable_monitor_mode(interface)
            metadata['monitor_interface'] = monitor_iface
            
            # Step 2: Capture handshake
            capture_file = f"/tmp/aircrack_capture_{target_bssid.replace(':', '')}"
            handshake_captured = self._capture_handshake(
                monitor_iface,
                target_bssid,
                channel,
                capture_file,
                capture_time
            )
            
            if handshake_captured:
                artifacts.append(f"{capture_file}-01.cap")
                metadata['handshake_captured'] = True
                
                # Step 3: Crack password
                if os.path.exists(wordlist):
                    password = self._crack_password(capture_file, target_bssid, wordlist)
                    if password:
                        metadata['password_cracked'] = True
                        metadata['password'] = password
                    else:
                        metadata['password_cracked'] = False
                else:
                    logger.warning(f"Wordlist not found: {wordlist}")
                    metadata['password_cracked'] = False
                    metadata['wordlist_missing'] = True
            else:
                metadata['handshake_captured'] = False
            
            # Step 4: Disable monitor mode
            self._disable_monitor_mode(monitor_iface, interface)
            
            return {
                "raw_output": metadata,
                "artifacts": artifacts,
                "metadata": metadata
            }
        
        except Exception as e:
            # Cleanup on error
            if 'monitor_iface' in metadata:
                try:
                    self._disable_monitor_mode(metadata['monitor_iface'], interface)
                except:
                    pass
            
            raise Exception(f"Aircrack-ng execution failed: {str(e)}")
    
    def parse_output(self, raw_output: Any) -> List[Dict[str, Any]]:
        """Parse Aircrack-ng output into findings."""
        findings = []
        
        if not isinstance(raw_output, dict):
            logger.warning("Invalid raw_output format")
            return findings
        
        metadata = raw_output
        
        # Finding 1: Handshake capture result
        if metadata.get('handshake_captured'):
            findings.append({
                'title': "WPA/WPA2 handshake captured successfully",
                'severity': 'high',
                'description': (
                    f"Successfully captured a 4-way handshake from target BSSID.\n\n"
                    f"This handshake can be used for offline password cracking. "
                    f"The security of the network depends entirely on password strength."
                ),
                'remediation': (
                    "Use a strong, random WPA2/WPA3 password (20+ characters). "
                    "Consider upgrading to WPA3 if supported."
                ),
                'raw_data': {'capture_file': metadata.get('artifacts', [])}
            })
        else:
            findings.append({
                'title': "Failed to capture WPA/WPA2 handshake",
                'severity': 'info',
                'description': (
                    "No handshake captured within the timeout period. "
                    "This may indicate:\n"
                    "- No clients connected to the target network\n"
                    "- Insufficient capture time\n"
                    "- Target out of range"
                ),
                'remediation': "Increase capture_time or wait for client activity.",
                'raw_data': metadata
            })
        
        # Finding 2: Password cracking result
        if metadata.get('password_cracked'):
            password = metadata.get('password', 'N/A')
            findings.append({
                'title': f"WiFi password cracked: {password}",
                'severity': 'critical',
                'description': (
                    f"Successfully cracked the WPA/WPA2 password: **{password}**\n\n"
                    f"This demonstrates the network is vulnerable to dictionary attacks. "
                    f"The password was found in a common wordlist."
                ),
                'remediation': (
                    "Immediately change the WiFi password to a strong, random passphrase. "
                    "Minimum 20 characters, avoid dictionary words."
                ),
                'raw_data': {'password': password}
            })
        elif metadata.get('handshake_captured') and not metadata.get('wordlist_missing'):
            findings.append({
                'title': "Password not found in wordlist",
                'severity': 'low',
                'description': (
                    "Handshake was captured but password was not found in the wordlist. "
                    "This suggests the password is not a common dictionary word."
                ),
                'remediation': (
                    "Good password strength. Continue using strong, unique passwords."
                ),
                'raw_data': metadata
            })
        
        logger.info(f"Created {len(findings)} findings from Aircrack-ng output")
        return findings
    
    def _enable_monitor_mode(self, interface: str) -> str:
        """Enable monitor mode on WiFi interface."""
        logger.info(f"Enabling monitor mode on {interface}")
        
        # Kill interfering processes
        subprocess.run(['airmon-ng', 'check', 'kill'], capture_output=True)
        
        # Enable monitor mode
        result = subprocess.run(
            ['airmon-ng', 'start', interface],
            capture_output=True,
            text=True,
            check=False
        )
        
        # Monitor interface is usually interface + "mon" (e.g., wlan0mon)
        monitor_iface = f"{interface}mon"
        
        # Verify monitor mode enabled
        iwconfig_result = subprocess.run(
            ['iwconfig', monitor_iface],
            capture_output=True,
            text=True,
            check=False
        )
        
        if 'Mode:Monitor' not in iwconfig_result.stdout:
            raise Exception(f"Failed to enable monitor mode on {interface}")
        
        logger.info(f"Monitor mode enabled: {monitor_iface}")
        return monitor_iface
    
    def _capture_handshake(
        self,
        interface: str,
        bssid: str,
        channel: int,
        output_file: str,
        timeout: int
    ) -> bool:
        """Capture WPA/WPA2 handshake."""
        logger.info(f"Capturing handshake from {bssid} on channel {channel}")
        
        # Build airodump-ng command
        cmd = [
            'airodump-ng',
            '--bssid', bssid,
            '--write', output_file,
            '--output-format', 'cap'
        ]
        
        if channel:
            cmd.extend(['--channel', str(channel)])
        
        cmd.append(interface)
        
        # Start capture
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait for timeout or handshake
            process.wait(timeout=timeout)
            process.terminate()
            
            # Check if handshake was captured
            cap_file = f"{output_file}-01.cap"
            if os.path.exists(cap_file):
                # Verify handshake with aircrack-ng
                verify_result = subprocess.run(
                    ['aircrack-ng', cap_file],
                    capture_output=True,
                    text=True,
                    check=False
                )
                
                if 'handshake' in verify_result.stdout.lower():
                    logger.info("Handshake captured successfully")
                    return True
            
            logger.warning("No handshake captured within timeout")
            return False
        
        except subprocess.TimeoutExpired:
            process.terminate()
            logger.warning("Capture timeout expired")
            return False
    
    def _crack_password(self, capture_file: str, bssid: str, wordlist: str) -> str:
        """Crack WPA/WPA2 password using wordlist."""
        logger.info(f"Attempting to crack password using {wordlist}")
        
        cap_file = f"{capture_file}-01.cap"
        
        result = subprocess.run(
            ['aircrack-ng', '-w', wordlist, '-b', bssid, cap_file],
            capture_output=True,
            text=True,
            timeout=3600,  # 1 hour max
            check=False
        )
        
        # Parse output for KEY FOUND
        match = re.search(r'KEY FOUND! \[ (.*?) \]', result.stdout)
        if match:
            password = match.group(1)
            logger.info(f"Password cracked: {password}")
            return password
        
        logger.info("Password not found in wordlist")
        return None
    
    def _disable_monitor_mode(self, monitor_iface: str, original_iface: str) -> None:
        """Disable monitor mode and restore managed mode."""
        logger.info(f"Disabling monitor mode on {monitor_iface}")
        
        subprocess.run(
            ['airmon-ng', 'stop', monitor_iface],
            capture_output=True,
            check=False
        )
        
        # Restart NetworkManager
        subprocess.run(
            ['systemctl', 'start', 'NetworkManager'],
            capture_output=True,
            check=False
        )
    
    def _is_valid_bssid(self, bssid: str) -> bool:
        """Validate BSSID format (MAC address)."""
        pattern = r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$'
        return bool(re.match(pattern, bssid))
