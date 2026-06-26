# Storage Governance — Pentest ToolBox v2

**Version :** 2.0
**Date :** 26 juin 2026
**Statut :** Partiellement implémenté — voir détails ci-dessous

---

## Contexte

Dans le cadre d'un usage professionnel de la ToolBox (une machine dédiée par mission,
plusieurs pentests par jour), la question de la gouvernance du stockage est réelle :
jobs, findings, artefacts MinIO et audit logs s'accumulent dans le temps.

Ce document décrit l'approche retenue, ce qui est déjà en place, et ce qui est planifié.

---

## Ce qui est implémenté en v2

### Audit Trail complet

Toutes les actions sensibles sont tracées dans la table `audit_logs` :

| Action tracée | Détail |
|--------------|--------|
| Connexion utilisateur | IP, user-agent, timestamp |
| Création / suppression de target | Auteur, valeur |
| Création / suppression d'utilisateur | Auteur |
| Changement de mot de passe | Auteur |
| Lancement de workflow | Nom, target, auteur |
| Lancement de Pivot Chain | Nom, CIDR, auteur |

### Page Compliance / RGPD

La page `/en/compliance/rgpd` documente la politique de données de la ToolBox :
- Données collectées et leur durée de vie
- Principe de localité (données sur la machine uniquement)
- Recommandation de destruction sécurisée en fin de mission (chiffrement LUKS + effacement disque)
- Note sur la purge applicative (voir ci-dessous)

### Scope Enforcement

Aucune cible n'est scannable sans avoir été préalablement enregistrée comme Authorized.
Cela limite la prolifération de données non sollicitées dans la base.

---

## Purge de mission (planifiée — non implémentée en v2)

### Besoin

En fin d'engagement, la machine doit être préparée pour une nouvelle mission.
Un bouton admin dédié (page Settings) effectuerait dans l'ordre :

1. Suppression de tous les Findings
2. Suppression de tous les Jobs
3. Suppression de toutes les Targets
4. Purge des Audit logs
5. Vidage du bucket MinIO (artefacts)
6. Confirmation avec double validation (action irréversible)

### Note RGPD importante

Cette purge applicative **ne remplace pas** la destruction sécurisée du disque
(chiffrement LUKS + effacement) en fin de mission réelle.
Elle permet de préparer la machine pour un nouvel engagement sans reconstruction
Docker complète — gain de temps opérationnel, pas substitut à la politique de
sécurité physique.

---

## Gouvernance du stockage (planifiée — non implémentée en v2)

Les fonctionnalités suivantes sont documentées dans `FUTURE_IMPROVEMENTS.md`
et constituent la roadmap pour une version future :

### Monitoring du stockage

- Endpoint `GET /api/storage/stats` — état BDD, MinIO, disque
- Alertes dashboard à 80% (warning) et 90% (critique)
- Rapport hebdomadaire automatique

### Politiques de rétention

- Rétention configurable par admin (ex: 365 jours pour les jobs)
- Identification des jobs éligibles au nettoyage
- Archivage ZIP avant suppression (artefacts + rapport + CSV)

### Gestion multi-missions

- Isolation complète des données par engagement (client A vs client B)
- Archivage et comparaison dans le temps
- Condition nécessaire avant d'implémenter la purge sélective

---

## Recommandations opérationnelles (v2 actuelle)

En attendant l'implémentation complète, voici les bonnes pratiques à adopter :

1. **En fin de mission** — éteindre la VM et restaurer un snapshot propre
   (approche la plus sûre et la plus rapide)

2. **Pour libérer de l'espace** — supprimer manuellement les jobs anciens
   via l'interface (page Jobs → sélection → suppression)

3. **Pour la conformité RGPD** — ne pas conserver de données client
   au-delà de la durée contractuelle de la mission

4. **Disque plein** — `docker system prune -f` supprime les images et
   volumes Docker inutilisés (ne touche pas aux données de la ToolBox)

---

## Estimations de croissance (référence)

| Usage | Croissance annuelle estimée |
|-------|-----------------------------|
| 1 pentest/jour, 50 findings moyens | ~47 Mo (BDD + MinIO) |
| 5 pentests/jour, 100 findings moyens | ~500 Mo |

**Conclusion :** La gouvernance devient nécessaire après 1 à 2 ans d'usage intensif.
Pour un usage académique ou ponctuel, la gestion manuelle suffit.

---

*Voir aussi : `docs/FUTURE_IMPROVEMENTS.md` pour la roadmap complète.*
*Voir aussi : `docs/RGPD_POLICY.md` pour la politique de protection des données.*
