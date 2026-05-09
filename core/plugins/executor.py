"""Plugin executor with timeout and error handling."""
import time
import signal
from typing import Dict, Any, List
from .registry import registry
from .base import PluginBase


class TimeoutError(Exception):
    """Raised when plugin execution times out."""
    pass


def timeout_handler(signum, frame):
    """Signal handler for timeout."""
    raise TimeoutError("Plugin execution timed out")


class PluginExecutor:
    """Execute plugins with timeout and error handling."""
    
    def __init__(self, timeout: int = 3600):
        """
        Initialize executor.
        
        Args:
            timeout: Maximum execution time in seconds (default: 1 hour)
        """
        self.timeout = timeout
    
    def execute(self, plugin_name: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a plugin.
        
        Args:
            plugin_name: Name of the plugin to execute
            config: Plugin configuration
            
        Returns:
            Dict containing:
                - success: bool
                - duration: float (seconds)
                - raw_output: Any
                - findings: List[Dict]
                - artifacts: List[str]
                - error: str (if failed)
        """
        start_time = time.time()
        result = {
            'success': False,
            'duration': 0,
            'raw_output': None,
            'findings': [],
            'artifacts': [],
            'error': None
        }
        
        try:
            # Get plugin class
            plugin_class = registry.get_plugin(plugin_name)
            
            # Instantiate plugin
            plugin: PluginBase = plugin_class(config)
            
            # Set timeout alarm
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(self.timeout)
            
            try:
                # Execute plugin
                execution_result = plugin.run()
                
                # Cancel timeout alarm
                signal.alarm(0)
                
                # Parse output
                findings = plugin.parse_output(
                    execution_result.get('raw_output'),
                    execution_result.get('metadata', {})
                )
                
                # Success
                result['success'] = True
                result['raw_output'] = execution_result.get('raw_output')
                result['findings'] = findings
                result['artifacts'] = execution_result.get('artifacts', [])
                
            except TimeoutError:
                signal.alarm(0)
                raise TimeoutError(f"Plugin execution exceeded {self.timeout}s timeout")
            
        except Exception as e:
            result['error'] = str(e)
        
        finally:
            result['duration'] = time.time() - start_time
        
        return result


# Global executor instance
executor = PluginExecutor()
