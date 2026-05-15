"""Base plugin interface."""
from abc import ABC, abstractmethod
from typing import Dict, List, Any


class PluginBase(ABC):
    """Base class for all plugins."""
    
    # Plugin metadata (must be defined by subclass)
    name: str = None
    version: str = None
    description: str = None
    capabilities: List[str] = []  # e.g., ['network_scan', 'web_scan']
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize plugin with configuration.
        
        Args:
            config: Plugin-specific configuration
        """
        self.config = config
        self.validate_config()
    
    @abstractmethod
    def validate_config(self) -> None:
        """
        Validate plugin configuration.
        
        Raises:
            ValueError: If configuration is invalid
        """
        pass
    
    @abstractmethod
    def run(self) -> Dict[str, Any]:
        """
        Execute the plugin.
        
        Returns:
            Dict containing:
                - raw_output: Raw tool output
                - artifacts: List of artifact paths
                - metadata: Execution metadata (duration, exit_code, etc.)
        """
        pass
    
    @abstractmethod
    def parse_output(self, raw_output: Any, metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Parse raw output into standardized findings.
        
        Args:
            raw_output: Raw output from the tool
            metadata: Optional metadata dict with context (job_id, config, etc.)
            
        Returns:
            List of findings, each containing:
                - title: Finding title
                - severity: critical/high/medium/low/info
                - description: Detailed description
                - remediation: How to fix
                - cvss_score: (optional) CVSS score
                - cve_id: (optional) CVE identifier
        """
        pass
    
    def get_metadata(self) -> Dict[str, Any]:
        """Get plugin metadata."""
        return {
            'name': self.name,
            'version': self.version,
            'description': self.description,
            'capabilities': self.capabilities
        }
