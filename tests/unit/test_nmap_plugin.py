"""
Tests unitaires du plugin Nmap
"""
import pytest
from plugins.nmap.plugin import NmapPlugin


def test_nmap_plugin_initialization():
    """Test: Plugin Nmap s'initialise correctement"""
    config = {'target': '192.168.1.1'}
    plugin = NmapPlugin(config)
    assert plugin.name == 'nmap'


def test_nmap_validate_config_valid():
    """Test: Configuration valide acceptée"""
    config = {
        'target': '192.168.1.1',
        'ports': '80,443,22'
    }
    plugin = NmapPlugin(config)
    
    # Should not raise exception (validate_config uses self.config)
    try:
        plugin.validate_config()  # PAS DE PARAMÈTRE
        assert True
    except Exception as e:
        assert False, f"Valid config should not raise exception: {e}"


def test_nmap_validate_config_missing_target():
    """Test: Configuration sans target rejetée"""
    config = {'ports': '80,443'}
    
    with pytest.raises(ValueError):
        plugin = NmapPlugin(config)
        plugin.validate_config()  # PAS DE PARAMÈTRE


def test_nmap_validate_config_invalid_target():
    """Test: Configuration avec target vide rejetée"""
    config = {'target': ''}
    
    with pytest.raises(ValueError):
        plugin = NmapPlugin(config)
        plugin.validate_config()  # PAS DE PARAMÈTRE
