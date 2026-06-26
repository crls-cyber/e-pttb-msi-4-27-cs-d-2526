# Credentials & Configuration

## User Accounts

Default credentials are set during installation via `scripts/create_user.py`.
See [QUICKSTART_v3.md](../QUICKSTART_v3.md) for the full setup procedure.

## Services

Passwords for PostgreSQL, MinIO and Redis are defined in `deploy/.env`.
Copy `deploy/.env.example` and set your own values before starting the stack.

## Secret Keys

- **SECRET_KEY** — Flask session signing key → set in `deploy/.env`
- **FERNET_KEY** — Optional encryption key → set in `deploy/.env`

Never commit your `.env` file to Git.

## Service Endpoints (default)

| Service | URL |
|---------|-----|
| Web Interface | http://localhost:5000 |
| MinIO Console | http://localhost:9001 |
| PostgreSQL | localhost:5432 |
| Redis | localhost:6379 |

## Metasploit (optional)

The Metasploit plugin uses an upload-based approach — no RPC daemon required.
Run your exploit in msfconsole, save the log, and upload it via the ToolBox.

## Test Targets

| Machine | Role |
|---------|------|
| Metasploitable2 | Primary vulnerable target (recommended) |
| DVWA | Included in docker-compose.yml (localhost:8080) |

Adapt IP addresses to your own lab network configuration.
See [LAB_CONFIG_EXAMPLE.md](../LAB_CONFIG_EXAMPLE.md) for a full example.

## Legal Reminder

Only scan targets you own or have explicit written authorization to test.
See [Legal Notice](../README.md#legal-notice) for full details.
