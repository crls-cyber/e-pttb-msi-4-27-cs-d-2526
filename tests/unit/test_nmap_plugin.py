"""
Tests unitaires du plugin Nmap
"""
import pytest
from plugins.nmap.plugin import NmapPlugin


def test_nmap_plugin_initialization():
    """Test: Plugin Nmap s'initialise correctement"""
    plugin = NmapPlugin()
    assert plugin.name == 'nmap'
    assert plugin.version is not None


def test_nmap_validate_config_valid():
    """Test: Configuration valide acceptée"""
    plugin = NmapPlugin()
    config = {
        'target': '192.168.1.1',
        'ports': '80,443,22'
    }
    
    # Should not raise exception
    try:
        plugin.validate_config(config)
        assert True
    except Exception:
        assert False, "Valid config should not raise exception"


def test_nmap_validate_config_missing_target():
    """Test: Configuration sans target rejetée"""
    plugin = NmapPlugin()
    config = {'ports': '80,443'}
    
    with pytest.raises(ValueError):
        plugin.validate_config(config)


def test_nmap_validate_config_invalid_target():
    """Test: Configuration avec target invalide rejetée"""
    plugin = NmapPlugin()
    config = {'target': ''}
    
    with pytest.raises(ValueError):
        plugin.validate_config(config)
