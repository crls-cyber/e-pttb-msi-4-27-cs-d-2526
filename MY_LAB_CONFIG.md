# MY LAB CONFIGURATION (Carlos)

**Date:** May 15, 2026  
**Host Machine:** Windows 11 Pro  
**Virtualization:** VMware Workstation 17

⚠️ **THIS FILE IS GITIGNORED** - Contains personal network topology

---

## VMware Networks

| Network | Type | Subnet | Usage |
|---------|------|--------|-------|
| VMnet1 | Host-only | 192.168.145.0/24 | Main lab network (WS22 DHCP) |
| VMnet8 | NAT | 192.168.200.0/24 | Isolated testing (Kali + Metasploitable2 only) |

---

## Virtual Machines

### Kali Linux (Attacker)
- **Host-only (eth0):** 192.168.145.100
- **NAT (eth1):** 192.168.200.129
- **RAM:** 8 GB
- **CPU:** 4 vCPU (2x2)
- **Disk:** 80 GB
- **msfrpcd:** Listening on 0.0.0.0:55553 (password: msf)

### WebSRV (Target)
- **IP:** 192.168.145.133
- **OS:** Debian 11
- **Services:** Apache 2.4, SSH, FTP
- **Role:** Vulnerable web application server

### WS22 (Infrastructure)
- **IP:** 192.168.145.10
- **OS:** Windows Server 2022
- **Role:** Active Directory Domain Controller (DHCP enabled on VMnet1)

### Metasploitable2 (Target)
- **Primary IP:** 192.168.145.102 (Host-only, DHCP from WS22)
- **Secondary IP:** 192.168.200.133 (NAT, manual config)
- **OS:** Ubuntu 8.04 (intentionally vulnerable)
- **Services:** vsftpd 2.3.4, Samba 3.x, Tomcat 5.5, PostgreSQL 8.3, MySQL 5.0
- **Note:** Secondary NAT IP used to avoid WS22 DHCP when testing Metasploit plugin

### Wazuh-SIEM (Optional)
- **IP:** 192.168.145.131
- **OS:** Ubuntu 22.04
- **Role:** SIEM for log aggregation and analysis
- **Status:** Not integrated with toolbox yet

### DVWA (Docker)
- **IP:** localhost:8080 (Docker bridge)
- **Access:** From Kali at http://localhost:8080
- **Included:** In pentest-toolbox-v2 docker-compose.yml

---

## Network Routing

**Kali can reach:**
- ✅ WebSRV (192.168.145.133) via eth0
- ✅ WS22 (192.168.145.10) via eth0
- ✅ Metasploitable2 (192.168.145.102) via eth0
- ✅ Metasploitable2 (192.168.200.133) via eth1 (NAT, preferred for Metasploit tests)
- ✅ Wazuh (192.168.145.131) via eth0
- ✅ Internet via eth1 (NAT)

**Why two IPs for Metasploitable2?**
- Primary (145.102): Assigned by WS22 DHCP, used for general testing
- Secondary (200.133): Manual static on NAT, used for Metasploit plugin to avoid WS22 dependency

---

## Metasploit Plugin Configuration

**Tested exploit:** exploit/unix/ftp/vsftpd_234_backdoor  
**Target:** 192.168.200.133 (Metasploitable2 on NAT)  
**Kali msfrpcd:** 192.168.200.129:55553  

**Example job config:**
```json
{
  "plugin": "metasploit",
  "config": {
    "target": "192.168.200.133",
    "exploit": "exploit/unix/ftp/vsftpd_234_backdoor",
    "payload": "cmd/unix/interact",
    "msf_host": "192.168.200.129",
    "msf_password": "msf"
  }
}
```

---

## Snapshots

| Snapshot Name | Date | Description |
|---------------|------|-------------|
| 00_Base_Kali_Clean | May 8 | Fresh Kali install |
| 01_Docker_Installed | May 8 | Docker + Poetry ready |
| 02_J4_Nmap_Working | May 11 | First plugin operational |
| 03_Phase2_Complete | May 14 | 11 plugins complete |
| 04_Metasploit_Tested | May 15 | Metasploit plugin validated |

