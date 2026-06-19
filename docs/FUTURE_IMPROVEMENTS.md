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

---

## 🎯 FEATURE 7 : Sécurisation Machine Dédiée par Mission (Haute Priorité)

### Contexte

Pour des missions sensibles, l'industrie du pentest utilise des machines dédiées par mission,
mises à disposition des pentesters mandatés, avec un environnement préconfiguré et verrouillé.

### Bonnes pratiques du secteur (confirmées réalistes)

- **Machine dédiée par mission** ("engagement laptop") — pratique courante chez les cabinets sérieux,
  parfois exigée contractuellement par le client.
- **Chiffrement disque complet** (LUKS / BitLocker) — standard de l'industrie, souvent imposé par
  les certifications (ISO 27001, PASSI en France).
- **Accès nominatif restreint** — cohérent avec le principe de moindre privilège.
- **Scope pré-défini (cibles autorisées/interdites)** — correspond aux Rules of Engagement (RoE)
  signées avant toute mission. Obligation légale et contractuelle, pas seulement une bonne pratique.

### Limites à connaître

- Le **chiffrement disque** protège contre le vol physique à froid, **pas** contre une compromission
  active pendant l'utilisation (keylogger, exfiltration réseau en cours de mission).
- L'**effacement à distance** nécessite que la machine ait une connexion réseau active pour recevoir
  l'ordre de wipe — inefficace si la machine est immédiatement mise hors ligne après le vol.
  Le chiffrement disque reste la défense principale, indépendante du réseau.

### Lien avec Feature 1 (Missions)

Cette feature est complémentaire à la Feature 1 (Gestion par Missions) : le scope RoE (cibles
autorisées/interdites) correspondrait directement aux champs `scope` et `exclusions` de la table
`missions`, et à la nouvelle Feature 8 (Scope Enforcement) ci-dessous.

---

## 🎯 FEATURE 8 : Scope Enforcement — Blocage Automatique des Cibles (Haute Priorité)

### Problème actuel

La page Targets (ajoutée en Phase 3) est purement informative — rien n'empêche aujourd'hui de
lancer un scan sur une cible non autorisée ou explicitement interdite.

### Solution proposée

**Deux listes de cibles :**
- **Authorized targets** — cibles explicitement autorisées
- **Unauthorized targets** — cibles explicitement interdites (prioritaires en cas de conflit)

**Formats de cibles supportés :**
- IP unique (`192.168.200.133`)
- Plage CIDR (`192.168.200.0/24`) — via le module `ipaddress` de Python
- Domaine exact (`example.com`)
- Domaine + sous-domaines (`*.example.com`)

**Logique de résolution (scope checker) :**
```
SI cible correspond à une entrée "Unauthorized" (règle la plus spécifique) → BLOQUÉ
SINON SI liste "Authorized" non vide ET cible ne correspond à aucune entrée → BLOQUÉ (zero trust)
SINON SI liste "Authorized" non vide ET cible correspond → AUTORISÉ
SINON (liste "Authorized" vide) → BLOQUÉ (zero trust par défaut)
```

**Mode "Zero Trust" par défaut** — standard reconnu en pentest professionnel (méthodologies PTES,
OSSTMM) : rien n'est autorisé tant que ce n'est pas explicitement dans le scope contractuel.
Plus simple à implémenter que le mode permissif actuel.

**Spécificité des règles** — la règle la plus spécifique l'emporte (ex: domaine autorisé +
sous-domaine spécifique interdit → tous les autres sous-domaines restent autorisés). Logique
identique aux règles de pare-feu / ACL réseau.

### Niveau d'application

Contrôle au **niveau API** (`core/api/routes.py`), avant toute création de `Job` — un point de
contrôle centralisé pour tous les endpoints de lancement (jobs individuels + 7 workflows).
Plus robuste qu'un contrôle côté formulaire (JS, contournable) ou côté plugin (redondant).

### Permissions

Seul le rôle `admin` peut ajouter/supprimer des cibles (`@require_role('admin')` sur les endpoints
`POST` et `DELETE /api/targets`), via le décorateur RBAC déjà existant dans `core/security/rbac.py`.

### Implémentation estimée

**Temps** : 1-2 jours

**Fichiers à modifier :**
- `core/models/target.py` (ajout champ `scope_type`: ip/cidr/domain/wildcard_domain)
- `core/security/scope_checker.py` (nouveau — logique de matching + spécificité)
- `core/api/routes.py` (contrôle dans `/jobs` POST + 7 endpoints `/workflows/*`)
- `ui/templates/targets.html` (deux tableaux, case "Unauthorized target", sélecteur de type)

---

## 🎯 FEATURE 9 : Mapping des Rôles RBAC (Priorité Moyenne)

### Constat

Le système RBAC existant définit 3 rôles (`admin`, `analyst`, `viewer`) mais la table `permissions`
est actuellement vide — seul `@require_role()` est utilisé (vérification directe du nom de rôle),
jamais `@require_permission()` (permissions granulaires).

### Mapping proposé (cohérent avec les standards du secteur pentest)

| Rôle existant | Équivalent métier | Responsabilités |
|----------------|-------------------|------------------|
| `admin`   | Lead Pentester | Gère le scope (targets), les utilisateurs, valide les rapports finaux, lance tout type de scan |
| `analyst` | Pentester | Lance des scans sur les cibles autorisées, consulte/édite les findings de ses missions |
| `viewer`  | Membre interne (consultation) | Suit l'avancement sans pouvoir agir — utile pour un manager ou un reviewer interne |

**Note contexte** : la ToolBox étant host-only (pas d'accès internet), le rôle `viewer` ne concerne
que l'équipe interne ayant physiquement accès à la machine — pas le client final.

### Amélioration future possible

Peupler réellement la table `permissions` pour un contrôle plus granulaire que le simple nom de
rôle (ex: `targets.create`, `targets.delete`, `reports.generate`, `jobs.launch`), en utilisant le
décorateur `@require_permission()` déjà présent mais inutilisé dans `rbac.py`.

---

## 🎯 FEATURE 10 : Verrouillage de l'Environnement en Mode Production (Haute Priorité)

### Problème

Une fois la ToolBox déployée en mission réelle ("mode production"), il faut empêcher les
pentesters d'altérer le code de l'application (accidentellement ou volontairement), tout en
leur laissant les droits `sudo` nécessaires aux outils natifs (Metasploit, Aircrack-ng, tcpdump).

### Nuance importante

Avoir `sudo` sur la machine (nécessaire pour `nmap -sS`, `tcpdump`, `aircrack-ng` en mode monitor,
`msfconsole`) ne protège **pas** automatiquement contre une modification volontaire du code de la
ToolBox — avec un `sudo` complet, aucune protection technique n'est totalement inviolable.
La vraie réponse combine **restriction technique** + **traçabilité/responsabilité procédurale**.

### Stratégie de verrouillage recommandée (par ordre de robustesse croissante)

**1. `sudoers` restreint** (essentiel) — autoriser `sudo` uniquement pour les binaires nécessaires
   (`nmap`, `tcpdump`, `aircrack-ng`, `msfconsole`), jamais un `sudo` total :
   ```
   pentester ALL=(ALL) NOPASSWD: /usr/bin/nmap, /usr/sbin/tcpdump, /usr/sbin/airmon-ng, /usr/bin/msfconsole
   ```

**2. Permissions filesystem** — dossier projet appartenant à `root`, lecture seule pour le
   compte pentester :
   ```bash
   sudo chown -R root:root ~/Desktop/ToolBox_M1/pentest-toolbox-v2
   sudo chmod -R 750 ~/Desktop/ToolBox_M1/pentest-toolbox-v2
   ```

**3. Comptes séparés** — le compte avec accès au dossier projet (admin) est distinct du compte
   utilisé pour les commandes sudo ciblées (pentester).

**4. Conteneurs Docker en lecture seule** en production :
   ```yaml
   volumes:
     - ./ui:/app/ui:ro
     - ./core:/app/core:ro
   ```
   Empêche l'écriture même avec un accès filesystem, et impose un redémarrage visible pour
   toute modification légitime.

**5. Audit log systématique** (déjà présent — table `audit_logs`) — toute action reste tracée et
   imputable, ce qui dissuade et permet d'enquêter a posteriori.

**6. Tag Git figé par mission** — déployer une version stable taguée (`v1.0-mission-ACME`) plutôt
   que la branche `main` en mouvement, pour garantir la reproductibilité et la non-régression
   pendant la durée de la mission.

### Conclusion

Combiner **1 + 2 + 5** est réaliste et suffisant pour un contexte académique/MVP. Les points
3, 4 et 6 sont des renforcements supplémentaires pour un déploiement professionnel réel.

---

## 📊 Priorités d'implémentation (mise à jour 19 juin 2026)

| Feature | Priorité | Effort | Impact | Quand |
|---------|----------|--------|--------|-------|
| **Scope Enforcement (targets)** | 🔴 Haute | 1-2j | ⭐⭐⭐⭐⭐ | Phase 4 |
| **Verrouillage mode production** | 🔴 Haute | 0.5-1j | ⭐⭐⭐⭐ | Phase 4 |
| **Missions** | 🔴 Haute | 3j | ⭐⭐⭐⭐⭐ | Phase 4 |
| **Backup/Restore** | 🔴 Haute | 1j | ⭐⭐⭐⭐ | Phase 4 |
| **Sécurisation machine dédiée** | 🟡 Moyenne | Documentation/procédure | ⭐⭐⭐⭐ | Phase 4-5 |
| **Mapping rôles RBAC + permissions** | 🟡 Moyenne | 1j | ⭐⭐⭐ | Phase 4-5 |
| **Rapport workflow consolidé** | 🟡 Moyenne | 1-2j | ⭐⭐⭐⭐ | Phase 4 |
| **Archivage** | 🟡 Moyenne | 1j | ⭐⭐⭐ | Phase 4-5 |
| **Export ZIP** | 🟡 Moyenne | 0.5j | ⭐⭐⭐ | Phase 5 |
| **Workflows paramétrables** | 🟢 Basse | 2-3j | ⭐⭐⭐ | Phase 5 |

---

**Version** : 1.2
**Mis à jour** : 19 juin 2026 (Phase 3)
**Ajouts** : Feature 7 (machine dédiée), Feature 8 (scope enforcement), Feature 9 (mapping rôles),
Feature 10 (verrouillage production)
