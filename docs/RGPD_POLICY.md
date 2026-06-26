# 🔒 RGPD & Data Protection Policy — Pentest ToolBox v2

**Version :** 2.0
**Date :** 26 juin 2026
**Scope :** Environnement de lab (réseau Host-Only isolé)

---

## Contexte & Applicabilité

Ce document définit la politique de protection des données de la ToolBox Pentest v2,
dans le cadre d'un projet académique M1 Cybersécurité (Sup de Vinci, 2025-2026).

**Ce document s'applique à :**
- ✅ Environnements de lab isolés (réseau Host-Only, pas d'accès internet)
- ✅ Tests internes sur VMs contrôlées (Metasploitable2, WebSRV, etc.)
- ✅ Données utilisateurs au sein de la ToolBox (comptes, jobs, findings)

**Ce document ne s'applique pas à :**
- ❌ Pentesting en production réelle (cadre juridique distinct requis)
- ❌ Données de clients réels (projet académique uniquement)

---

## Données collectées

### Données personnelles

| Type | Finalité | Base légale | Rétention |
|------|---------|-------------|-----------|
| Nom d'utilisateur | Authentification | Contrat / Consentement | Jusqu'à suppression du compte |
| Email | Récupération de compte | Contrat / Consentement | Jusqu'à suppression du compte |
| Hash du mot de passe | Authentification | Contrat / Consentement | Jusqu'à suppression du compte |
| Adresse IP | Audit logs, sécurité | Intérêt légitime | Durée de la mission |
| Cookies de session | État d'authentification | Contrat | Durée de la session |

### Données techniques

| Type | Finalité | Stockage |
|------|---------|---------|
| Cibles de scan (IPs, domaines, CIDR) | Exécution des jobs | PostgreSQL (`targets`, `jobs.config`) |
| Findings (vulnérabilités détectées) | Résultats de pentest | PostgreSQL (`findings`) |
| Artefacts (XML, PCAP, logs) | Preuves et rapports | MinIO (S3-compatible, local) |
| Audit logs (actions sensibles) | Sécurité et traçabilité | PostgreSQL (`audit_logs`) |

### Données NON collectées

- ❌ Données biométriques
- ❌ Données de santé ou financières
- ❌ Géolocalisation
- ❌ Tracking comportemental (pas d'analytics, pas de cookies tiers)

---

## Stockage des données

**Toutes les données restent sur la machine physique hébergeant la VM Kali.**
Aucune donnée ne quitte le réseau local. Aucune dépendance cloud.

| Composant | Technologie | Chiffrement |
|-----------|------------|-------------|
| Comptes utilisateurs | PostgreSQL | Mots de passe hachés (Werkzeug) |
| Jobs & findings | PostgreSQL | Chiffrement disque recommandé (LUKS) |
| Artefacts | MinIO (local) | Chiffrement disque recommandé (LUKS) |
| Audit logs | PostgreSQL | Non chiffré (logs structurés) |
| Secrets applicatifs | Fichier `.env` (hors Git) | Non commité |

---

## Rétention des données

| Type | Période | Remarque |
|------|---------|---------|
| Comptes utilisateurs | Jusqu'à suppression manuelle | Par l'admin ou l'utilisateur |
| Jobs & findings | Durée de la mission | Purge manuelle en fin de mission |
| Audit logs | Durée de la mission | Purge manuelle en fin de mission |
| Cookies de session | Durée de la session | Configuré dans Settings (défaut : 30 min) |

### Purge en fin de mission

La suppression des données en fin d'engagement se fait en deux étapes :

1. **Purge applicative (planifiée)** — un bouton admin dans Settings supprimera
   jobs, findings, targets, audit logs et artefacts MinIO en une seule action.
   Cette fonctionnalité n'est pas encore implémentée en v2.

2. **Destruction sécurisée du disque (recommandée)** — chiffrement LUKS + effacement
   complet de la VM. C'est la seule garantie absolue qu'aucune donnée ne subsiste.

---

## Droits des utilisateurs (RGPD)

### Droits applicables

| Droit | Article RGPD | Implémentation actuelle |
|-------|-------------|------------------------|
| Accès aux données | Art. 15 | Via l'interface : Jobs, Findings, Settings |
| Rectification | Art. 16 | Via Settings (mot de passe, préférences) |
| Effacement | Art. 17 | Suppression manuelle par l'admin (page Admin Users) |
| Portabilité | Art. 20 | Export CSV des findings disponible |
| Opposition | Art. 21 | Non applicable (pas de profilage automatisé) |

### Exercer ses droits

Pour exercer vos droits ou signaler un problème, contacter l'administrateur
de la ToolBox directement (accès local à la machine de mission).

---

## Mesures de sécurité

### Mesures techniques

| Mesure | Implémentation | Statut |
|--------|----------------|--------|
| Hachage des mots de passe | Werkzeug (PBKDF2) | ✅ Implémenté |
| RBAC | 3 rôles appliqués côté serveur (Admin, Analyst, Viewer) | ✅ Implémenté |
| Scope enforcement | Zero-trust : aucun scan sans cible autorisée | ✅ Implémenté |
| Audit logging | Toutes les actions sensibles tracées | ✅ Implémenté |
| Isolation réseau | Réseau Host-Only (pas d'exposition internet) | ✅ Recommandé |
| Isolation conteneurs | Réseau Docker segmenté | ✅ Implémenté |
| HTTPS | Non implémenté (HTTP en environnement local) | ⏳ Planifié |
| Chiffrement disque | LUKS (à configurer sur la VM hôte) | ⏳ Recommandé |

### Indépendance méthodologique

Chaque analyste ne voit que ses propres jobs et findings. Cette règle,
appliquée côté serveur, garantit qu'aucun analyste ne peut accéder
aux résultats de travaux d'un autre membre de l'équipe.

---

## Cadre légal

### RGPD / GDPR (Règlement UE 2016/679)

Principes appliqués :
- **Minimisation des données** — seules les données nécessaires sont collectées
- **Limitation des finalités** — données utilisées uniquement pour les pentests autorisés
- **Limitation de la conservation** — purge en fin de mission
- **Intégrité et confidentialité** — RBAC, hachage, isolation réseau
- **Responsabilité** — audit trail complet

### Article 323-1 du Code Pénal français

La ToolBox est utilisée **uniquement sur des cibles autorisées** :
- ✅ Machines propres (Metasploitable2, DVWA, WebSRV)
- ✅ Réseau Host-Only isolé
- ❌ Jamais sur des systèmes de production sans autorisation écrite explicite

---

## Contexte académique

Ce projet est un outil académique de recherche en cybersécurité :
- ✅ Utilisé uniquement en environnement de lab contrôlé
- ✅ Aucune donnée client réelle traitée
- ✅ Aucune utilisation commerciale
- ✅ Les membres de l'équipe sont les seuls utilisateurs (consentement implicite)

---

## Contact

**Responsable du traitement :** Carlos (@crls-cyber)
**Dépôt GitHub :** https://github.com/crls-cyber/e-pttb-msi-4-27-cs-d-2526

---

*Voir aussi : `docs/STORAGE_GOVERNANCE.md` pour la gouvernance du stockage.*
*Voir aussi : `docs/FUTURE_IMPROVEMENTS.md` pour les fonctionnalités planifiées.*
