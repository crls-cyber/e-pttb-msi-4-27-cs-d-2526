# 📖 Guide Complet des Pull Requests

**Projet :** Pentest Toolbox M1  
**Date :** 30 mai 2026  
**Destinataires :** Tous les collaborateurs  
**Niveau :** Débutant à intermédiaire  

---

## 📚 Table des matières

1. [Qu'est-ce qu'une Pull Request ?](#quest-ce-quune-pull-request)
2. [Workflow global](#workflow-global)
3. [Créer une PR avec Git CLI](#créer-une-pr-avec-git-cli)
4. [Créer une PR avec GitHub Web](#créer-une-pr-avec-github-web)
5. [Conventions de l'équipe](#conventions-de-léquipe)
6. [Recevoir et reviser une PR](#recevoir-et-reviser-une-pr)
7. [Scénarios complets](#scénarios-complets)
8. [Troubleshooting](#troubleshooting)

---

## Qu'est-ce qu'une Pull Request ?

### Définition simple

Une **Pull Request (PR)** est une demande de fusion d'une branche vers une autre.

**En pratique :**
1. Tu crées une branche (`feat/ma-feature`)
2. Tu fais des changements et des commits
3. Tu pushes ta branche
4. Tu ouvres une PR pour demander : "Pouvez-vous merger mes changements dans `main` ?"
5. L'équipe revoit ton code
6. Une fois approuvée (et tests passés), ta PR est mergée

### Pourquoi utiliser les PRs ?

✅ **Revue de code** : Les autres vérifient ton code avant fusion  
✅ **CI automatisé** : Les tests s'exécutent automatiquement  
✅ **Historique clair** : Chaque changement est tracé et documenté  
✅ **Collaboration** : Discussions avant merge  
✅ **Sécurité** : Protection de branche `main` — impossible de push directement  

---

## Workflow global

### Diagramme du workflow standard

```
┌─────────────────────────────────────────────────────────────┐
│  1. Créer une branche                                       │
│     $ git checkout -b feat/ma-feature                       │
└──────────────────────┬──────────────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  2. Faire des changements & commits                         │
│     $ git add <files>                                       │
│     $ git commit -m "feat: description"                     │
└──────────────────────┬──────────────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  3. Pousser la branche                                      │
│     $ git push origin feat/ma-feature                       │
└──────────────────────┬──────────────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  4. Créer la Pull Request                                   │
│     Via GitHub web ou : gh pr create                        │
└──────────────────────┬──────────────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  5. CI Pipeline s'exécute                                   │
│     ✓ Lint (flake8)                                         │
│     ✓ Tests (pytest)                                        │
└──────────────────────┬──────────────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  6. Revue de code & approbation                             │
│     L'équipe commente et approuve                           │
└──────────────────────┬──────────────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  7. Merger la PR                                            │
│     "Merge pull request" → Branche fusionnée dans main      │
└─────────────────────────────────────────────────────────────┘
```

---

## Créer une PR avec Git CLI

### Pour ceux qui préfèrent le terminal

#### Étape 1 : Préparer ton environnement local

```bash
# Aller dans le dossier du projet
cd ~/Desktop/ToolBox_M1/pentest-toolbox-v2

# Mettre à jour main (pour partir d'une base à jour)
git checkout main
git pull origin main
```

#### Étape 2 : Créer une branche

```bash
# Créer une branche avec un nom descriptif
git checkout -b feat/ma-nouvelle-feature

# Exemples de bons noms :
# feat/ajouter-plugin-nuclei
# fix/corriger-bug-api
# docs/mettre-a-jour-readme
# test/ajouter-tests-nmap
```

**Conventions de nommage (voir section dédiée plus bas)**

#### Étape 3 : Faire des changements

```bash
# Éditer tes fichiers avec ton éditeur
# (VS Code, PyCharm, nano, vi, etc.)

# Vérifier les changements
git status

# Ajouter les fichiers modifiés
git add fichier1.py fichier2.py

# Ou ajouter tous les changements
git add .

# Vérifier avant commit
git diff --staged
```

#### Étape 4 : Commiter tes changements

```bash
# Commit avec un message descriptif
git commit -m "feat: ajouter plugin nuclei avec parsing JSON"

# Ou pour un commit plus détaillé
git commit -m "feat: ajouter plugin nuclei

- Implémentation scanner vulnerabilités
- Parser JSON output
- Integration avec orchestration Celery"
```

**Format des messages (voir conventions ci-dessous)**

#### Étape 5 : Pousser la branche

```bash
# Pousser vers GitHub
git push origin feat/ma-nouvelle-feature

# Ou (première fois, pour configurer le tracking)
git push -u origin feat/ma-nouvelle-feature
```

#### Étape 6 : Créer la PR via `gh` CLI

```bash
# Créer une PR directement depuis le terminal
gh pr create \
  --title "feat: ajouter plugin nuclei" \
  --body "Implémentation du scanner Nuclei avec:
- Parsing JSON
- Integration Celery
- Tests unitaires"
```

**Ou plus simple (interactive) :**

```bash
gh pr create --web
# Cela va ouvrir GitHub dans le navigateur pour créer la PR
```

#### Étape 7 : Attendre l'approbation

```bash
# Voir le statut de ta PR
gh pr view

# Voir si les tests passent
gh pr checks

# Voir les commentaires
gh pr view --comments
```

---

## Créer une PR avec GitHub Web

### Pour ceux qui préfèrent l'interface graphique

#### Étape 1 : Accéder au repo GitHub

```
https://github.com/crls-cyber/pentest-toolbox-v2
```

#### Étape 2 : Pousser ta branche (en local d'abord)

**Tu dois d'abord avoir pushé ta branche localement :**

```bash
cd ~/Desktop/ToolBox_M1/pentest-toolbox-v2
git checkout -b feat/ma-feature
# ... faire des changements ...
git add .
git commit -m "feat: description"
git push -u origin feat/ma-feature
```

#### Étape 3 : Créer la PR sur GitHub

**Accès :** Clique sur l'onglet **"Pull requests"** (en haut du repo)

```
Code | Issues | Pull requests ← Clique ici
```

**Ou :** GitHub te propose automatiquement un bouton "Compare & pull request" après un push.

#### Étape 4 : Cliquer sur "New pull request"

Bouton vert en haut à droite.

#### Étape 5 : Configurer la PR

La page "Comparing changes" s'ouvre.

**Vérifier :**
- `base: main` ← destination (où merger)
- `compare: feat/ma-feature` ← ta branche source

**Cliquer sur "Create pull request"**

#### Étape 6 : Remplir le formulaire

**Titre :** Description courte
```
feat: ajouter plugin nuclei
```

**Description :** Explique ce que ta PR fait
```
Ajoute le plugin Nuclei pour les scans de vulnérabilités.

Changes:
- Implémentation du wrapper Nuclei
- Parser JSON output
- Tests unitaires

Closes: #123 (si elle corrige une issue)
```

**Cliquer "Create pull request"**

#### Étape 7 : Vérifier le statut

- ✅ CI Pipeline s'exécute (2-3 minutes)
- ✅ Checks passent = feu vert
- ✅ CODEOWNERS assignés automatiquement en reviewers

#### Étape 8 : Attendre la revue

L'équipe va :
- Lire ton code
- Commenter les lignes
- Approuver ou demander des changements

---

## Conventions de l'équipe

### 1. Nommage des branches

**Format :** `<type>/<description-courte>`

| Type | Usage | Exemple |
|------|-------|---------|
| `feat/` | Nouvelle fonctionnalité | `feat/plugin-nuclei` |
| `fix/` | Correction bug | `fix/api-timeout` |
| `docs/` | Documentation | `docs/update-readme` |
| `test/` | Tests | `test/coverage-plugins` |
| `refactor/` | Refactorisation code | `refactor/simplify-orm` |
| `chore/` | Maintenance (dépendances, config) | `chore/update-dependencies` |

**Règles :**
- Utilise des **tirets** (`-`), pas des underscores
- Minuscules uniquement
- Court et descriptif (2-4 mots)
- Pas d'espaces

**✅ BONS NOMS :**
- `feat/add-nmap-plugin`
- `fix/handle-empty-response`
- `docs/api-endpoints`

**❌ MAUVAIS NOMS :**
- `feature/...` (utilisez `feat/`)
- `My_New_Feature` (tirets + minuscules)
- `work-in-progress` (trop vague)

### 2. Messages de commit

**Format Conventional Commits :**

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Exemple complet :**

```
feat(plugins/nuclei): add JSON output parser

Implement parsing of Nuclei JSON output to extract:
- CVE identifiers
- Severity levels
- Remediation steps

Map findings to internal Finding model for storage.

Closes #42
```

**Types :**
- `feat:` Nouvelle fonctionnalité
- `fix:` Correction bug
- `docs:` Documentation
- `test:` Tests
- `refactor:` Refactorisation
- `chore:` Maintenance

**Scope (optionnel) :**
- `plugins/nuclei`, `api/auth`, `ui/dashboard`, etc.

**Subject :**
- Impératif ("add" pas "added")
- Pas de point à la fin
- < 50 caractères
- En anglais (convention industrie)

**Body (optionnel mais recommandé) :**
- Explique le **pourquoi**, pas le quoi
- 72 caractères par ligne
- Séparer du subject par une ligne vide

**Footer (optionnel) :**
- Références issues : `Closes #123`, `Fixes #456`
- Breaking changes : `BREAKING CHANGE: ...`

### 3. Checklist avant de créer la PR

**Avant de pousser, vérifie :**

- [ ] Ma branche est à jour avec `main`
  ```bash
  git fetch origin
  git rebase origin/main
  ```

- [ ] J'ai testé localement
  ```bash
  poetry run pytest
  poetry run flake8
  ```

- [ ] Pas de fichiers temporaires commitées
  ```bash
  git status  # Doit être propre
  ```

- [ ] Messages de commit sont clairs
  ```bash
  git log origin/main..HEAD
  ```

- [ ] Documentation à jour (si applicable)
  - README.md
  - docs/ (si nouvelles features)
  - Docstrings Python

- [ ] `.env` et secrets **jamais** commitées
  ```bash
  grep -r "password\|secret\|api_key" --include="*.py" .
  ```

---

## Recevoir et reviser une PR

### Pour les reviewers

#### Accéder à une PR

**Onglet "Pull requests" → Clique sur le titre de la PR**

#### Lire la description

Comprendre ce que la PR fait et pourquoi.

#### Analyser les changements

Onglet **"Files changed"**

- 🟢 Vert = ajouté
- 🔴 Rouge = supprimé
- ⚪ Gris = contexte

#### Commenter le code

**Hover sur une ligne → Clique sur le `+` → Écris un commentaire**

Exemples :
```
"Pourquoi on utilise `json.loads()` ici au lieu de notre parser custom ?"

"Cette ligne est vide, peux-tu la supprimer ?"

"Excellente implémentation !"
```

#### Approuver ou demander des changements

**Bouton "Review changes"** (en haut à droite)

- ✅ **Approve** : "Looks good to me, peut être mergée"
- 📝 **Comment** : "Quelques suggestions mineures"
- ❌ **Request changes** : "Doit être modifié avant merge"

#### CI Pipeline

**Si les tests échouent :**
1. Clique sur "Details" dans le statut des checks
2. Lis les logs d'erreur
3. Commente avec le problème
4. Attends que l'auteur corrige

---

## Scénarios complets

### Scénario 1 : Ajouter une petite correction

**Situation :** Tu dois fixer un bug mineur dans l'API.

**Via CLI :**

```bash
cd ~/Desktop/ToolBox_M1/pentest-toolbox-v2

# Mettre à jour main
git checkout main
git pull origin main

# Créer branche
git checkout -b fix/api-auth-timeout

# Éditer le fichier problématique
# (ex: core/api/auth.py)
nano core/api/auth.py
# ... change timeout de 30s à 60s ...

# Commit
git add core/api/auth.py
git commit -m "fix(api/auth): increase login timeout to 60 seconds"

# Push
git push origin fix/api-auth-timeout

# Créer PR
gh pr create --web
```

**Sur GitHub :**
- Titre : "fix: increase login timeout to 60 seconds"
- Description : "Users on slow connections were getting logged out. Increased timeout from 30 to 60 seconds."

**Attendre :**
- CI passe (1-2 min)
- Quelqu'un approuve
- Auto-merge

---

### Scénario 2 : Ajouter un nouveau plugin

**Situation :** Tu dois ajouter le plugin subfinder (reconnaissance DNS).

**Via CLI :**

```bash
cd ~/Desktop/ToolBox_M1/pentest-toolbox-v2
git checkout main
git pull origin main

# Créer branche
git checkout -b feat/add-subfinder-plugin

# Créer la structure du plugin
mkdir plugins/subfinder
touch plugins/subfinder/__init__.py
touch plugins/subfinder/plugin.py
touch plugins/subfinder/parser.py

# Éditer les fichiers (plugin.py, parser.py, etc.)
# ... code du plugin ...

# Tests
poetry run pytest tests/unit/test_subfinder_plugin.py

# Ajouter et commiter (plusieurs commits si besoin)
git add plugins/subfinder/
git commit -m "feat(plugins/subfinder): add DNS enumeration plugin

Implement Subfinder integration:
- Enumerate subdomains from various sources
- Parse output to domain list
- Integrate with Celery orchestration
- Add unit tests

Closes #35"

# Peut ajouter plus de commits si needed
git add tests/
git commit -m "test(plugins/subfinder): add integration tests"

# Push
git push origin feat/add-subfinder-plugin

# Créer PR
gh pr create --web
```

**Sur GitHub :**
- Titre : "feat: add subfinder plugin for DNS enumeration"
- Description complète avec features

**Attendre :**
- CI passe
- Revue détaillée (plusieurs commentaires)
- Peut demander des modifications
- Une fois approuvé → merge

---

### Scénario 3 : Corriger les commentaires d'une PR

**Situation :** La revue demande des changements.

**Message du reviewer :**
```
"La fonction `parse_output()` devrait avoir une docstring expliquant le format JSON attendu."
```

**Tu corriges :**

```bash
# Tu es déjà sur ta branche feat/...
# Éditer le fichier
nano plugins/subfinder/parser.py

# Ajouter la docstring
# def parse_output(json_output):
#     """Parse Subfinder JSON output into domain list.
#     
#     Args:
#         json_output (str): Subfinder JSON output
#     
#     Returns:
#         list: List of found domains
#     """

# Commit (pas besoin de nouveau push, juste add/commit)
git add plugins/subfinder/parser.py
git commit -m "docs(plugins/subfinder): add docstring to parse_output"

# Push le commit à la même branche
git push origin feat/add-subfinder-plugin
```

**GitHub :**
- Le commit aparait automatiquement dans la PR
- Clique sur "Resolve" pour marquer le commentaire comme résolu
- Le reviewer peut re-approuver

---

## Troubleshooting

### Problème 1 : "Your branch has diverged from origin/main"

**Symptôme :**
```
Your branch and 'origin/main' have diverged,
and have 2 and 3 different commits each, respectively.
```

**Cause :** `main` a des nouveaux commits et ta branche aussi. Conflit de merge potentiel.

**Solution :**

```bash
# Option 1 : Rebase (recommandé)
git fetch origin
git rebase origin/main

# Si conflit, Git va te montrer les fichiers à résoudre
# Résous les conflits dans les fichiers
# Puis continue
git rebase --continue
git push origin feat/ma-feature --force-with-lease
```

**Ou Option 2 : Merge**

```bash
git fetch origin
git merge origin/main
git push origin feat/ma-feature
```

---

### Problème 2 : "CI Pipeline failed"

**Symptôme :** La PR montre une ✗ rouge au lieu de ✓ verte.

**Actions :**

1. Clique sur "Details" pour voir les logs
2. Regarde l'erreur (flake8 ou pytest)
3. Corrige le code localement

**Exemple : Erreur flake8**
```
E501 line too long (95 > 88 characters)
```

Correction :
```bash
# Éditer le fichier
nano plugins/subfinder/plugin.py

# Raccourcir la ligne (ajouter retour à la ligne)
# Au lieu de:
# long_variable = some_function_that_does_stuff(param1, param2, param3, param4)
# Faire:
# long_variable = some_function_that_does_stuff(
#     param1, param2, param3, param4)

git add plugins/subfinder/plugin.py
git commit -m "fix: comply with flake8 line length requirement"
git push origin feat/ma-feature
```

Le CI redémarre automatiquement.

---

### Problème 3 : Conflit de merge

**Symptôme :**
```
CONFLICT (content merge): Merge conflict in core/api/auth.py
Automatic merge failed; fix conflicts and then commit the result.
```

**Solution :**

```bash
# Voir les fichiers en conflit
git status

# Éditer le fichier problématique
nano core/api/auth.py

# Git aura marqué les conflits ainsi :
# <<<<<<< HEAD (current change)
# mon code
# =======
# leur code
# >>>>>>> origin/main

# Décider quelle version garder
# Supprimer les marqueurs <<<<, ====, >>>>

# Une fois résolu
git add core/api/auth.py
git commit -m "resolve: merge conflict in auth.py"
git push origin feat/ma-feature
```

---

### Problème 4 : "Branch is out of date"

**Symptôme :** Le message "This branch is out of date with the base branch" aparait.

**Cause :** `main` a eu de nouveaux commits.

**Solution :**

```bash
git fetch origin
git rebase origin/main
git push origin feat/ma-feature --force-with-lease
```

Ou sur GitHub : Clique sur "Update branch" (bouton automatique).

---

### Problème 5 : J'ai accidentellement committed un secret

**Symptôme :** Tu as committé un mot de passe ou API key.

**Solution IMMÉDIATE :**

```bash
# NE PAS PUSH
# Annuler le commit
git reset --soft HEAD~1

# Retirer le fichier secret du staging
git reset core/config.py

# Éditer .gitignore pour l'ajouter
nano .gitignore
# ajouter : core/config.py

# Ajouter les autres fichiers
git add .
git commit -m "chore: don't commit secrets"
git push origin feat/ma-feature
```

**Si déjà pushé :**
```bash
# Contact Carlos IMMÉDIATEMENT pour faire un force-push
```

---

## Checklist finale avant de merger

**Reviewer (personne qui approuve) :**

- [ ] Code lisible et bien commenté
- [ ] Tests unitaires ajoutés/modifiés
- [ ] Documentation à jour
- [ ] Pas de secrets committes
- [ ] Messages de commit clairs
- [ ] Respect des conventions

**Système automatique :**

- ✅ CI Pipeline passe (flake8 + pytest)
- ✅ Pas de conflits avec main
- ✅ CODEOWNERS ont approuvé (ou leur notification)

**Merger :**

- Sur la PR : Clique "Merge pull request"
- Confirme
- Branche est maintenant dans `main` ✅

---

## Questions fréquentes

**Q : Je dois ajouter des fichiers à ma PR après la création ?**  
R : Oui, fais juste des commits supplémentaires sur ta branche et push. La PR se met à jour automatiquement.

**Q : Je peux merger ma propre PR ?**  
R : Non, protection de branche l'interdit. Quelqu'un d'autre doit approuver.

**Q : Combien de temps avant que ma PR soit mergée ?**  
R : Ça dépend. Petites fixes : 1-2 jours. Gros changements : 3-5 jours.

**Q : Ma PR a un conflit, que faire ?**  
R : Voir section Troubleshooting → Problème 3.

**Q : Comment garder ma branche à jour avec main ?**  
R : `git fetch origin && git rebase origin/main && git push origin feat/... --force-with-lease`

---

## Support et aide

**Problème non résolu ?**

1. Regarde le Troubleshooting
2. Demande sur Discord/Slack de l'équipe
3. Contacte Carlos (@crls-cyber)

---

**Fin du guide**

**Version :** 1.0  
**Date :** 30 mai 2026  
**Responsable :** Carlos (@crls-cyber)  
**Dernière révision :** 30 mai 2026
