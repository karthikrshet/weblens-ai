"""
Playwright Browser Fallback for JavaScript-heavy Web Applications.
Only invoked when static HTTP extraction yields sparse/empty content.
Enforces strict execution timeouts, disables unnecessary capabilities, and tears down instances cleanly.
"""

import asyncio
import logging
from typing import Optional

logger = logging.getLogger(__name__)


async def fetch_page_with_browser(
    url: str,
    timeout_seconds: float = 20.0,
) -> Optional[str]:
    """
    Render JavaScript-rendered single-page applications via headless browser.
    Returns rendered HTML or None if Playwright is unavailable or fails.
    """
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        logger.info("Playwright is not installed in the environment; skipping browser fallback.")
        return None

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                ],
            )
            context = await browser.new_context(
                java_script_enabled=True,
                bypass_csp=False,
            )
            page = await context.new_page()
            
            try:
                await page.goto(url, wait_until="networkidle", timeout=int(timeout_seconds * 1000))
                rendered_html = await page.content()
                return rendered_html
            except Exception as e:
                logger.warning(f"Browser navigation failed for '{url}': {str(e)}")
                return None
            finally:
                await context.close()
                await browser.close()

    except Exception as e:
        logger.warning(f"Playwright execution error for '{url}': {str(e)}")
        return None
