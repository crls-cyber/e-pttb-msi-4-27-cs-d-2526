# Guide de Création de Plugins

## Structure d'un plugin

Chaque plugin doit être dans un dossier `plugins/<nom_plugin>/` contenant au minimum : 

plugins/
└── mon_plugin/
├── init.py
└── plugin.py

## Exemple minimal

**`plugins/mon_plugin/plugin.py` :**

```python
from core.plugins import PluginBase
from typing import Dict, Any, List
import subprocess

class MonPlugin(PluginBase):
    """Description de mon plugin."""
    
    name = "mon_plugin"
    version = "1.0.0"
    description = "Mon plugin de pentest"
    capabilities = ["network_scan"]
    
    def validate_config(self) -> None:
        """Valide la configuration."""
        if 'target' not in self.config:
            raise ValueError("Parameter 'target' is required")
    
    def run(self) -> Dict[str, Any]:
        """Exécute le plugin."""
        target = self.config['target']
        
        # Exécuter l'outil
        result = subprocess.run(
            ['nmap', '-sV', target],
            capture_output=True,
            text=True,
            timeout=300
        )
        
        return {
            'raw_output': result.stdout,
            'artifacts': [],  # Chemins vers fichiers générés
            'metadata': {
                'exit_code': result.returncode
            }
        }
    
    def parse_output(self, raw_output: Any) -> List[Dict[str, Any]]:
        """Parse la sortie en findings."""
        findings = []
        
        # Parser la sortie (exemple simplifié)
        if 'open' in raw_output:
            findings.append({
                'title': 'Port ouvert détecté',
                'severity': 'medium',
                'description': 'Un port est ouvert',
                'remediation': 'Vérifier la nécessité'
            })
        
        return findings
```

## Configuration requise

- Hériter de `PluginBase`
- Définir : `name`, `version`, `description`, `capabilities`
- Implémenter : `validate_config()`, `run()`, `parse_output()`

## Utilisation

Le plugin sera automatiquement découvert au démarrage.

```python
# Créer un job avec ce plugin
curl -X POST http://localhost:5000/api/jobs \
  -H "Content-Type: application/json" \
  -d '{"plugin":"mon_plugin","config":{"target":"192.168.1.1"}}'
```

## Sévérités des findings

- `critical` : Critique
- `high` : Élevée
- `medium` : Moyenne
- `low` : Faible
- `info` : Informationnelle

