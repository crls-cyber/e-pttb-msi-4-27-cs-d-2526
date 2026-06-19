"""
Scope Checker — Target authorization enforcement.

Implements a "zero trust" scope model for pentest targets:
- A target must be explicitly authorized to be scanned.
- An unauthorized entry always wins over an authorized one (fail-safe).
- The most specific matching rule wins (CIDR/wildcard specificity).
- If no authorized targets exist at all, every scan is blocked by default.

Supported scope types:
- 'ip'              : exact IP address match (e.g. "192.168.200.133")
- 'cidr'             : IP range match (e.g. "192.168.200.0/24")
- 'domain'           : exact domain match (e.g. "example.com")
- 'wildcard_domain'  : domain + all subdomains (e.g. "*.example.com")
"""
import ipaddress
import logging

logger = logging.getLogger(__name__)


class ScopeViolation(Exception):
    """Raised when a target is not within the authorized scope."""
    def __init__(self, target, reason):
        self.target = target
        self.reason = reason
        super().__init__(f"Target '{target}' is out of scope: {reason}")


def _strip_target(raw_target):
    """Normalize a target string: strip protocol, path, port, whitespace."""
    if not raw_target:
        return ''
    t = raw_target.strip()
    # Strip protocol
    for proto in ('http://', 'https://'):
        if t.startswith(proto):
            t = t[len(proto):]
    # Strip path
    t = t.split('/')[0]
    # Strip port (but keep IPv6 brackets untouched — not a concern here)
    if ':' in t and not _is_ip(t):
        t = t.split(':')[0]
    return t.lower().strip()


def _is_ip(value):
    try:
        ipaddress.ip_address(value)
        return True
    except ValueError:
        return False


def _matches(target, entry):
    """
    Check if `target` (normalized string) matches a target registry `entry`.
    Returns (matched: bool, specificity: int) — higher specificity wins.
    Specificity scale: exact_ip=100, cidr=variable (more bits=more specific),
    exact_domain=80, wildcard_domain=40.
    """
    scope_type = entry.scope_type
    value = entry.ip_or_domain.strip().lower()

    try:
        if scope_type == 'ip':
            if _is_ip(target) and target == value:
                return True, 100
            return False, 0

        elif scope_type == 'cidr':
            if not _is_ip(target):
                return False, 0
            try:
                network = ipaddress.ip_network(value, strict=False)
                ip_obj = ipaddress.ip_address(target)
                if ip_obj in network:
                    # More specific (smaller) networks score higher
                    return True, network.prefixlen
                return False, 0
            except ValueError:
                return False, 0

        elif scope_type == 'domain':
            if target == value:
                return True, 80
            return False, 0

        elif scope_type == 'wildcard_domain':
            # value may be "*.example.com" or "example.com" (treated as wildcard base)
            base = value[2:] if value.startswith('*.') else value
            if target == base or target.endswith('.' + base):
                return True, 40
            return False, 0

        else:
            logger.warning(f"Unknown scope_type '{scope_type}' for target entry {entry.id}")
            return False, 0

    except Exception as e:
        logger.error(f"Scope matching error for target='{target}' entry='{value}': {e}")
        return False, 0


def is_target_authorized(raw_target):
    """
    Check whether a target is authorized to be scanned.

    Resolution order:
    1. Find the most specific matching "unauthorized" entry -> if found, BLOCKED.
    2. Find the most specific matching "authorized" entry -> if found, ALLOWED.
    3. If no authorized entries exist at all in the system -> BLOCKED (zero trust default).
    4. If authorized entries exist but none match -> BLOCKED (zero trust).

    Args:
        raw_target: the target string as provided by the user (IP, domain, URL...)

    Returns:
        (authorized: bool, reason: str)
    """
    from core.models.target import Target
    from core.api.app import db

    target = _strip_target(raw_target)
    if not target:
        return False, "Empty or invalid target"

    all_targets = db.session.query(Target).all()
    authorized_entries   = [t for t in all_targets if t.authorized]
    unauthorized_entries = [t for t in all_targets if not t.authorized]

    # Step 1 — check unauthorized list first (fail-safe: blocked always wins)
    best_unauthorized = None
    best_unauthorized_specificity = -1
    for entry in unauthorized_entries:
        matched, specificity = _matches(target, entry)
        if matched and specificity > best_unauthorized_specificity:
            best_unauthorized = entry
            best_unauthorized_specificity = specificity

    # Step 2 — check authorized list
    best_authorized = None
    best_authorized_specificity = -1
    for entry in authorized_entries:
        matched, specificity = _matches(target, entry)
        if matched and specificity > best_authorized_specificity:
            best_authorized = entry
            best_authorized_specificity = specificity

    # Resolution: most specific rule wins; unauthorized wins on equal specificity (fail-safe)
    if best_unauthorized and best_authorized:
        if best_unauthorized_specificity >= best_authorized_specificity:
            return False, f"Blocked by unauthorized rule: {best_unauthorized.ip_or_domain}"
        else:
            return True, f"Allowed by more specific authorized rule: {best_authorized.ip_or_domain}"

    if best_unauthorized:
        return False, f"Blocked by unauthorized rule: {best_unauthorized.ip_or_domain}"

    if best_authorized:
        return True, f"Allowed by authorized rule: {best_authorized.ip_or_domain}"

    # No matching rule at all
    if not authorized_entries:
        return False, "Zero trust: no authorized targets registered in the system"

    return False, "Zero trust: target does not match any authorized entry"


def enforce_scope(raw_target):
    """
    Raise ScopeViolation if the target is not authorized.
    Use this in API routes before creating a Job.
    """
    authorized, reason = is_target_authorized(raw_target)
    if not authorized:
        logger.warning(f"Scope violation blocked: target='{raw_target}' reason='{reason}'")
        raise ScopeViolation(raw_target, reason)
    logger.info(f"Scope check passed: target='{raw_target}' reason='{reason}'")
    return True
