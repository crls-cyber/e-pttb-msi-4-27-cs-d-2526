# Aircrack-ng Plugin Setup Guide

## ⚠️ Prerequisites

### Hardware Requirements

The Aircrack-ng plugin requires a **WiFi adapter with monitor mode support**.

**Recommended adapters:**
- Alfa AWUS036ACH (AC1200, monitor mode)
- Alfa AWUS036NHA (N150, monitor mode)
- TP-Link TL-WN722N v1 (NOT v2 or v3)
- Panda PAU09 (N600)

**NOT compatible:**
- Built-in laptop WiFi cards (most don't support monitor mode)
- USB WiFi adapters without monitor mode
- WiFi adapters inside VMs without USB passthrough

---

## VM Configuration

### VMware Workstation

1. **Plug in USB WiFi adapter** to host machine
2. **VM Settings → USB Controller**
3. **Add → USB Device → Select your WiFi adapter**
4. **Enable "Connect USB device to this virtual machine"**
5. **Restart VM**

### VirtualBox

1. **Plug in USB WiFi adapter**
2. **VM Settings → USB**
3. **Add USB Device Filter → Select adapter**
4. **Start VM** (adapter should appear in `ip link`)

---

## Verification

### Check if adapter supports monitor mode:

```bash
# List wireless interfaces
iwconfig

# Expected output:
# wlan0     IEEE 802.11  ESSID:off/any
#           Mode:Managed  Access Point: Not-Associated

# Test monitor mode
sudo airmon-ng start wlan0

# Expected output:
# PHY	Interface	Driver		Chipset
# phy0	wlan0		rt2800usb	Ralink Technology, Corp. RT5372

# Verify monitor mode enabled
iwconfig wlan0mon

# Expected: Mode:Monitor
```

---

## Usage

### Via Toolbox UI

1. **Navigate to:** Jobs → New Scan
2. **Select plugin:** Aircrack-ng
3. **Configure:**
   - `interface`: wlan0 (your WiFi adapter)
   - `target_bssid`: AA:BB:CC:DD:EE:FF (target network MAC)
   - `channel`: 6 (optional, network channel)
   - `wordlist`: /usr/share/wordlists/rockyou.txt
   - `capture_time`: 300 (seconds to capture handshake)
4. **Launch scan**

### Via API

```bash
curl -X POST http://localhost:5000/api/jobs \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "plugin": "aircrack",
    "config": {
      "interface": "wlan0",
      "target_bssid": "AA:BB:CC:DD:EE:FF",
      "channel": 6,
      "wordlist": "/usr/share/wordlists/rockyou.txt",
      "capture_time": 300
    }
  }'
```

---

## Workflow

1. **Scan for networks:** Plugin enables monitor mode
2. **Capture handshake:** Listens for WPA/WPA2 4-way handshake (5 min default)
3. **Crack password:** Uses wordlist attack against captured handshake
4. **Report findings:**
   - Handshake captured → HIGH severity
   - Password cracked → CRITICAL severity
   - Password not found → LOW severity (good security)

---

## Troubleshooting

### "Interface wlan0 not found"

**Cause:** No WiFi adapter detected

**Solution:**
- Check USB passthrough in VM settings
- Verify adapter is plugged in
- Run `lsusb` to see if adapter is visible
- Try `sudo modprobe <driver>` if driver not loaded

### "Failed to enable monitor mode"

**Cause:** Adapter doesn't support monitor mode or driver issue

**Solution:**
- Verify adapter model supports monitor mode
- Update Kali: `sudo apt update && sudo apt upgrade`
- Check `dmesg | tail` for driver errors

### "No handshake captured"

**Cause:** No clients connected to target network during capture

**Solution:**
- Increase `capture_time` (e.g., 600 seconds)
- Wait for legitimate client activity
- Target network may have no active clients

---

## Legal & Ethical Considerations

### ⚠️ LEGAL WARNING

**Only audit networks you own or have explicit written permission to test.**

Unauthorized WiFi auditing is **illegal** in most jurisdictions under:
- Computer Fraud and Abuse Act (USA)
- Computer Misuse Act (UK)
- Similar laws in EU, Canada, Australia, etc.

**Penalties:**
- Criminal charges
- Fines
- Imprisonment

### Ethical Use

✅ **Permitted:**
- Testing your own home/business WiFi
- Penetration tests with signed authorization
- Educational labs with isolated networks

❌ **Prohibited:**
- Neighbor's WiFi (even if open)
- Public WiFi (coffee shops, airports)
- Any network without written permission

---

## Expected Output

### Successful Capture + Crack

```
Findings:

[HIGH] WPA/WPA2 handshake captured successfully
[CRITICAL] WiFi password cracked: MyPassword123

Remediation:

Change WiFi password immediately
Use 20+ character random passphrase
Consider upgrading to WPA3
```

### Capture but No Crack

```
Findings:

[HIGH] WPA/WPA2 handshake captured successfully
[LOW] Password not found in wordlist

Remediation:

Good password strength detected
Continue using strong passwords
```
---

## Known Limitations

- ❌ Cannot crack WPA3 (use WPA2 targets only)
- ❌ Requires USB WiFi adapter (built-in cards rarely work)
- ❌ VM performance slower than native Linux
- ❌ Large wordlists can take hours/days
- ❌ No clients = no handshake

---

## Alternative: Native Kali Installation

For best performance, run Aircrack-ng on **native Kali Linux** (not VM):

1. Boot Kali from USB or dual-boot
2. Plugin USB WiFi adapter
3. Run toolbox on native system
4. Full hardware access = faster cracking

---

**Version:** 1.0.0  
**Last Updated:** May 14, 2026  
**Author:** ToolBox M1 Team
