"""
Unit tests for HTML extraction and link discovery.
"""

from app.extraction.extractor import extract_metadata_and_clean_content, compute_content_hash
from app.crawling.discovery import discover_internal_links, categorize_and_score_url

SAMPLE_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <title>Acme Cloud - Enterprise Analytics SaaS</title>
    <meta name="description" content="Acme Cloud provides AI-powered real-time data analytics for modern enterprises.">
    <meta property="og:title" content="Acme Cloud Analytics">
    <script type="application/ld+json">
    {
        "@context": "https://schema.org",
        "@type": "SoftwareApplication",
        "name": "Acme Cloud",
        "applicationCategory": "BusinessApplication"
    }
    </script>
</head>
<body>
    <nav>
        <a href="/">Home</a>
        <a href="/products">Products</a>
        <a href="/pricing">Pricing Plans</a>
        <a href="/about">About Us</a>
        <a href="https://external-partner.com">Partner</a>
    </nav>
    <main>
        <h1>Next Generation Cloud Analytics</h1>
        <p>Acme Cloud empowers data teams to query petabytes of data with sub-second latency.</p>
        <h2>Key Platform Features</h2>
        <p>Real-time stream processing, automated anomaly detection, and unified data pipelines.</p>
    </main>
    <footer>
        <p>© 2026 Acme Corp. All rights reserved.</p>
    </footer>
</body>
</html>
"""


def test_extract_metadata_and_clean_content():
    extracted = extract_metadata_and_clean_content("https://acme.com", SAMPLE_HTML)
    assert extracted.title == "Acme Cloud - Enterprise Analytics SaaS"
    assert "AI-powered real-time data analytics" in extracted.description
    assert len(extracted.headings) >= 2
    assert extracted.language == "en"
    assert len(extracted.json_ld) == 1
    assert extracted.json_ld[0]["name"] == "Acme Cloud"
    assert "Acme Cloud empowers data teams" in extracted.clean_text


def test_discover_internal_links():
    links = discover_internal_links("https://acme.com", SAMPLE_HTML)
    urls = [l.url for l in links]
    assert "https://acme.com/products" in urls
    assert "https://acme.com/pricing" in urls
    assert "https://acme.com/about" in urls
    # Ensure external domain was excluded
    assert "https://external-partner.com" not in urls


def test_categorize_and_score_url():
    cat_pricing, score_pricing = categorize_and_score_url("/pricing-plans", "Pricing Plans")
    assert cat_pricing == "pricing"
    assert score_pricing >= 0.85

    cat_about, score_about = categorize_and_score_url("/company/about-us", "About Us")
    assert cat_about == "about"
    assert score_about >= 0.85
