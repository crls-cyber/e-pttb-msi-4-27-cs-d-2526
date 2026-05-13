"""Base class for external file parsers."""
from abc import ABC, abstractmethod
from typing import Dict, Any, List
import os


class ExternalParserBase(ABC):
    """Base class for parsing externally uploaded files."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Parser name."""
        pass
    
    @property
    @abstractmethod
    def supported_extensions(self) -> List[str]:
        """List of supported file extensions (e.g., ['.pcap', '.pcapng'])."""
        pass
    
    @property
    @abstractmethod
    def max_file_size_mb(self) -> int:
        """Maximum allowed file size in MB."""
        pass
    
    def validate_file(self, filepath: str) -> bool:
        """
        Validate uploaded file.
        
        Args:
            filepath: Path to the uploaded file
            
        Returns:
            True if valid, raises ValueError otherwise
        """
        if not os.path.exists(filepath):
            raise ValueError(f"File not found: {filepath}")
        
        # Check extension
        ext = os.path.splitext(filepath)[1].lower()
        if ext not in self.supported_extensions:
            raise ValueError(
                f"Unsupported file extension: {ext}. "
                f"Supported: {', '.join(self.supported_extensions)}"
            )
        
        # Check file size
        size_mb = os.path.getsize(filepath) / (1024 * 1024)
        if size_mb > self.max_file_size_mb:
            raise ValueError(
                f"File too large: {size_mb:.1f}MB. "
                f"Maximum: {self.max_file_size_mb}MB"
            )
        
        return True
    
    @abstractmethod
    def parse(self, filepath: str, user_id: str) -> Dict[str, Any]:
        """
        Parse the uploaded file and extract findings.
        
        Args:
            filepath: Path to the uploaded file
            user_id: User who uploaded the file
            
        Returns:
            Dictionary with:
                - findings: List of findings
                - metadata: File metadata
                - summary: Human-readable summary
        """
        pass
