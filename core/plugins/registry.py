"""Plugin registry for auto-discovery."""
import os
import importlib
import inspect
from typing import Dict, List, Type
from .base import PluginBase


class PluginRegistry:
    """Registry for plugin auto-discovery and management."""
    
    def __init__(self):
        self._plugins: Dict[str, Type[PluginBase]] = {}
        self._discover_plugins()
    
    def _discover_plugins(self) -> None:
        """Discover all plugins in the plugins/ directory."""
        plugins_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'plugins')
        
        if not os.path.exists(plugins_dir):
            return
        
        for plugin_name in os.listdir(plugins_dir):
            plugin_path = os.path.join(plugins_dir, plugin_name)
            
            # Skip if not a directory, starts with _, or is the external parsers folder
            if not os.path.isdir(plugin_path) or plugin_name.startswith('_'):
                continue
            if plugin_name == 'external':
                continue
            
            # Try to import plugin.py
            try:
                module_name = f'plugins.{plugin_name}.plugin'
                module = importlib.import_module(module_name)
                
                # Find PluginBase subclasses
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if issubclass(obj, PluginBase) and obj is not PluginBase:
                        self._plugins[plugin_name] = obj
                        print(f"[Registry] Discovered plugin: {plugin_name}")
                        
            except Exception as e:
                print(f"[Registry] Failed to load plugin {plugin_name}: {e}")
    
    def get_plugin(self, name: str) -> Type[PluginBase]:
        """
        Get a plugin class by name.
        
        Args:
            name: Plugin name
            
        Returns:
            Plugin class
            
        Raises:
            KeyError: If plugin not found
        """
        if name not in self._plugins:
            raise KeyError(f"Plugin '{name}' not found")
        return self._plugins[name]
    
    def list_plugins(self) -> List[Dict[str, str]]:
        """
        List all available plugins.
        
        Returns:
            List of plugin metadata
        """
        plugins = []
        for name, plugin_class in self._plugins.items():
            plugins.append({
                'name': name,
                'version': plugin_class.version,
                'description': plugin_class.description,
                'capabilities': plugin_class.capabilities
            })
        return plugins
    
    def plugin_exists(self, name: str) -> bool:
        """Check if a plugin exists."""
        return name in self._plugins


# Global registry instance
registry = PluginRegistry()
