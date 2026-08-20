"""
SSRF Protection and URL Security Validator.
Enforces strict scheme validation, port restrictions, hostname filtering,
DNS resolution, and private/reserved/cloud-metadata IP range blocking.
"""

import ipaddress
import socket
from urllib.parse import urlparse, urlunparse
from typing import Tuple, Optional, Set
import logging

logger = logging.getLogger(__name__)

# Private and reserved IPv4 networks
BLOCKED_IPV4_NETWORKS = [
    ipaddress.ip_network("0.0.0.0/8"),         # "This host on this network"
    ipaddress.ip_network("10.0.0.0/8"),        # Private network (RFC 1918)
    ipaddress.ip_network("100.64.0.0/10"),     # Shared address space (Carrier-grade NAT)
    ipaddress.ip_network("127.0.0.0/8"),       # Loopback
    ipaddress.ip_network("169.254.0.0/16"),    # Link-Local / Cloud Metadata (AWS/GCP/Azure)
    ipaddress.ip_network("172.16.0.0/12"),     # Private network (RFC 1918)
    ipaddress.ip_network("192.0.0.0/24"),      # IETF Protocol Assignments
    ipaddress.ip_network("192.0.2.0/24"),      # TEST-NET-1
    ipaddress.ip_network("192.88.99.0/24"),    # 6to4 Relay Anycast
    ipaddress.ip_network("192.168.0.0/16"),    # Private network (RFC 1918)
    ipaddress.ip_network("198.18.0.0/15"),     # Benchmarking
    ipaddress.ip_network("198.51.100.0/24"),   # TEST-NET-2
    ipaddress.ip_network("203.0.113.0/24"),    # TEST-NET-3
    ipaddress.ip_network("224.0.0.0/4"),       # Multicast
    ipaddress.ip_network("240.0.0.0/4"),       # Reserved for future use
    ipaddress.ip_network("255.255.255.255/32"),# Broadcast
]

# Private and reserved IPv6 networks
BLOCKED_IPV6_NETWORKS = [
    ipaddress.ip_network("::1/128"),          # Loopback
    ipaddress.ip_network("::/128"),           # Unspecified
    ipaddress.ip_network("::ffff:0:0/96"),    # IPv4-mapped IPv6
    ipaddress.ip_network("100::/64"),         # Discard prefix
    ipaddress.ip_network("2001:db8::/32"),    # Documentation
    ipaddress.ip_network("fc00::/7"),         # Unique Local (ULA)
    ipaddress.ip_network("fe80::/10"),        # Link-Local
    ipaddress.ip_network("ff00::/8"),         # Multicast
]

BLOCKED_HOSTNAMES: Set[str] = {
    "localhost",
    "localhost.localdomain",
    "metadata.google.internal",
    "instance-data",
}

ALLOWED_SCHEMES: Set[str] = {"http", "https"}
ALLOWED_PORTS: Set[int] = {80, 443, 8080, 8443}


class SSRFValidationError(Exception):
    """Raised when a URL violates SSRF security boundaries."""
    pass


class InvalidURLError(Exception):
    """Raised when a URL is malformed or uses an unsupported scheme."""
    pass


def is_ip_blocked(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    """Check if an IP address belongs to any blocked/private/reserved range."""
    if ip.is_loopback or ip.is_private or ip.is_link_local or ip.is_multicast or ip.is_reserved or ip.is_unspecified:
        return True
    
    if isinstance(ip, ipaddress.IPv4Address):
        for network in BLOCKED_IPV4_NETWORKS:
            if ip in network:
                return True
    elif isinstance(ip, ipaddress.IPv6Address):
        for network in BLOCKED_IPV6_NETWORKS:
            if ip in network:
                return True
    return False


def normalize_url(raw_url: str) -> str:
    """Clean and normalize URL: add default scheme if missing, strip fragments."""
    url = raw_url.strip()
    # If no URI scheme is provided at all (e.g. example.com), default to https://
    if "://" not in url and not url.startswith("javascript:") and not url.startswith("mailto:") and not url.startswith("data:"):
        url = "https://" + url
    
    parsed = urlparse(url)
    # Remove fragment and normalize path
    path = parsed.path if parsed.path else "/"
    normalized = urlunparse((
        parsed.scheme.lower(),
        parsed.netloc.lower(),
        path,
        parsed.params,
        parsed.query,
        ""  # Remove fragment
    ))
    return normalized


def validate_url_security(url: str, enforce_dns: bool = True) -> Tuple[str, str]:
    """
    Validate that the URL is safe from SSRF, unsupported schemes, and forbidden networks.
    
    Returns:
        Tuple of (canonical_url, resolved_ip)
    
    Raises:
        InvalidURLError: For malformed URLs or disallowed schemes/ports.
        SSRFValidationError: If destination targets private or metadata networks.
    """
    normalized = normalize_url(url)
    parsed = urlparse(normalized)

    # 1. Scheme Validation
    if parsed.scheme not in ALLOWED_SCHEMES:
        logger.warning(f"SSRF blocked: Disallowed scheme '{parsed.scheme}' for URL: {normalized}")
        raise InvalidURLError(f"Invalid URL scheme '{parsed.scheme}'. Only http:// and https:// are permitted.")

    # 2. Hostname Validation
    hostname = parsed.hostname
    if not hostname:
        raise InvalidURLError("Invalid URL: Hostname could not be parsed.")
    
    hostname_lower = hostname.lower()
    if hostname_lower in BLOCKED_HOSTNAMES or hostname_lower.endswith(".local") or hostname_lower.endswith(".internal"):
        logger.warning(f"SSRF blocked: Blacklisted hostname '{hostname}'")
        raise SSRFValidationError("Target destination is not allowed.")

    # 3. Check Direct IP input first (before port so IP is rejected with SSRFValidationError)
    try:
        direct_ip = ipaddress.ip_address(hostname_lower)
        if is_ip_blocked(direct_ip):
            logger.warning(f"SSRF blocked: Direct IP {direct_ip} belongs to reserved/private range")
            raise SSRFValidationError("Target destination is not allowed.")
    except ValueError:
        # Hostname is not an IP literal, proceed
        pass

    # 4. Port Validation
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    if port not in ALLOWED_PORTS:
        logger.warning(f"SSRF blocked: Disallowed port {port} for URL: {normalized}")
        raise InvalidURLError(f"Disallowed destination port {port}.")

    try:
        direct_ip = ipaddress.ip_address(hostname_lower)
        return normalized, str(direct_ip)
    except ValueError:
        pass

    # 5. DNS Resolution & IP Range Check
    if enforce_dns:
        try:
            addr_info = socket.getaddrinfo(hostname, port, proto=socket.IPPROTO_TCP)
            if not addr_info:
                raise SSRFValidationError("Could not resolve destination hostname.")
            
            resolved_ip_str = ""
            for family, socktype, proto, canonname, sockaddr in addr_info:
                ip_str = sockaddr[0]
                ip_obj = ipaddress.ip_address(ip_str)
                if is_ip_blocked(ip_obj):
                    logger.warning(f"SSRF blocked: Hostname '{hostname}' resolved to blocked IP: {ip_str}")
                    raise SSRFValidationError("Target destination is not allowed.")
                if not resolved_ip_str:
                    resolved_ip_str = ip_str

            return normalized, resolved_ip_str
        except socket.gaierror as e:
            logger.warning(f"DNS resolution failure for '{hostname}': {str(e)}")
            raise InvalidURLError(f"Could not resolve website hostname: {hostname}")

    return normalized, ""
