# WebLens AI — System Architecture Blueprint

```mermaid
graph TD
    User([User / Browser])
    
    subgraph Frontend ["Frontend Layer (Next.js 14 + TypeScript)"]
        Landing["Landing Page (URL Analysis Form)"]
        Dashboard["Intelligence Dashboard (/website/:id)"]
        ChatUI["Grounded Chat & Follow-up (/chat/:id)"]
        TraceUI["Telemetry & Activity Drawer"]
    end

    subgraph API ["API & Security Gateway (FastAPI)"]
        Router["REST & SSE Endpoints (/api/v1)"]
        SSRFGuard["SSRF & DNS Pre-Resolution Guard"]
        RateLimiter["Resource & Domain Rate Limiter"]
    end

    subgraph Agent ["Agent Orchestrator Layer"]
        Orchestrator["Orchestrator Brain (LLM)"]
        Policy["Backend Tool Authorization Policy"]
        subgraph Tools ["Deterministic Controlled Tools"]
            T_Validate["validate_url()"]
            T_Fetch["fetch_page()"]
            T_Discover["discover_links()"]
            T_Crawl["crawl_page()"]
            T_Search["search_website()"]
            T_Retrieve["retrieve_content()"]
            T_Profile["get_website_profile()"]
        end
    end

    subgraph Ingestion ["Content & Ingestion Pipeline"]
        HTTPClient["Streaming HTTPX Fetcher (5MB Cap)"]
        Parser["Structural Parser & Cleaner (Trafilatura / BS4)"]
        Chunker["Heading-Aware Semantic Chunker"]
        Embedder["Dense Embedding Generator"]
    end

    subgraph Storage ["Storage & Retrieval Engine"]
        PostgreSQL["Relational DB (Websites, Pages, Messages)"]
        HybridIndex["Hybrid Search (BM25 + Dense Vectors)"]
    end

    User --> Landing & Dashboard & ChatUI
    Landing & Dashboard & ChatUI --> Router
    Router --> SSRFGuard --> HTTPClient
    Router --> Agent
    Agent --> Policy --> Tools
    Tools --> Ingestion --> Storage
    Tools --> HybridIndex --> Orchestrator
    Orchestrator --> ChatUI
```

## Architectural Principles
1. **Decoupled Reasoning & Execution**: The LLM determines the information strategy (intent classification, retrieval requirement, deeper crawling need), but all network fetches and storage operations are executed deterministically by backend tools.
2. **SSRF Defense-in-Depth**: DNS is pre-resolved to evaluate IPv4/IPv6 destination ranges. Every redirect hop is checked before connecting.
3. **Hybrid RAG Pipeline**: Combines Okapi BM25 with dense cosine similarity vectors to balance exact keyword retrieval (e.g., pricing tiers, SKUs) with conceptual queries.
