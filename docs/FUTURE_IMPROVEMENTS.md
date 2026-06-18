# Améliorations Futures — ToolBox M1

**Document créé** : 18 mai 2026 (J16)  
**Statut** : Roadmap post-MVP  
**Priorité** : Phase 4 ou Phase 5

---

## 🎯 FEATURE 1 : Gestion par MISSIONS (Haute Priorité)

### Problème actuel

L'architecture MVP mélange tous les jobs/findings de tous les clients. Pas d'isolation par projet client.

### Solution proposée : Table MISSIONS

```sql
-- Nouvelle table missions
CREATE TABLE missions (
    id UUID PRIMARY KEY,
    client_name VARCHAR(255) NOT NULL,
    project_code VARCHAR(50) UNIQUE NOT NULL,  -- "ACME-2026-Q2"
    scope TEXT,                                -- "192.168.1.0/24, app.acme.com"
    exclusions TEXT,                           -- IPs/domaines exclus
    start_date DATE,
    end_date DATE,
    status VARCHAR(20) DEFAULT 'draft',        -- draft, active, completed, archived
    rules_of_engagement TEXT,                  -- RoE : horaires, limitations
    contact_info JSONB,                        -- POC client
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Modifier table jobs (ajout mission_id)
ALTER TABLE jobs ADD COLUMN mission_id UUID REFERENCES missions(id);
CREATE INDEX idx_jobs_mission ON jobs(mission_id);

-- Modifier table findings (hérite via job.mission_id)
-- Pas de changement direct, relation via job
```

### Workflow utilisateur

**1. Création mission :**

```
UI : /missions/new

Nom client : "Acme Corp"
Code projet : "ACME-2026-Q2"
Scope : 192.168.1.0/24, app.acme.com
Exclusions : 192.168.1.10 (prod DB)
Dates : 2026-05-20 → 2026-05-27
RoE : Tests 22h-6h uniquement
Contact : security@acme.com
```

**2. Pendant la mission :**

```
Dashboard : Filtre automatique par mission active
Jobs : Tous liés à mission_id
Findings : Affichage par mission
Scope validation : Alerte si scan hors scope
```

**3. Fin de mission :**

```
Rapport global mission (tous jobs agrégés)
Archive mission → read-only
Export complet pour client
Suppression RGPD : DELETE mission CASCADE
```

### Bénéfices

- ✅ **Isolation clients** : Données ACME ≠ BetaCorp
- ✅ **Conformité RGPD** : Suppression mission = suppression données
- ✅ **Audit trail** : Traçabilité par client
- ✅ **Facturation** : Temps passé par mission
- ✅ **Collaboration** : Équipe assignée à mission
- ✅ **Scope enforcement** : Validation automatique cibles

### Implémentation estimée

**Temps** : 2-3 jours (J17-J19 si fait maintenant, ou Phase 4)

**Fichiers à modifier :**
- `core/models/mission.py` (nouveau)
- `core/models/job.py` (ajout mission_id)
- `core/api/routes.py` (+10 endpoints missions)
- `ui/templates/missions.html` (nouveau)
- `ui/templates/mission_detail.html` (nouveau)
- `ui/templates/dashboard.html` (filtrage mission)
- Migration DB : `scripts/migrations/add_missions.py`

**Tests requis :**
- CRUD missions
- Cascade delete (mission → jobs → findings)
- Filtrage UI par mission
- Rapport mission global

---

## 🎯 FEATURE 2 : Backup & Archivage (Haute Priorité)

### Problème actuel

Pas de stratégie backup/restore définie. Suppression définitive.

### Solution proposée : Système backup complet

**Composants à sauvegarder :**

```bash
# 1. Base de données PostgreSQL
pg_dump -U pentest pentest_toolbox > backup_$(date +%Y%m%d).sql

# 2. MinIO artifacts
mc mirror local/artifacts /backup/minio/

# 3. Configuration
cp .env /backup/config/

# 4. Logs applicatifs
tar -czf logs_$(date +%Y%m%d).tar.gz /var/log/pentest-toolbox/
```

**Script automatisé :**

```bash
#!/bin/bash
# scripts/backup.sh

BACKUP_DIR="/backup/pentest-toolbox"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR/$DATE

# PostgreSQL
docker-compose exec -T postgres pg_dump -U pentest pentest_toolbox > $BACKUP_DIR/$DATE/db.sql

# MinIO
docker-compose exec -T minio mc mirror local/artifacts $BACKUP_DIR/$DATE/minio/

# Config
cp .env $BACKUP_DIR/$DATE/config.env

# Chiffrement (optionnel)
tar -czf $BACKUP_DIR/backup_$DATE.tar.gz $BACKUP_DIR/$DATE/
gpg --encrypt --recipient admin@toolbox.local $BACKUP_DIR/backup_$DATE.tar.gz

# Cleanup ancien backups (garde 30 jours)
find $BACKUP_DIR -type f -mtime +30 -delete

echo "Backup completed: $BACKUP_DIR/backup_$DATE.tar.gz.gpg"
```

**Cron automatique :**

```cron
# Backup quotidien 2h du matin
0 2 * * * /opt/pentest-toolbox/scripts/backup.sh
```

**Restore procedure :**

```bash
#!/bin/bash
# scripts/restore.sh

BACKUP_FILE=$1

# Decrypt
gpg --decrypt $BACKUP_FILE > backup.tar.gz

# Extract
tar -xzf backup.tar.gz

# Restore DB
docker-compose exec -T postgres psql -U pentest pentest_toolbox < backup_*/db.sql

# Restore MinIO
docker-compose exec -T minio mc mirror backup_*/minio/ local/artifacts/

echo "Restore completed"
```

---

## 🎯 FEATURE 3 : Archivage Missions (Moyenne Priorité)

### Workflow archivage

**1. Fin de mission :**
```python
# Archive mission (read-only)
mission.status = 'archived'
mission.archived_at = datetime.utcnow()
db.session.commit()

# Export complet
export_mission_data(mission.id, format='zip')
# Contient : rapport PDF, CSV findings, artifacts MinIO
```

**2. Suppression RGPD :**
```python
# Suppression complète données client
def delete_mission_gdpr(mission_id):
    mission = Mission.query.get(mission_id)
    
    # 1. Findings (via jobs)
    for job in mission.jobs:
        Finding.query.filter_by(job_id=job.id).delete()
    
    # 2. Artifacts MinIO
    for job in mission.jobs:
        artifacts = Artifact.query.filter_by(job_id=job.id).all()
        for artifact in artifacts:
            minio_client.remove_object(artifact.minio_bucket, artifact.minio_key)
        Artifact.query.filter_by(job_id=job.id).delete()
    
    # 3. Jobs
    Job.query.filter_by(mission_id=mission_id).delete()
    
    # 4. Mission
    db.session.delete(mission)
    
    # 5. Audit log
    audit_log('mission.deleted_gdpr', 'mission', mission_id)
    
    db.session.commit()
```

**3. Rétention légale :**
```python
# Politique de rétention (configurable)
RETENTION_POLICIES = {
    'active': None,           # Pas de limite
    'completed': 365,         # 1 an
    'archived': 730,          # 2 ans
}

# Cron cleanup automatique
def cleanup_old_missions():
    for status, days in RETENTION_POLICIES.items():
        if days:
            cutoff = datetime.utcnow() - timedelta(days=days)
            old_missions = Mission.query.filter(
                Mission.status == status,
                Mission.updated_at < cutoff
            ).all()
            
            for mission in old_missions:
                delete_mission_gdpr(mission.id)
```

---

## 🎯 FEATURE 4 : Export Mission Complet (Moyenne Priorité)

### Format d'export

```python
def export_mission_zip(mission_id):
    """
    Export complet mission en ZIP
    
    Structure :
    ACME-2026-Q2/
    ├── rapport_mission.pdf          # Rapport global
    ├── findings_export.csv          # Tous findings
    ├── jobs/
    │   ├── job_nmap_001.json        # Détails job
    │   ├── job_nuclei_002.json
    │   └── ...
    ├── artifacts/
    │   ├── nmap_output.xml          # Depuis MinIO
    │   ├── nuclei_report.json
    │   └── ...
    └── metadata.json                # Info mission
    """
    pass
```

**UI Download :**

```
/missions/ACME-2026-Q2/export
→ Bouton "Download Complete Mission Archive"
→ ZIP chiffré (password optionnel)
→ Livrable client final
```

---

## 📊 Priorités d'implémentation

| Feature | Priorité | Effort | Impact | Quand |
|---------|----------|--------|--------|-------|
| **Missions** | 🔴 Haute | 3j | ⭐⭐⭐⭐⭐ | Phase 4 ou dès que MVP validé |
| **Backup/Restore** | 🔴 Haute | 1j | ⭐⭐⭐⭐ | Phase 4 |
| **Archivage** | 🟡 Moyenne | 1j | ⭐⭐⭐ | Phase 4-5 |
| **Export ZIP** | 🟡 Moyenne | 0.5j | ⭐⭐⭐ | Phase 5 |

---

## 📝 Notes d'implémentation

**Compatibilité ascendante :**
- Missions optionnelles : jobs sans mission_id restent valides
- Migration : jobs existants → mission "Legacy" par défaut
- UI : affichage avec/sans mission (fallback gracieux)

**Tests requis :**
- CASCADE DELETE mission → jobs → findings
- Backup/restore complet
- Export ZIP chiffré
- Performance avec 1000+ missions

**Documentation requise :**
- Guide création mission
- Procédure backup/restore
- Politique RGPD
- Guide archivage

---

**Version** : 1.0  
**Auteur** : Carlos  
**Validation requise** : Avant implémentation Phase 4

---

## 🎯 FEATURE 5 : Rapport Consolidé par Workflow (Moyenne Priorité)

### Problème actuel

Chaque outil d'un workflow génère son propre job et son propre rapport indépendant.
Il n'existe pas de vue unifiée des résultats d'un workflow complet.

### Solution proposée

- Nouveau modèle `Workflow` en base (id, name, job_ids[], status, created_at)
- Endpoint `/api/workflows/<id>/report` — agrège les findings de tous les jobs
- Générateur de rapport multi-outils (HTML + PDF)
- UI : page `/workflows/<id>` affichant la chaîne + findings consolidés

### Implémentation estimée

**Temps** : 1-2 jours

**Fichiers à modifier :**
- `core/models/workflow.py` (nouveau)
- `core/orchestrator/workflows.py` (retourner workflow_id persistant)
- `core/reporting/html_generator.py` (rapport multi-jobs)
- `ui/templates/workflow_detail.html` (nouveau)

---

## 🎯 FEATURE 6 : Workflows Paramétrables (Basse Priorité)

### Problème actuel

Les workflows utilisent des paramètres par défaut fixes.
L'utilisateur ne peut pas ajuster les options de chaque outil dans la chaîne.

### Solution proposée (Option C — Hybride)

- Paramètres par défaut intelligents pour un lancement rapide ("one click")
- Section `<details>` dépliable par étape dans l'UI workflow
- Chaque étape expose les mêmes options que sa page dédiée
- Cohérent avec l'approche des pages `nmap_launch.html`, `nuclei_launch.html`, etc.

### Implémentation estimée

**Temps** : 2-3 jours

**Fichiers à modifier :**
- `ui/templates/workflows.html` (formulaires étendus par workflow)
- `core/api/routes.py` (accepter paramètres étendus)
- `core/orchestrator/workflows.py` (passer paramètres aux jobs)

---

## 📊 Priorités d'implémentation (mise à jour 18 juin 2026)

| Feature | Priorité | Effort | Impact | Quand |
|---------|----------|--------|--------|-------|
| **Missions** | 🔴 Haute | 3j | ⭐⭐⭐⭐⭐ | Phase 4 |
| **Backup/Restore** | 🔴 Haute | 1j | ⭐⭐⭐⭐ | Phase 4 |
| **Rapport workflow consolidé** | 🟡 Moyenne | 1-2j | ⭐⭐⭐⭐ | Phase 4 |
| **Archivage** | 🟡 Moyenne | 1j | ⭐⭐⭐ | Phase 4-5 |
| **Export ZIP** | 🟡 Moyenne | 0.5j | ⭐⭐⭐ | Phase 5 |
| **Workflows paramétrables** | 🟢 Basse | 2-3j | ⭐⭐⭐ | Phase 5 |

---

**Version** : 1.1
**Mis à jour** : 18 juin 2026 (Phase 3)
**Ajouts** : Feature 5 (rapport workflow), Feature 6 (workflows paramétrables)
