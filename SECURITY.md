# Security Policy for WebLens AI

## Security Architecture Overview
WebLens AI treats all external web content and user-submitted URLs as untrusted.

### 1. SSRF Protection
- Disallows all private network IP ranges (RFC 1918: `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`).
- Blocks loopback (`127.0.0.0/8`, `::1`), link-local (`169.254.0.0/16`), multicast, and cloud metadata services (`169.254.169.254`, `metadata.google.internal`).
- Pre-resolves DNS and inspects every redirect hop destination before issuing HTTP requests.
- Restricts destination ports strictly to standard web ports (`80`, `443`, `8080`, `8443`).

### 2. Prompt Injection Isolation
- Webpage content is injected into LLM context strictly as data blocks, never system instructions.
- System prompt instructs the agent to discard any commands or overrides embedded within scraped text.

### 3. Resource & DoS Safeguards
- Hard 5MB response size cutoff on all streaming HTTP downloads.
- Maximum 20 pages crawled per website with maximum depth of 2.
- Hard timeout of 15 seconds per request and 60 seconds total crawl budget.
- Maximum 8 tool executions per agent turn with duplicate call suppression.

### Reporting Vulnerabilities
If you discover a security issue or bypass attempt, please open a security advisory or contact security@weblens.ai.
