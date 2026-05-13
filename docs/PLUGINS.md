# Plugin Development Guide

This guide explains how to create custom plugins for the Pentest Toolbox.

---

## 📋 Table of Contents

- [Plugin Structure](#plugin-structure)
- [Minimal Example](#minimal-example)
- [PluginBase Class](#pluginbase-class)
- [Configuration Validation](#configuration-validation)
- [Execution Logic](#execution-logic)
- [Output Parsing](#output-parsing)
- [Error Handling](#error-handling)
- [Testing Plugins](#testing-plugins)
- [Best Practices](#best-practices)

---

## 📂 Plugin Structure

Each plugin must be in a folder `plugins/<plugin_name>/` containing at minimum:

## 📂 Plugin Structure

Each plugin must be in a folder `plugins/<plugin_name>/` containing at minimum:

```
plugins/
└── my_plugin/
    ├── __init__.py
    └── plugin.py
```

### Optional Files

```
plugins/
└── my_plugin/
    ├── __init__.py
    ├── plugin.py
    ├── parser.py      # Output parsing logic
    ├── config.py      # Plugin-specific config
    └── tests/
        └── test_my_plugin.py
```

---

## 🛠️ Minimal Example

### `plugins/my_plugin/plugin.py`

```python
from core.plugins import PluginBase
from typing import Dict, Any, List
import subprocess

class MyPlugin(PluginBase):
    """Description of my plugin."""
    
    name = "my_plugin"
    version = "1.0.0"
    description = "My pentest plugin"
    capabilities = ["network_scan"]
    
    required_params = ["target"]
    optional_params = ["ports", "timeout"]
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate plugin configuration."""
        if "target" not in config:
            raise ValueError("Missing required parameter: target")
        return True
    
    def run(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the plugin."""
        target = config["target"]
        ports = config.get("ports", "80,443")
        
        # Execute tool (example: nmap)
        result = subprocess.run(
            ["nmap", "-p", ports, target],
            capture_output=True,
            text=True,
            timeout=300
        )
        
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "return_code": result.returncode
        }
    
    def parse_output(self, raw_output: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse tool output into findings."""
        findings = []
        
        # Example parsing logic
        if "open" in raw_output["stdout"]:
            findings.append({
                "title": f"Open ports found on {config['target']}",
                "severity": "medium",
                "description": raw_output["stdout"]
            })
        
        return findings
```

### `plugins/my_plugin/__init__.py`

```python
from .plugin import MyPlugin

__all__ = ["MyPlugin"]
```

---

## 🧩 PluginBase Class

All plugins must inherit from `PluginBase` and implement these methods:

### Required Attributes

```python
class MyPlugin(PluginBase):
    name = "my_plugin"              # Unique identifier (lowercase, underscores)
    version = "1.0.0"                # Semantic versioning
    description = "Short description" # One-line description
    capabilities = ["network_scan"]  # List of capabilities
    
    required_params = ["target"]     # Required config parameters
    optional_params = ["ports"]      # Optional config parameters
```

### Required Methods

#### 1. `validate_config(config: Dict) -> bool`

Validates the configuration before execution.

```python
def validate_config(self, config: Dict[str, Any]) -> bool:
    """Validate plugin configuration."""
    
    # Check required parameters
    for param in self.required_params:
        if param not in config:
            raise ValueError(f"Missing required parameter: {param}")
    
    # Validate parameter types/values
    if "ports" in config:
        if not isinstance(config["ports"], str):
            raise ValueError("Parameter 'ports' must be a string")
    
    return True
```

#### 2. `run(config: Dict) -> Dict`

Executes the plugin's main logic.

```python
def run(self, config: Dict[str, Any]) -> Dict[str, Any]:
    """Execute the plugin."""
    
    # Extract config
    target = config["target"]
    
    # Execute tool
    result = subprocess.run(
        ["tool", "--target", target],
        capture_output=True,
        text=True,
        timeout=config.get("timeout", 300)
    )
    
    # Return raw output
    return {
        "stdout": result.stdout,
        "stderr": result.stderr,
        "return_code": result.returncode
    }
```

#### 3. `parse_output(raw_output: Dict) -> List[Dict]`

Parses tool output into structured findings.

```python
def parse_output(self, raw_output: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Parse tool output into findings."""
    
    findings = []
    
    # Example: Parse JSON output
    import json
    data = json.loads(raw_output["stdout"])
    
    for item in data.get("vulnerabilities", []):
        findings.append({
            "title": item["name"],
            "severity": item["severity"],
            "description": item["description"],
            "cvss_score": item.get("cvss"),
            "cve_id": item.get("cve")
        })
    
    return findings
```

---

## ✅ Configuration Validation

### Example: Complex Validation

```python
def validate_config(self, config: Dict[str, Any]) -> bool:
    """Validate configuration with detailed checks."""
    
    # Required parameters
    if "target" not in config:
        raise ValueError("Missing required parameter: target")
    
    # IP address validation
    target = config["target"]
    if not self._is_valid_ip(target) and not self._is_valid_domain(target):
        raise ValueError(f"Invalid target: {target}")
    
    # Port range validation
    if "ports" in config:
        ports = config["ports"]
        if not self._is_valid_port_range(ports):
            raise ValueError(f"Invalid port range: {ports}")
    
    # Numeric parameter validation
    if "timeout" in config:
        timeout = config["timeout"]
        if not isinstance(timeout, int) or timeout <= 0:
            raise ValueError(f"Invalid timeout: {timeout}")
    
    return True

def _is_valid_ip(self, ip: str) -> bool:
    """Check if string is a valid IP address."""
    import ipaddress
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False

def _is_valid_domain(self, domain: str) -> bool:
    """Check if string is a valid domain."""
    import re
    pattern = r'^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$'
    return bool(re.match(pattern, domain))
```

---

## 🚀 Execution Logic

### Using subprocess

```python
import subprocess

def run(self, config: Dict[str, Any]) -> Dict[str, Any]:
    """Execute external tool."""
    
    cmd = [
        "nmap",
        "-sV",  # Service version detection
        "-p", config.get("ports", "1-1000"),
        config["target"]
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=config.get("timeout", 300),
            check=False  # Don't raise on non-zero exit
        )
        
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "return_code": result.returncode,
            "command": " ".join(cmd)
        }
    
    except subprocess.TimeoutExpired:
        raise Exception(f"Plugin execution timeout after {config.get('timeout', 300)}s")
```

### Using Python Libraries

```python
import nmap

def run(self, config: Dict[str, Any]) -> Dict[str, Any]:
    """Execute using python-nmap library."""
    
    nm = nmap.PortScanner()
    
    nm.scan(
        hosts=config["target"],
        ports=config.get("ports", "1-1000"),
        arguments="-sV"
    )
    
    return {
        "raw_data": nm.csv(),
        "scan_info": nm.scaninfo(),
        "hosts": dict(nm._scan_result)
    }
```

---

## 🔍 Output Parsing

### Example: XML Parsing (Nmap)

```python
import xml.etree.ElementTree as ET

def parse_output(self, raw_output: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Parse Nmap XML output."""
    
    findings = []
    xml_content = raw_output["stdout"]
    
    try:
        root = ET.fromstring(xml_content)
        
        for host in root.findall(".//host"):
            ip = host.find(".//address[@addrtype='ipv4']").get("addr")
            
            for port in host.findall(".//port"):
                port_id = port.get("portid")
                state = port.find("state").get("state")
                
                if state == "open":
                    service = port.find("service")
                    service_name = service.get("name") if service is not None else "unknown"
                    
                    findings.append({
                        "title": f"Open port {port_id}/tcp on {ip}",
                        "severity": "medium",
                        "description": f"Port {port_id}/tcp is open running {service_name}"
                    })
    
    except ET.ParseError as e:
        raise Exception(f"Failed to parse XML output: {e}")
    
    return findings
```

### Example: JSON Parsing (Nuclei)

```python
import json

def parse_output(self, raw_output: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Parse Nuclei JSON output."""
    
    findings = []
    
    for line in raw_output["stdout"].strip().split("\n"):
        if not line:
            continue
        
        try:
            data = json.loads(line)
            
            findings.append({
                "title": data.get("info", {}).get("name", "Vulnerability found"),
                "severity": data.get("info", {}).get("severity", "info"),
                "description": data.get("info", {}).get("description", ""),
                "cve_id": data.get("info", {}).get("cve-id"),
                "cvss_score": data.get("info", {}).get("cvss-score")
            })
        
        except json.JSONDecodeError:
            continue
    
    return findings
```

---

## ⚠️ Error Handling

### Best Practices

```python
def run(self, config: Dict[str, Any]) -> Dict[str, Any]:
    """Execute plugin with robust error handling."""
    
    try:
        # Validate before execution
        self.validate_config(config)
        
        # Execute tool
        result = subprocess.run(
            ["tool", "--target", config["target"]],
            capture_output=True,
            text=True,
            timeout=config.get("timeout", 300)
        )
        
        # Check for errors
        if result.returncode != 0:
            raise Exception(f"Tool failed with exit code {result.returncode}: {result.stderr}")
        
        return {"stdout": result.stdout, "stderr": result.stderr}
    
    except subprocess.TimeoutExpired:
        raise Exception(f"Plugin execution timeout after {config.get('timeout', 300)}s")
    
    except FileNotFoundError:
        raise Exception("Tool not found. Ensure it is installed in the Docker worker.")
    
    except Exception as e:
        raise Exception(f"Plugin execution failed: {str(e)}")
```

---

## 🧪 Testing Plugins

### Unit Tests

Create `plugins/my_plugin/tests/test_my_plugin.py`:

```python
import pytest
from plugins.my_plugin.plugin import MyPlugin

def test_validate_config_missing_target():
    """Test validation fails when target is missing."""
    plugin = MyPlugin()
    
    with pytest.raises(ValueError, match="Missing required parameter: target"):
        plugin.validate_config({})

def test_validate_config_valid():
    """Test validation passes with valid config."""
    plugin = MyPlugin()
    
    config = {"target": "192.168.1.1", "ports": "80,443"}
    assert plugin.validate_config(config) is True

def test_parse_output():
    """Test output parsing."""
    plugin = MyPlugin()
    
    raw_output = {
        "stdout": "Port 80/tcp open\nPort 443/tcp open",
        "stderr": "",
        "return_code": 0
    }
    
    findings = plugin.parse_output(raw_output)
    
    assert len(findings) > 0
    assert findings[0]["severity"] in ["critical", "high", "medium", "low", "info"]
```

### Running Tests

```bash
# Run all plugin tests
pytest plugins/my_plugin/tests/ -v

# Run with coverage
pytest plugins/my_plugin/tests/ --cov=plugins.my_plugin
```

---

## 📏 Best Practices

### 1. Security

- ✅ **Never execute user input directly** (risk of command injection)
- ✅ **Validate all parameters** before execution
- ✅ **Use subprocess with lists** instead of shell strings
- ✅ **Set timeouts** to prevent hanging jobs

```python
# ✅ GOOD
subprocess.run(["nmap", "-p", ports, target], timeout=300)

# ❌ BAD (command injection risk)
os.system(f"nmap -p {ports} {target}")
```

### 2. Performance

- ✅ **Set reasonable timeouts** (default: 300s)
- ✅ **Stream large outputs** instead of loading in memory
- ✅ **Clean up temporary files** after execution

### 3. Error Messages

- ✅ **Provide clear error messages** for debugging
- ✅ **Log errors** to Celery worker logs
- ✅ **Return partial results** if possible

### 4. Documentation

- ✅ **Document all parameters** in docstrings
- ✅ **Provide usage examples** in plugin docstring
- ✅ **Update PLUGINS.md** when adding new capabilities

---

## 📦 Plugin Registration

Plugins are **automatically discovered** by the `PluginRegistry` at startup.

### How It Works

1. Registry scans `plugins/` directory
2. Finds all classes inheriting from `PluginBase`
3. Registers plugins by their `name` attribute

### Manual Registration (Optional)

```python
# core/plugins/registry.py
from plugins.my_plugin import MyPlugin

registry = PluginRegistry()
registry.register(MyPlugin())
```

---

## 🔌 Available Capabilities

Plugins can declare these capabilities:

| Capability | Description | Examples |
|------------|-------------|----------|
| `network_scan` | Network/port scanning | Nmap, Masscan |
| `web_scan` | Web application scanning | Nuclei, ZAP, Nikto |
| `osint` | Open-source intelligence | theHarvester, Maltego |
| `exploitation` | Automated exploitation | Metasploit, SQLmap |
| `bruteforce` | Credential brute-forcing | Hydra, Medusa |
| `wireless` | WiFi security testing | Aircrack-ng |
| `mitm` | Man-in-the-middle attacks | Ettercap, Bettercap |

---

## 📝 Full Example: SQLmap Plugin

See `plugins/sqlmap/plugin.py` for a complete real-world example.

---

## 🆘 Troubleshooting

### Plugin Not Found

- Check folder structure: `plugins/<name>/plugin.py`
- Verify `__init__.py` exports the class
- Restart Celery worker: `docker compose restart worker`

### Import Errors

- Ensure dependencies are in `pyproject.toml`
- Rebuild worker image: `docker compose build worker`

### Timeout Issues

- Increase timeout in plugin config
- Check Celery task limits in `deploy/.env`

---

## 📬 Need Help?

- **Documentation:** [docs/](../docs/)
- **Issues:** [GitHub Issues](https://github.com/crls-cyber/pentest-toolbox-v2/issues)
- **Contact:** admin@toolbox.local

---

**Happy plugin development! 🚀**
