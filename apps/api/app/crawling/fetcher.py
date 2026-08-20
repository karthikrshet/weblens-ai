"""
Secure HTTP Page Fetcher with SSRF defense, streaming size limits,
redirect destination validation, and structured error handling.
"""

import time
import httpx
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse

from app.config.settings import settings
from app.security.ssrf import validate_url_security, SSRFValidationError, InvalidURLError

logger = logging.getLogger(__name__)


class FetchError(Exception):
    """Base exception for page fetching failures."""
    pass


class ResponseTooLargeError(FetchError):
    """Raised when the fetched page exceeds maximum byte threshold."""
    pass


class BlockedDestinationError(FetchError):
    """Raised when destination is rejected by SSRF guard."""
    pass


@dataclass
class FetchResult:
    url: str
    final_url: str
    status_code: int
    content_type: str
    html: str
    response_time_ms: float
    is_success: bool
    error: Optional[str] = None
    headers: Dict[str, str] = None


async def fetch_page_secure(
    url: str,
    max_bytes: int = settings.MAX_RESPONSE_BYTES,
    timeout_seconds: float = settings.REQUEST_TIMEOUT_SECONDS,
    max_redirects: int = settings.MAX_REDIRECTS,
    user_agent: str = settings.USER_AGENT,
    enforce_dns: bool = True,
) -> FetchResult:
    """
    Fetch a web page securely:
    1. Pre-validates URL for SSRF and disallowed schemes/ports.
    2. Streams response with hard byte cutoff to prevent memory exhaustion / zip bombs.
    3. Validates each redirect hop destination against SSRF policies.
    """
    start_time = time.time()
    
    # 1. Pre-connection SSRF & scheme check
    try:
        canonical_url, _ = validate_url_security(url, enforce_dns=enforce_dns)
    except (SSRFValidationError, InvalidURLError) as e:
        logger.warning(f"URL validation failed for '{url}': {str(e)}")
        raise BlockedDestinationError(f"Access to URL was rejected: {str(e)}")

    current_url = canonical_url
    redirect_count = 0

    headers = {
        "User-Agent": user_agent,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }

    try:
        async with httpx.AsyncClient(
            follow_redirects=False, # We handle redirects manually to enforce SSRF checks on every hop
            timeout=httpx.Timeout(timeout_seconds),
            verify=True,
        ) as client:
            
            while True:
                # Validate current hop before making HTTP request
                if redirect_count > 0:
                    try:
                        validate_url_security(current_url, enforce_dns=enforce_dns)
                    except (SSRFValidationError, InvalidURLError) as e:
                        raise BlockedDestinationError(f"Redirect destination blocked: {str(e)}")

                response = await client.get(current_url, headers=headers)
                
                # Check for redirects (301, 302, 303, 307, 308)
                if response.is_redirect and "location" in response.headers:
                    redirect_count += 1
                    if redirect_count > max_redirects:
                        raise FetchError(f"Exceeded maximum redirect limit ({max_redirects})")
                    
                    redirect_location = response.headers["location"]
                    current_url = urljoin(current_url, redirect_location)
                    continue

                # Normal response reached
                content_type = response.headers.get("content-type", "").lower()
                
                # Read response body with streaming size enforcement
                content_bytes = bytearray()
                async for chunk in response.aiter_bytes():
                    content_bytes.extend(chunk)
                    if len(content_bytes) > max_bytes:
                        logger.warning(f"Response size exceeded limit ({max_bytes} bytes) for URL: {current_url}")
                        raise ResponseTooLargeError(f"Page content exceeded maximum size limit ({max_bytes // 1024 // 1024}MB)")

                elapsed_ms = round((time.time() - start_time) * 1000, 2)
                
                # Decode text safely
                encoding = response.encoding or "utf-8"
                try:
                    html_text = content_bytes.decode(encoding, errors="replace")
                except Exception:
                    html_text = content_bytes.decode("utf-8", errors="replace")

                return FetchResult(
                    url=url,
                    final_url=str(response.url),
                    status_code=response.status_code,
                    content_type=content_type,
                    html=html_text,
                    response_time_ms=elapsed_ms,
                    is_success=response.is_success,
                    headers=dict(response.headers),
                )

    except httpx.TimeoutException:
        elapsed_ms = round((time.time() - start_time) * 1000, 2)
        logger.warning(f"Fetch timeout after {timeout_seconds}s for URL: {url}")
        raise FetchError(f"Website request timed out after {timeout_seconds} seconds.")
    except httpx.HTTPError as e:
        elapsed_ms = round((time.time() - start_time) * 1000, 2)
        logger.warning(f"HTTP error for URL '{url}': {str(e)}")
        raise FetchError(f"HTTP request error: {str(e)}")
