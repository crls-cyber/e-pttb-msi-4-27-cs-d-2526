# LAB_CONFIG_EXAMPLE.md — Example Lab Configuration

> **This file is an example.** Adapt all IP addresses, passwords and VM names
> to match your own lab environment.

---

## Recommended Lab Architecture

This toolbox has been developed and tested on the following lab architecture.
You do not need to reproduce it exactly — any isolated network with at least
one vulnerable target machine will work.

---

## VMware Networks (example)

| Network | Type | Subnet | Usage |
|---------|------|--------|-------|
| VMnet1 | Host-only | 192.168.10.0/24 | Main lab network |
| VMnet8 | NAT | 192.168.20.0/24 | Isolated testing (optional) |

> **Host-only** is recommended for the toolbox — it isolates all traffic
> from the internet and from the host machine's production network.

---

## Recommended Virtual Machines

### Kali Linux (Attacker — runs the ToolBox)
- **OS:** Kali Linux 2026+
- **RAM:** 8 GB recommended
- **Disk:** 80 GB
- **Network:** Host-only adapter (+ optional NAT for updates)
- **Docker:** installed and running

### Metasploitable2 (Primary target — recommended)
- **OS:** Ubuntu 8.04 (intentionally vulnerable)
- **Network:** Host-only — e.g. `192.168.10.102`
- **Services available:** vsftpd 2.3.4, Samba 3.x, Tomcat 5.5, PostgreSQL, MySQL, SSH, FTP, Telnet...
- **Download:** https://sourceforge.net/projects/metasploitable/

### DVWA — Damn Vulnerable Web Application (optional)
- **Mode:** Docker container (included in `docker-compose.yml`)
- **Access:** http://localhost:8080 from Kali
- **Note:** Already included — no separate installation needed

### Additional targets (optional)
- Any intentionally vulnerable VM (VulnHub, HackTheBox offline, etc.)
- Windows Server VM for Active Directory testing (Hydra SMB, RDP)

---

## Scope Configuration

Before launching any scan, register your targets in the ToolBox:

1. Log in as `admin`
2. Go to **Targets** → **Add Target**
3. Add each VM IP or CIDR range as **Authorized**
4. Optionally add specific IPs as **Unauthorized** (exceptions within an authorized CIDR)

Example authorized entries:
```
Type: CIDR    Value: 192.168.10.0/24    Description: Lab network
Type: IP      Value: 192.168.10.102     Description: Metasploitable2
```

---

## Metasploit Plugin (upload-based)

The Metasploit plugin uses an **upload-based** approach — no daemon required:

1. Run your exploit manually in `msfconsole` on Kali
2. Save the session log: `spool /tmp/msf_session.log`
3. Upload the log file via the ToolBox **Upload** page
4. The ToolBox parses the log and creates structured Findings

---

## Network Routing Checklist

Before running scans, verify connectivity:

```bash
# From Kali — can you reach your targets?
ping 192.168.10.102        # Metasploitable2 (adapt to your IP)
nmap -sn 192.168.10.0/24  # Discover all hosts on the segment

# Docker services running?
docker compose ps          # All services should show "Up"
```

---

## PCAP Capture (for Wireshark upload parser)

```bash
# Capture traffic on the lab interface
sudo tcpdump -i eth0 -w /tmp/capture.pcap

# Or use Wireshark GUI on Kali
# Then upload the .pcap file via ToolBox → Upload
```

---

## ⚠️ Important Reminders

- **NEVER** connect your lab VMs to the internet while running active scans
- **ALWAYS** add targets to the Authorized list before scanning (zero-trust enforcement)
- **NEVER** scan systems you do not own or have explicit written authorization to test
- Keep your `.env` file private — never commit it to Git
