# Architecture Decision Records (ADRs)

## ADR-001: Single Orchestrator vs Multi-Agent Architecture
- **Decision**: Use a single orchestrator agent with deterministic backend tools.
- **Rationale**: Multi-agent setups introduce non-deterministic communication loops, token overhead, and debugging complexity. A single orchestrator with strict tool boundaries provides predictable reasoning and rapid execution.

## ADR-002: Hybrid Retrieval (BM25 + Dense Vectors)
- **Decision**: Combine Okapi BM25 keyword matching with normalized dense vector cosine similarity.
- **Rationale**: Vector search excels at semantic concepts but struggles with exact entity strings (model numbers, specific plan names, pricing tiers). Hybrid retrieval delivers the highest recall and precision.

## ADR-003: Backend-Enforced Security Policies
- **Decision**: The LLM is never given direct network access or security authorization responsibilities.
- **Rationale**: Security cannot rely on model alignment. All SSRF pre-connection checks, domain boundary constraints, response size cutoffs, and redirect validations are enforced strictly in Python.

## ADR-004: Safe Observability Streams vs Raw Chain-of-Thought
- **Decision**: Expose safe telemetry (tool name, latency, status, input summary) over SSE, without streaming raw internal reasoning.
- **Rationale**: Protects against accidental system prompt or secret exfiltration while providing users and developers with complete transparency into agent actions.
