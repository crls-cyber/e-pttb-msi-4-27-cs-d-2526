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
            
            # Instantiate plugin with config
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
                # Pass metadata to parse_output when the plugin's signature accepts it
                # (some plugins like nmap/nuclei/sqlmap take metadata as a 2nd arg,
                # others like hydra expect it nested inside raw_output as a dict).
                import inspect
                sig_params = inspect.signature(plugin.parse_output).parameters
                raw_output_value = execution_result.get('raw_output')
                metadata_value = execution_result.get('metadata', {})

                if 'metadata' in sig_params:
                    findings = plugin.parse_output(raw_output_value, metadata=metadata_value)
                elif isinstance(raw_output_value, str) and metadata_value:
                    # Plugin expects a single dict-like raw_output containing metadata
                    # (e.g. hydra) — wrap it so raw_output.get('metadata') works.
                    findings = plugin.parse_output({
                        'raw_output': raw_output_value,
                        'metadata': metadata_value
                    })
                else:
                    findings = plugin.parse_output(raw_output_value)
                
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
