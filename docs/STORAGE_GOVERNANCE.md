# Gouvernance du Stockage —**Document créé** : 18 mai 2026 (J16)  
**Statut** : Architecture définie, implémentation Phase 4  
**Priorité** : Haute (production-ready)  
**Auteur** : Carlos

---

## 🎯 Problématique

### Sans gouvernance (situation actuelle MVP)

```
Scénario catastrophe :

- 1 pentest/jour × 365 jours = 365 jobs
- Chaque job : ~50 findings + 3 artifacts (XML, HTML, PDF)
- Croissance linéaire infinie
- Aucune alerte, aucune limite
- Risque : saturation disque → crash Docker
```
**Risques identifiés :**
- ❌ **BDD PostgreSQL** : Croissance illimitée (findings + audit_logs)
- ❌ **MinIO** : Artifacts s'accumulent (rapports, PCAP, XML)
- ❌ **Disque VM Kali** : Peut saturer silencieusement
- ❌ **Conformité RGPD** : Pas de suppression données client
- ❌ **Performance** : Requêtes lentes avec millions de lignes

---

## ✅ Solution : Système de Gouvernance Intelligent

### Principes directeurs

1. **Monitoring actif** : Dashboard affiche état stockage en temps réel
2. **Alertes proactives** : Warnings à 80%, critiques à 90%
3. **Contrôle manuel** : Aucune suppression automatique (prévenir pertes)
4. **Archivage sécurisé** : ZIP complet avant suppression
5. **Traçabilité** : Audit logs de toutes suppressions
6. **Flexibilité** : Policies configurables par admin

---

## 📊 Architecture Proposée

### 1. Table de Configuration

```sql
-- Nouvelle table : storage_policies
CREATE TABLE storage_policies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    policy_type VARCHAR(50) NOT NULL,  -- 'retention', 'quota', 'alert'
    config JSONB NOT NULL,
    enabled BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Politique de rétention (exemple)
INSERT INTO storage_policies (policy_type, config) VALUES
('retention', '{
    "job_retention_days": 365,
    "artifact_retention_days": 730,
    "auto_archive_enabled": false,
    "auto_delete_enabled": false,
    "warning_threshold_days": 330
}');

-- Politique de quotas (exemple)
INSERT INTO storage_policies (policy_type, config) VALUES
('quota', '{
    "database_max_mb": 500,
    "minio_max_gb": 10,
    "disk_max_percent": 85,
    "alert_threshold_percent": 80,
    "critical_threshold_percent": 90
}');

-- Politique d'alertes (exemple)
INSERT INTO storage_policies (policy_type, config) VALUES
('alert', '{
    "storage_warning_enabled": true,
    "email_alerts": ["admin@toolbox.local"],
    "dashboard_warning": true,
    "weekly_report": true
}');
```

### 2. Modification Table Jobs

```sql
-- Ajouter colonnes archivage/suppression
ALTER TABLE jobs ADD COLUMN archived_at TIMESTAMP;
ALTER TABLE jobs ADD COLUMN archived_by UUID REFERENCES users(id);
ALTER TABLE jobs ADD COLUMN deleted_at TIMESTAMP;
ALTER TABLE jobs ADD COLUMN deleted_by UUID REFERENCES users(id);

-- Index pour requêtes cleanup
CREATE INDEX idx_jobs_archived ON jobs(archived_at) WHERE archived_at IS NOT NULL;
CREATE INDEX idx_jobs_old ON jobs(created_at) WHERE status = 'completed';
```

---

## 🔧 Endpoints API à Implémenter

### Endpoint 1 : Monitoring Stockage

**Route :** `GET /api/storage/stats`  
**Auth :** Admin uniquement  
**Fonction :** Retourne statistiques stockage + warnings

**Réponse (exemple) :**
```json
{
  "database": {
    "size_mb": 245.8,
    "max_mb": 500,
    "percent_used": 49.2,
    "status": "ok"
  },
  "minio": {
    "size_gb": 4.3,
    "max_gb": 10,
    "percent_used": 43.0,
    "status": "ok"
  },
  "disk": {
    "percent_used": 67.2,
    "status": "ok"
  },
  "oldest_job_days": 287,
  "warnings": [
    {
      "level": "info",
      "message": "Oldest job is 287 days old (retention policy: 365 days)",
      "action": "review_old_jobs"
    }
  ]
}
```

**Logique warnings :**
```python
# Niveaux d'alerte
if percent >= 90:
    level = "critical"  # 🔴
elif percent >= 80:
    level = "warning"   # 🟡
else:
    level = "ok"        # ✅
```

---

### Endpoint 2 : Candidates au Nettoyage

**Route :** `GET /api/storage/cleanup-candidates`  
**Auth :** Admin uniquement  
**Fonction :** Liste jobs éligibles au nettoyage selon retention policy

**Réponse (exemple) :**
```json
{
  "retention_days": 365,
  "cutoff_date": "2025-05-18T00:00:00Z",
  "total_candidates": 47,
  "total_size_mb": 234.5,
  "candidates": [
    {
      "id": "abc123...",
      "plugin": "nmap",
      "created_at": "2025-01-15T10:30:00Z",
      "age_days": 488,
      "findings_count": 12,
      "artifacts_count": 3,
      "size_mb": 5.2
    },
    {
      "id": "def456...",
      "plugin": "nuclei",
      "created_at": "2025-02-10T14:20:00Z",
      "age_days": 462,
      "findings_count": 8,
      "artifacts_count": 2,
      "size_mb": 3.1
    }
  ]
}
```

**Logique :**
```python
cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
old_jobs = db.session.query(Job).filter(
    Job.created_at < cutoff_date,
    Job.status == 'completed'
).order_by(Job.created_at.asc()).all()
```

---

### Endpoint 3 : Archivage Job

**Route :** `POST /api/storage/archive-job/<job_id>`  
**Auth :** Admin uniquement  
**Fonction :** Archive complète d'un job avant suppression

**Corps requête :**
```json
{
  "include_artifacts": true,
  "reason": "Retention policy cleanup"
}
```

**Processus d'archivage :**

```
1. Créer répertoire temporaire
2. Générer rapport HTML final
3. Générer rapport PDF final
4. Exporter findings en CSV
5. Télécharger artifacts depuis MinIO
6. Créer ZIP compressé
7. Upload ZIP vers MinIO (bucket 'archives')
8. Marquer job.archived_at = NOW()
9. Créer audit log
10. Retourner lien download archive
```

**Structure ZIP :**

```
job_abc123_archive.zip
├── report_abc123.html
├── report_abc123.pdf
├── findings_abc123.csv
├── metadata.json
└── artifacts/
    ├── nmap_output.xml
    ├── nuclei_report.json
    └── screenshot.png
```

**Réponse (exemple) :**
```json
{
  "message": "Job archived successfully",
  "archive_id": "xyz789...",
  "archive_key": "archives/2026/05/job_abc123_archive.zip",
  "archive_size_mb": 15.3,
  "download_url": "/api/storage/download-archive/xyz789"
}
```

---

### Endpoint 4 : Suppression Définitive

**Route :** `DELETE /api/storage/delete-job/<job_id>`  
**Auth :** Admin uniquement  
**Fonction :** Suppression permanente job (GDPR-compliant)

**⚠️ SÉCURITÉ : Confirmation obligatoire**

**Corps requête :**
```json
{
  "confirmation": "DELETE_abc123",
  "reason": "GDPR right to erasure request"
}
```

**Validation :**
```python
# Confirmation = "DELETE_" + 8 premiers caractères job_id
expected = f"DELETE_{job_id[:8]}"
if confirmation != expected:
    return jsonify({'error': 'Invalid confirmation token'}), 400
```

**Processus de suppression :**

```
1. Vérifier job existe
2. Vérifier confirmation token
3. Supprimer findings (CASCADE)
4. Supprimer artifacts MinIO
5. Supprimer entrées artifacts BDD
6. Supprimer job
7. Créer audit log
8. Commit transaction
```

**Réponse (exemple) :**
```json
{
  "message": "Job permanently deleted",
  "job_id": "abc123...",
  "findings_deleted": 12,
  "artifacts_deleted": 3,
  "minio_size_freed_mb": 5.2,
  "deleted_by": "admin",
  "deleted_at": "2026-05-18T16:45:00Z"
}
```

**Audit log créé :**
```json
{
  "action": "job.deleted_permanent",
  "user_id": "admin_uuid",
  "resource_type": "job",
  "resource_id": "abc123...",
  "metadata": {
    "reason": "GDPR right to erasure request",
    "findings_count": 12,
    "artifacts_count": 3,
    "size_freed_mb": 5.2
  }
}
```

---

### Endpoint 5 : Download Archive

**Route :** `GET /api/storage/download-archive/<archive_id>`  
**Auth :** Admin uniquement  
**Fonction :** Télécharge archive ZIP depuis MinIO

**Réponse :** Fichier ZIP (Content-Type: application/zip)

---

## 🎨 Interface Utilisateur

### Dashboard : Section Storage Warnings

**Affichage conditionnel :** Visible uniquement si warnings présents

```html
<div class="chart-card warning-card" id="storageWarnings">
    <div class="chart-card-header">
        ⚠️ Storage Warnings
    </div>
    <div class="warning-content">
        <ul>
            <li>🔴 Database usage: 92.3% (461.5 MB / 500 MB)</li>
            <li>🟡 MinIO usage: 84.1% (8.4 GB / 10 GB)</li>
            <li>ℹ️ Oldest job is 488 days old (retention: 365 days)</li>
        </ul>
        <a href="/en/storage-management" class="btn btn-primary">
            Manage Storage
        </a>
    </div>
</div>
```

**Logique d'affichage :**
```javascript
fetch('/api/storage/stats')
    .then(r => r.json())
    .then(data => {
        if (data.warnings && data.warnings.length > 0) {
            document.getElementById('storageWarnings').style.display = 'block';
            // Populate warnings...
        }
    });
```

---

### Page : Storage Management (admin)

**Route :** `/en/storage-management`  
**Auth :** Admin uniquement

**Sections :**

#### 1. Storage Overview


```
┌─────────────────────────────────────────┐
│ 📊 Storage Overview                     │
├─────────────────────────────────────────┤
│ Database:   461.5 MB / 500 MB (92%) 🔴  │
│ MinIO:      8.4 GB / 10 GB (84%) 🟡     │
│ Disk (VM):  45.2 GB / 60 GB (75%) ✅    │
│                                         │
│ Oldest job: 488 days                    │
│ Total jobs: 1,234                       │
│ Total findings: 56,789                  │
└─────────────────────────────────────────┘
```

#### 2. Cleanup Recommendations

```
┌─────────────────────────────────────────────────────────────┐
│ 🧹 Cleanup Recommendations                                  │
├─────────────────────────────────────────────────────────────┤
│ 47 jobs eligible for cleanup (365+ days old)               │
│ Total size: 234.5 MB                                        │
│                                                             │
│ ☐ Select All                                                │
│                                                             │
│ ☐ Job #1234 (Nmap, 2025-01-15, 488 days) - 5.2 MB        │
│ ☐ Job #1235 (Nuclei, 2025-02-10, 462 days) - 3.1 MB      │
│ ☐ Job #1236 (ZAP, 2025-02-20, 452 days) - 8.7 MB         │
│ ... (44 more)                                               │
│                                                             │
│ [Archive Selected (47)] [Delete Selected (47)]             │
│                                                             │
│ ⚠️ Warning: Deletion is permanent!                         │
│ 💡 Tip: Archive jobs before deleting                       │
└─────────────────────────────────────────────────────────────┘
```

#### 3. Storage Policies

```
┌─────────────────────────────────────────────────────┐
│ ⚙️ Storage Policies                                 │
├─────────────────────────────────────────────────────┤
│ Retention Policy:                                   │
│ • Job retention: 365 days ✅ Enabled               │
│ • Artifact retention: 730 days ✅ Enabled          │
│ • Auto-archive: ❌ Disabled (manual only)          │
│ • Auto-delete: ❌ Disabled (manual only)           │
│ [Edit Policy]                                       │
│                                                     │
│ Quota Policy:                                       │
│ • Database max: 500 MB                             │
│ • MinIO max: 10 GB                                 │
│ • Alert threshold: 80%                             │
│ • Critical threshold: 90%                          │
│ [Edit Policy]                                       │
└─────────────────────────────────────────────────────┘
```

#### 4. Recent Actions

```
┌─────────────────────────────────────────────────────────┐
│ 📜 Recent Storage Actions                               │
├─────────────────────────────────────────────────────────┤
│ 2026-05-18 16:45 - Job abc123 deleted by admin         │
│ 2026-05-18 16:44 - Job abc123 archived (15.3 MB)       │
│ 2026-05-17 10:20 - 12 jobs archived by admin           │
│ 2026-05-16 14:30 - Storage policy updated by admin     │
└─────────────────────────────────────────────────────────┘
```

---

## 🔒 Sécurité & Conformité

### Prévention erreurs critiques

**1. Confirmation obligatoire suppression**
```javascript
// UI : Double confirmation
if (confirm(`Archive ces jobs avant suppression ?`)) {
    // Archivage d'abord
    await archiveJobs(selectedIds);
    
    if (confirm(`ATTENTION : Suppression définitive de ${selectedIds.length} jobs. Confirmer ?`)) {
        const token = `DELETE_${jobId.substring(0, 8)}`;
        await deleteJobs(selectedIds, token);
    }
}
```

**2. Rate limiting**
```python
# Maximum 10 suppressions par heure pour éviter erreurs masse
from flask_limiter import Limiter

limiter = Limiter(app, key_func=get_remote_address)

@api_bp.route('/storage/delete-job/<job_id>', methods=['DELETE'])
@limiter.limit("10 per hour")
@require_role('admin')
def delete_job_permanent(job_id):
    ...
```

**3. Audit trail complet**
```python
# Tout est tracé dans audit_logs
audit_log('job.archived', 'job', job_id, metadata={
    'reason': reason,
    'size_mb': size_mb,
    'archived_by': current_user.username
})

audit_log('job.deleted_permanent', 'job', job_id, metadata={
    'reason': reason,
    'findings_deleted': findings_count,
    'artifacts_deleted': artifacts_count,
    'deleted_by': current_user.username
})
```

---

### Conformité RGPD

**Droit à l'effacement (Article 17) :**
```python
@api_bp.route('/gdpr/delete-client-data', methods=['POST'])
@require_role('admin')
def gdpr_delete_client_data():
    """
    Suppression complète données client (RGPR)
    
    Requête :
    {
        "client_identifier": "Acme Corp",
        "reason": "GDPR right to erasure request",
        "confirmation": "GDPR_DELETE_ACME"
    }
    """
    client_id = request.json.get('client_identifier')
    reason = request.json.get('reason')
    confirmation = request.json.get('confirmation')
    
    # Validation confirmation
    expected = f"GDPR_DELETE_{client_id.upper().replace(' ', '_')}"
    if confirmation != expected:
        return jsonify({'error': 'Invalid confirmation'}), 400
    
    # Trouver tous les jobs liés au client
    # (Nécessite mission_id ou tagging, voir FUTURE_IMPROVEMENTS.md)
    jobs = find_jobs_by_client(client_id)
    
    deleted_count = 0
    for job in jobs:
        delete_job_permanent(job.id, reason=reason)
        deleted_count += 1
    
    audit_log('gdpr.client_data_deleted', 'client', client_id, metadata={
        'jobs_deleted': deleted_count,
        'reason': reason
    })
    
    return jsonify({
        'message': f'Client data deleted: {deleted_count} jobs',
        'client': client_id
    })
```

---

## 📈 Estimation Tailles (Référence)

### Tailles moyennes par job

| Élément | Taille moyenne | Notes |
|---------|---------------|-------|
| **Job (row BDD)** | ~500 bytes | Métadonnées + config JSON |
| **Finding (row BDD)** | ~2 KB | Titre + description + remediation |
| **Rapport HTML** | ~10 KB | Template Jinja2 rendu |
| **Rapport PDF** | ~15 KB | WeasyPrint (avec CSS) |
| **Nmap XML** | ~5 KB | Scan basique 1 cible |
| **Nuclei JSON** | ~3 KB | 10 vulns détectées |
| **PCAP capture** | ~500 KB | 5 min capture Wireshark |

### Projections croissance

**Scénario conservateur :**
- 1 pentest/jour
- 50 findings moyens/job
- 3 artifacts/job (XML, HTML, PDF)

**Croissance annuelle :**
- Jobs : 365 × 500 B = **183 KB**
- Findings : 365 × 50 × 2 KB = **36 MB**
- Rapports : 365 × (10 + 15) KB = **9 MB**
- Artifacts : 365 × 5 KB = **1.8 MB**
- **TOTAL/an : ~47 MB** (BDD + MinIO)

**Projection 5 ans :** ~235 MB (sans nettoyage)

**Scénario intensif :**
- 5 pentests/jour
- 100 findings moyens/job
- 5 artifacts/job

**TOTAL/an : ~500 MB**

**Conclusion :** Gouvernance nécessaire après **1-2 ans** d'utilisation intensive.

---

## 🎯 Plan d'Implémentation (Phase 4)

### Étape 1 : Modèle de données (J1)
- [ ] Créer table `storage_policies`
- [ ] Modifier table `jobs` (colonnes archived_at, deleted_at)
- [ ] Créer indexes performance
- [ ] Migration SQL testée
- [ ] Seed policies par défaut

### Étape 2 : Endpoints API (J2-J3)
- [ ] `GET /api/storage/stats`
- [ ] `GET /api/storage/cleanup-candidates`
- [ ] `POST /api/storage/archive-job/<id>`
- [ ] `DELETE /api/storage/delete-job/<id>`
- [ ] `GET /api/storage/download-archive/<id>`
- [ ] Tests unitaires (pytest)

### Étape 3 : Interface utilisateur (J4)
- [ ] Dashboard : section warnings
- [ ] Page `/storage-management` (admin)
- [ ] Formulaires archivage/suppression
- [ ] Confirmations doubles
- [ ] Tests UI (manuel)

### Étape 4 : Tests & Documentation (J5)
- [ ] Tests intégration end-to-end
- [ ] Guide admin (procédures)
- [ ] Vidéo démo archivage/suppression
- [ ] Update README.md

**Temps estimé :** 5 jours (1 personne)

---

## 📚 Références & Bonnes Pratiques

### Inspirations industrielles

**AWS S3 Lifecycle Policies :**
- Transition vers tiers froid après X jours
- Suppression automatique après Y jours
- Notifications avant suppression

**GitLab Artifacts Retention :**
- Retention policy configurable par projet
- Archivage automatique builds anciens
- UI cleanup avec preview taille libérée

**Sentry Data Retention :**
- 90 jours par défaut (plan gratuit)
- Extension configurable (plan payant)
- Agrégation métrics conservée après suppression events

### Principes RGPD appliqués

1. **Minimisation données** : Ne garder que le nécessaire
2. **Limitation conservation** : Retention policies claires
3. **Droit à l'effacement** : Endpoint GDPR dédié
4. **Traçabilité** : Audit logs de toutes suppressions
5. **Sécurité** : Confirmations obligatoires

---

## ⚠️ Points d'Attention

### Ce qui DOIT être manuel

- ❌ **Pas de suppression automatique** : Trop risqué (pertes données)
- ❌ **Pas d'archivage automatique** : Nécessite review admin
- ✅ **Uniquement warnings automatiques** : Alertes dashboard safe

### Ce qui PEUT être automatisé (optionnel)

- ✅ Emails hebdomadaires (rapport stockage)
- ✅ Calculs statistiques nocturnes (cron)
- ✅ Archivage ZIP en background (Celery task)

### Gestion erreurs critiques

**Si suppression échoue (MinIO down) :**
```python
try:
    minio_client.remove_object(bucket, key)
except Exception as e:
    logger.error(f'MinIO delete failed: {e}')
    # Ne pas supprimer BDD si MinIO échoue
    db.session.rollback()
    return jsonify({'error': 'MinIO unavailable'}), 503
```

**Si archivage échoue (disque plein) :**
```python
try:
    with zipfile.ZipFile(archive_path, 'w') as zipf:
        # ...
except OSError as e:
    if 'No space left' in str(e):
        return jsonify({'error': 'Disk full, cannot create archive'}), 507
```

---

## 🧪 Tests à Prévoir

### Tests unitaires
- [ ] Calcul storage stats (mock BDD)
- [ ] Filtrage cleanup candidates (dates)
- [ ] Génération archive ZIP (temp dir)
- [ ] Validation confirmation tokens
- [ ] Suppression cascade (findings → artifacts → job)

### Tests intégration
- [ ] Archivage job → vérifier ZIP dans MinIO
- [ ] Suppression job → vérifier cascade BDD + MinIO
- [ ] Warnings dashboard → seuils déclenchés correctement
- [ ] Rate limiting suppressions

### Tests manuels
- [ ] UI Storage Management (workflow complet)
- [ ] Download archive ZIP (intégrité fichiers)
- [ ] Double confirmation suppression
- [ ] Audit logs créés correctement

---

## 📝 Documentation Utilisateur Finale

### Guide Admin : Nettoyage Mensuel

**Procédure recommandée :**

1. **Consulter dashboard** (1er du mois)
   - Vérifier warnings stockage
   - Noter % utilisation BDD/MinIO

2. **Identifier candidates** (si warnings présents)
   - Aller dans Storage Management
   - Review liste jobs > 365 jours

3. **Archiver PUIS supprimer**
   - Sélectionner jobs à nettoyer
   - Clic "Archive Selected" → attend confirmation
   - Télécharger archives générées (backup externe)
   - Clic "Delete Selected" → double confirmation
   - Vérifier audit logs

4. **Vérifier libération espace**
   - Rafraîchir dashboard
   - Confirmer % utilisation diminué

**Fréquence recommandée :** 1× par mois (ou si warning 🟡)

---

## 🎓 Glossaire

| Terme | Définition |
|-------|-----------|
| **Retention policy** | Durée conservation données avant éligibilité suppression |
| **Quota policy** | Limites max stockage (BDD, MinIO, disque) |
| **Alert threshold** | Seuil % déclenchant warning (ex: 80%) |
| **Critical threshold** | Seuil % déclenchant alerte critique (ex: 90%) |
| **Archivage** | Création ZIP complet job avant suppression |
| **Suppression permanente** | Effacement définitif BDD + MinIO (GDPR-compliant) |
| **Cleanup candidate** | Job éligible nettoyage selon retention policy |
| **Audit trail** | Historique complet actions (qui, quand, quoi) |

---

**Version** : 1.0  
**Dernière mise à jour** : 18 mai 2026  
**Prochaine review** : Après implémentation Phase 4  
**Validation requise** : Admin système avant déploiement production
