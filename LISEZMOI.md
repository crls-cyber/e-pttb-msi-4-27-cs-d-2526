# 🛡️ ToolBox Pentest — Projet M1 Cybersécurité

**Plateforme d'automatisation de tests d'intrusion**

[![Licence](https://img.shields.io/badge/licence-CC--BY--NC--ND--4.0-lightgrey.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/docker-24.0+-blue.svg)](https://www.docker.com/)
[![Statut](https://img.shields.io/badge/statut-v2.0%20complet-success.svg)]()

> **Projet académique** — M1 Cybersécurité, Sup de Vinci (2025-2026)
> ToolBox modulaire d'automatisation de pentests avec RBAC, Pivot Chains data-driven, reporting professionnel et orchestration Docker.

---

## 📋 Sommaire

- [Vue d'ensemble](#vue-densemble)
- [Fonctionnalités](#fonctionnalités)
- [Architecture](#architecture)
- [Stack technique](#stack-technique)
- [Démarrage rapide](#démarrage-rapide)
- [Plugins](#plugins)
- [Documentation](#documentation)
- [Sécurité](#sécurité)
- [Mentions légales](#mentions-légales)
- [Licence](#licence)

---

## 🎯 Vue d'ensemble

**Pentest ToolBox v2** est une plateforme modulaire de tests d'intrusion conçue pour :
- ✅ **Automatiser** les phases de reconnaissance, scan et exploitation
- ✅ **Réduire** le temps de réalisation d'un pentest via des workflows orchestrés et des Pivot Chains data-driven
- ✅ **Standardiser** les pratiques avec des plugins réutilisables et auto-découverts
- ✅ **Sécuriser** les accès avec RBAC et contrôle de périmètre zero-trust
- ✅ **Générer** des rapports professionnels (HTML, PDF, CSV)

**Utilisateurs cibles :** Analystes sécurité, pentesters, équipes SOC, chercheurs académiques.

---

## ✨ Fonctionnalités

### 🔌 13 Outils intégrés

**Flux A — Plugins Docker automatisés (8)**

| Plugin | Phase | Capacité |
|--------|-------|---------|
| **Nmap** | Reconnaissance | Scan réseau, détection ports et services |
| **Nuclei** | Vulnérabilités | Détection CVE (5000+ templates) |
| **SQLmap** | Exploitation | Automatisation injections SQL |
| **Hydra** | Accès credentials | Brute-force (SSH, FTP, SMB, MySQL, RDP...) |
| **Subfinder** | OSINT | Énumération passive de sous-domaines DNS |
| **theHarvester** | OSINT | Collecte emails, hosts, IPs via moteurs de recherche |
| **WhatWeb** | Fingerprinting | Identification technologies web |
| **ZAP (OWASP)** | Audit web | Scan actif vulnérabilités web (XSS, CSRF...) |

**Flux C — Parseurs Upload (5)**

| Outil | Format importé | Phase |
|-------|---------------|-------|
| **Metasploit** | Log (.log) | Exploitation / Post-exploitation |
| **Burp Suite** | Export XML (.xml) | Audit web avancé |
| **Wireshark** | PCAP (.pcap) | Analyse réseau / Forensique |
| **Aircrack-ng** | Log (.txt) | Audit Wi-Fi |
| **Ettercap** | Log (.txt) | Man-in-the-Middle |

### 🔄 7 Workflows séquentiels

Enchaînements en un clic sur une cible fixe :

| Workflow | Chaîne |
|----------|--------|
| Recon-to-Exploit | Nmap → Nuclei → Hydra |
| Web Pentest Advanced | Nmap → Nuclei → SQLmap |
| Web App Audit | WhatWeb → ZAP → SQLmap |
| Network Bruteforce | Nmap → Hydra |
| OSINT Reconnaissance | theHarvester → Subfinder |
| Quick Vuln Scan | Nmap → Nuclei |
| Full External Recon | Subfinder → theHarvester → Nmap → WhatWeb |

### 🔀 3 Pivot Chains data-driven

Contrairement aux workflows séquentiels, les Pivot Chains créent les jobs suivants **dynamiquement**, en fonction des résultats réels de l'étape précédente :

| Pivot Chain | Logique | Résultat testé |
|-------------|---------|---------------|
| **Network Pivot Discovery** | Nmap (CIDR) → [par hôte découvert] → Nuclei + WhatWeb | 4 hôtes découverts, 8 jobs créés dynamiquement ✅ |
| **Credential Access Discovery** | Nmap (ports auth) → [par service ouvert] → Hydra | 10 services trouvés, 10 jobs Hydra lancés précisément ✅ |
| **Exploitation Readiness Report** | Nmap + Nuclei → [analyse findings] → Recommandations Metasploit | Backdoor vsftpd 2.3.4 identifié avec module précis, 15+ hints CVE ✅ |

### 📊 Reporting professionnel

- **Rapport par job** — HTML / PDF avec score CVSS, CVE, description, remédiation
- **Rapport global** — tous les findings de tous les jobs complétés
- **Rapport personnalisé** — filtré par cible, plugin et/ou plage de dates
- **Export CSV** — pour analyse externe

### 🔐 Sécurité intégrée

- **Authentification** — Flask-Login, mots de passe hachés (Werkzeug)
- **RBAC** — 3 rôles appliqués côté serveur (Admin, Analyst, Viewer)
- **Scope Enforcement** — Zero-trust : aucun scan sans cible préalablement autorisée
- **Audit Logs** — toutes les actions sensibles tracées
- **Indépendance méthodologique** — chaque analyste ne voit que ses propres jobs/findings

---

## 🏛️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              UTILISATEURS (Analystes)                       │
│              Interface web EN/FR (thème Delta OS)           │
└────────────────────┬────────────────────────────────────────┘
                     │
         ┌───────────────────────┐
         │   UI + API (Flask)    │
         │   Port 5000           │
         │   Auth + RBAC         │
         │   13 pages dédiées    │
         └───────────┬───────────┘
                     │
        ┌────────────┴────────────┐
        ▼                         ▼
┌───────────────┐         ┌──────────────┐
│  PostgreSQL   │         │    Redis     │
│  Jobs         │         │   Broker     │
│  Findings     │         │   Celery     │
│  Utilisateurs │         └──────┬───────┘
│  Audit logs   │                │
└───────────────┘                ▼
                    ┌─────────────────────────┐
                    │   Celery Worker          │
                    │   4 processus parallèles │
                    └──────────┬──────────────┘
                               │
              ┌────────────────┴────────────────┐
              ▼                                  ▼
   ┌─────────────────────┐          ┌──────────────────────┐
   │  Flux A : Docker    │          │  Flux C : Upload     │
   │  8 outils automatisés│         │  5 parseurs externes │
   └──────────┬──────────┘          └──────────────────────┘
              ▼
   ┌─────────────────────┐
   │       MinIO          │
   │  Stockage artefacts  │
   │  (compatible S3)     │
   └─────────────────────┘
```

**Décisions d'architecture clés :**
- **Celery** plutôt que threading — vrai async, retry, monitoring
- **MinIO** plutôt que filesystem — compatible S3, prêt pour le cloud
- **Flask** — recommandé par le cahier des charges, écosystème mature
- **Auto-découverte des plugins** — ajouter un outil sans toucher au core

---

## 🧰 Stack technique

| Composant | Technologie | Version |
|-----------|-------------|---------|
| Langage | Python | 3.11+ |
| Framework web | Flask | 3.0+ |
| ORM | SQLAlchemy | 2.0+ |
| Jobs asynchrones | Celery | 5.3+ |
| Broker | Redis | 7.0+ |
| Base de données | PostgreSQL | 15+ |
| Stockage objets | MinIO | Latest |
| Conteneurs | Docker Compose | V2 |
| Gestion dépendances | Poetry | 1.7+ |
| Génération PDF | WeasyPrint | 62.0+ |
| CI/CD | GitHub Actions | — |

---

## 🚀 Démarrage rapide

### Prérequis

- **OS :** Kali Linux 2026+ (ou Debian/Ubuntu 22.04+)
- **Docker :** 24.0+
- **Docker Compose :** V2
- **RAM :** 4 Go minimum, 8 Go recommandés
- **Disque :** 20 Go minimum

### Installation

```bash
# 1. Cloner le dépôt
git clone https://github.com/crls-cyber/e-pttb-msi-4-27-cs-d-2526.git
cd e-pttb-msi-4-27-cs-d-2526

# 2. Configurer les variables d'environnement
cp deploy/.env.example deploy/.env
nano deploy/.env  # Modifier les mots de passe et secrets

# 3. Démarrer tous les services
docker compose up -d

# 4. Attendre l'initialisation (~30 secondes)
sleep 30

# 5. Initialiser la base de données
docker compose exec api python scripts/init_db.py

# 6. Créer l'utilisateur admin
docker compose exec api python scripts/create_user.py \
  --username admin \
  --password VotreMotDePasseFort \
  --email admin@toolbox.local \
  --role admin

# 7. Ouvrir l'interface web
firefox http://localhost:5000
```

### Premiers pas

1. Se connecter en tant qu'`admin`
2. Aller dans **Targets** → ajouter les cibles autorisées (IP, CIDR, domaine)
3. Aller dans **Workflows** ou **Pivot Chains** → lancer un premier scan
4. Les résultats apparaissent dans **Jobs** → **Findings**

---

## 🔌 Plugins

### Plugins Docker automatisés (8)

| Plugin | Statut | Notes |
|--------|--------|-------|
| Nmap | ✅ Opérationnel | Détection de services, plages CIDR supportées |
| Nuclei | ✅ Opérationnel | 5000+ templates CVE |
| SQLmap | ✅ Opérationnel | Paramètre sqli_url optionnel |
| Hydra | ✅ Opérationnel | Userlist en liste Python supportée |
| Subfinder | ✅ Opérationnel | Noms de domaine uniquement (pas d'IPs) |
| theHarvester | ✅ Opérationnel | Timeout possible sur sources rate-limitées (connu) |
| WhatWeb | ✅ Opérationnel | |
| ZAP (OWASP) | ⚠️ Partiel | Bug spider sans timeout identifié, correction planifiée |

### Parseurs Upload (5)

| Outil | Statut |
|-------|--------|
| Metasploit | ✅ Opérationnel |
| Burp Suite | ✅ Opérationnel |
| Wireshark | ✅ Opérationnel |
| Aircrack-ng | ✅ Opérationnel |
| Ettercap | ✅ Opérationnel |

### Ajouter un plugin

Chaque plugin étend `PluginBase` et implémente trois méthodes :
- `validate_config()` — validation des paramètres
- `run()` — exécution de l'outil via subprocess
- `parse_output()` — sortie brute → Findings structurés

Les plugins sont **auto-découverts** au démarrage — aucune modification du core nécessaire.

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [QUICKSTART_v3.md](QUICKSTART_v3.md) | Guide de démarrage pas à pas |
| [PLAN_DEVELOPPEMENT_v3.md](PLAN_DEVELOPPEMENT_v3.md) | Plan de développement |
| [CHECKLIST_PRELANCEMENT_v3.md](CHECKLIST_PRELANCEMENT_v3.md) | Checklist pré-lancement |
| [docs/FUTURE_IMPROVEMENTS.md](docs/FUTURE_IMPROVEMENTS.md) | Roadmap et fonctionnalités planifiées |
| [architecture_pentest_toolbox_v6_1.md](architecture_pentest_toolbox_v6_1.md) | Architecture détaillée |

---

## 🔐 Sécurité

### Contrôles intégrés

- ✅ Hachage des mots de passe (Werkzeug)
- ✅ RBAC appliqué côté serveur
- ✅ Scope enforcement zero-trust (aucun scan non autorisé)
- ✅ Audit trail (toutes les actions sensibles tracées)
- ✅ Sécurité des sessions (cookies signés Flask-Login)

### Recommandation de déploiement

Cette ToolBox est conçue pour des **machines dédiées par mission** — une machine par engagement. Les données restent locales par défaut. Aucune dépendance cloud requise.

### Limite connue

Le spider ZAP (`_wait_for_spider()`) ne dispose pas de paramètre timeout — peut bloquer indéfiniment sur certaines cibles. Correction planifiée. Contournement : redémarrer le worker en cas de blocage.

---

## ⚖️ Mentions légales

**Ce projet est un outil académique de recherche en sécurité.**

**Article 323-1 du Code Pénal français :**
> Le fait d'accéder ou de se maintenir, frauduleusement, dans tout ou partie d'un système de traitement automatisé de données est puni de deux ans d'emprisonnement et de 60 000 € d'amende.

**N'utilisez cette ToolBox QUE sur :**
- ✅ Vos propres systèmes
- ✅ Des systèmes avec autorisation écrite explicite
- ✅ Des cibles de lab autorisées (Metasploitable2, DVWA, etc.)

**❌ Ne scannez JAMAIS des systèmes sans autorisation préalable écrite.**

Les auteurs déclinent toute responsabilité en cas d'utilisation illégale de cet outil.

---

## 📄 Licence

Ce projet est distribué sous licence **CC BY-NC-ND 4.0**
(Attribution — Pas d'Utilisation Commerciale — Pas de Modification)

Voir [LICENSE](LICENSE) pour les conditions complètes.

---

## 🎓 Contexte académique

**Établissement :** Sup de Vinci — M1 Cybersécurité
**Période :** Décembre 2025 – Juin 2026
**Équipe :** Carlos (@crls-cyber), Emeric (@freezy-ted), Antoine (@ItsJinmaa), Elsy (@nker-svg)

---

**Version :** v2.0
**Dernière mise à jour :** 26 juin 2026
**Statut :** ✅ Complet
