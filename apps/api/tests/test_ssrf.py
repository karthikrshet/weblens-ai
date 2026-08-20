"""
Unit tests for SSRF Protection and URL Security.
"""

import pytest
from app.security.ssrf import (
    validate_url_security,
    normalize_url,
    SSRFValidationError,
    InvalidURLError,
)


def test_normalize_url():
    assert normalize_url("example.com") == "https://example.com/"
    assert normalize_url("http://example.com/about#section") == "http://example.com/about"
    assert normalize_url("https://EXAMPLE.com/path?query=1") == "https://example.com/path?query=1"


def test_block_loopback_ip():
    with pytest.raises(SSRFValidationError):
        validate_url_security("http://127.0.0.1:8000", enforce_dns=False)
    with pytest.raises(SSRFValidationError):
        validate_url_security("http://127.0.0.254", enforce_dns=False)


def test_block_private_networks():
    with pytest.raises(SSRFValidationError):
        validate_url_security("http://10.0.0.1", enforce_dns=False)
    with pytest.raises(SSRFValidationError):
        validate_url_security("http://172.16.0.1", enforce_dns=False)
    with pytest.raises(SSRFValidationError):
        validate_url_security("http://192.168.1.1", enforce_dns=False)


def test_block_cloud_metadata_ip():
    with pytest.raises(SSRFValidationError):
        validate_url_security("http://169.254.169.254/latest/meta-data/", enforce_dns=False)


def test_block_blacklisted_hostnames():
    with pytest.raises(SSRFValidationError):
        validate_url_security("http://localhost:3000", enforce_dns=False)
    with pytest.raises(SSRFValidationError):
        validate_url_security("http://metadata.google.internal", enforce_dns=False)
    with pytest.raises(SSRFValidationError):
        validate_url_security("http://service.local", enforce_dns=False)


def test_block_dangerous_schemes():
    with pytest.raises(InvalidURLError):
        validate_url_security("file:///etc/passwd", enforce_dns=False)
    with pytest.raises(InvalidURLError):
        validate_url_security("ftp://ftp.example.com", enforce_dns=False)
    with pytest.raises(InvalidURLError):
        validate_url_security("gopher://127.0.0.1", enforce_dns=False)


def test_block_disallowed_ports():
    with pytest.raises(InvalidURLError):
        validate_url_security("https://example.com:22", enforce_dns=False)
    with pytest.raises(InvalidURLError):
        validate_url_security("http://example.com:3306", enforce_dns=False)


def test_allow_valid_public_domain():
    url, ip = validate_url_security("https://example.com", enforce_dns=False)
    assert url == "https://example.com/"
