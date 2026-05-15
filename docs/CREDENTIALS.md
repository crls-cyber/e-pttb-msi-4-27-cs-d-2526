# Credentials ToolBox M1

**Date de création :** 8-9 mai 2026

## Utilisateurs

| Service | Username | Password |
|---------|----------|----------|
| Admin Flask | admin | Test123! |

## Services

| Service | User | Password |
|---------|------|----------|
| PostgreSQL | pentest | ToolBox2026!PostgreSQL |
| MinIO | admin | ToolBox2026!MinIO |

## Clés de chiffrement

- **SECRET_KEY :** Stocké dans `.env` (ne pas commiter)
- **FERNET_KEY :** Stocké dans `.env` (ne pas commiter)

## Connexions réseau

- **API Flask :** http://localhost:5000
- **PostgreSQL :** localhost:5432 (depuis Kali) / postgres:5432 (depuis Docker)
- **Redis :** localhost:6379 (depuis Kali) / redis:6379 (depuis Docker)
- **MinIO Console :** http://localhost:9001

## Cibles de test

| Machine | IP | Rôle |
|---------|-----|------|
| WebSRV | 192.168.145.133 | Serveur web Debian (Apache + SSH) |
| WS22 | 192.168.145.10 | Active Directory (Windows Server 2022) |

---

⚠️ **IMPORTANT :** 
- Ne JAMAIS commiter le fichier `.env` dans Git
- Ce fichier CREDENTIALS.md est safe à commiter (pas de secrets réels)
- Pour usage interne uniquement (projet académique)

## Metasploit RPC (msfrpcd)

| Service | Host | Port | Password | Notes |
|---------|------|------|----------|-------|
| msfrpcd | 192.168.200.129 | 55553 | msf | Kali sur réseau NAT |

**Commande de démarrage :**
```bash
msfrpcd -P msf -S -a 0.0.0.0 &
```

**Vérification :**
```bash
netstat -tulnp | grep 55553
# Doit écouter sur 0.0.0.0:55553
```

**Configuration plugin Metasploit :**
```json
{
  "msf_host": "192.168.200.129",
  "msf_port": 55553,
  "msf_password": "msf"
}
```

---

**Dernière mise à jour :** 15 mai 2026 (ajout msfrpcd)
