# SHARP-on-MCP Convening-Session Extension (RFC)

> **Status:** Draft, proposed for community review.
> **Authors:** Council Health AI, May 2026.
> **Discussion:** [https://github.com/prompt-opinion/po-community-mcp](https://github.com/prompt-opinion/po-community-mcp) (PR pending)
> **Companion implementation:** [github.com/council-health-ai/council/packages/specialty-lens-mcp](https://github.com/council-health-ai/council/tree/main/packages/specialty-lens-mcp)

---

## Abstract

SHARP-on-MCP propagates FHIR context (server URL + access token + patient ID) from the agent host to the MCP server on every tool call. This RFC proposes a small, optional extension — **convening-session headers** — that lets multiple cooperating agents (a Convener and N specialty peers) tag their MCP traffic so that a single SHARP-on-MCP server can:

1. **Cache FHIR retrieval** within a deliberation, avoiding N redundant Patient/Condition/Observation lookups when N specialty agents query the same patient simultaneously.
2. **Group audit log entries** by deliberation, enabling MedLog-style surveillance and post-hoc replay.
3. **Optionally enforce specialty-scoped tool authorization** — only the Cardiology agent's traffic can invoke `get_cardiology_perspective`.

The proposal also documents and proposes a fix for a **divergence between the SHARP spec and the reference implementations** in `prompt-opinion/po-community-mcp`.

## Motivation

The current SHARP-on-MCP spec assumes a single agent → single MCP server interaction model. Each tool call carries fresh FHIR context. This is correct for many cases — but it leaves performance, observability, and authorization gaps in **multi-agent peer scenarios**.

Concretely: in The Council, 8 specialty agents (Cardiology, Oncology, Nephrology, Endocrinology, Obstetrics, Developmental Pediatrics, Psychiatry, Anesthesia) each call the same `specialty-lens-mcp` server within a few seconds, all asking about the same patient. Without a shared session identifier, the server has no signal that these calls belong together. It cannot cache, cannot audit-group, and cannot enforce that only the Cardiology agent invokes `get_cardiology_perspective`.

## Proposal

### 1. Three new optional HTTP headers

```
X-Council-Convening-Id:  <UUID, opaque, stable across all calls in a single deliberation>
X-Council-Specialty:     <one of: cardiology|oncology|nephrology|endocrinology|
                                  obstetrics|developmental_pediatrics|psychiatry|anesthesia>
X-Council-Round-Id:      <integer, 1-indexed, monotonic within a Convening-Id>
```

All three are **optional**. A SHARP-on-MCP server that doesn't recognize them MUST ignore them and behave as today. A server that does recognize them MAY use them for caching, audit grouping, or scoped authorization.

The names are deliberately **convening-session** rather than overlapping with A2A's `contextId`. A single A2A `contextId` can span multiple convenings (e.g., a clinician's chat session that triggers two distinct council deliberations on two different patients), and a convening can be invoked outside an A2A context (e.g., a CLI script). Decoupling keeps the headers usable in both flows.

### 2. Capability advertisement

A SHARP-on-MCP server that supports these headers SHOULD advertise the convening-session extension on its `initialize` response:

```jsonc
{
  "capabilities": {
    "extensions": {
      "ai.council-health/convening-session": {
        "version": "0.1",
        "headers": [
          "x-council-convening-id",
          "x-council-specialty",
          "x-council-round-id"
        ],
        "description": "Optional headers that group MCP calls within a single multi-agent deliberation."
      }
    }
  }
}
```

This sits alongside the existing `ai.promptopinion/fhir-context` extension (and, per the spec divergence note below, the spec-canonical `experimental.fhir_context_required` shape).

### 3. Server behaviors enabled (all optional, SHOULD-not-MUST)

#### 3.1 FHIR retrieval cache

When the same `(X-Council-Convening-Id, X-Patient-ID)` pair is observed within the cache TTL (suggested: 10 minutes), the server MAY serve cached FHIR resource bundles for that patient instead of re-fetching from the FHIR server. This dramatically reduces FHIR load — for an 8-specialty Council, FHIR fetches drop from ~8N to N.

The cache key is `(convening_id, fhir_server_url, patient_id, resource_type)`. The server MUST invalidate when the FHIR access token changes (token-bound caching).

#### 3.2 Audit log grouping

The server MAY tag each tool-call audit record with the convening_id, enabling Mandel-style MedLog reports of "show me every reasoning step in deliberation X." This is mechanically simple — the server already logs per-tool-call; adding convening_id is a single column.

#### 3.3 Specialty-scoped tool authorization (opt-in)

A server MAY enforce that `X-Council-Specialty=cardiology` is required to invoke `get_cardiology_perspective`. This prevents agents from spoofing other specialties' opinions when forming concordance.

This is **opt-in** because most MCP servers don't expose specialty-scoped tools. For The Council's `specialty-lens-mcp`, it's a reasonable safeguard. For a generic medical knowledge MCP, it would be over-constraining.

### 4. Spec-vs-implementation divergence — a parallel ask

While drafting this proposal we observed a divergence between the [SHARP-on-MCP spec](https://sharponmcp.com/key-components.html) and the [TypeScript / Python / .NET reference implementations](https://github.com/prompt-opinion/po-community-mcp):

| Source | Capability advertisement |
|--------|--------------------------|
| **Spec** (`sharponmcp.com/key-components.html`) | `capabilities.experimental.fhir_context_required: { value: true }` |
| **Reference impls** (this repo) | `capabilities.extensions["ai.promptopinion/fhir-context"]: { scopes: [...] }` |

We propose **reconciling these** — pick one canonical shape and update the other. Until reconciliation lands, our reference implementation in `specialty-lens-mcp` advertises **both** for forward+backward compatibility, and we recommend the same defensive pattern for any new SHARP-on-MCP server.

We also observed that **none of the three reference implementations enforce HTTP 403** when a tool requiring FHIR context is invoked without the required headers — they throw at tool dispatch and surface a JSON-RPC error, which doesn't satisfy the spec's wording ("the MCP server should respond with a 403 Forbidden response"). Our `specialty-lens-mcp` implements 403 enforcement at request entry; we recommend making this part of the SHARP conformance test suite.

## Backward compatibility

- All three new headers are **optional**. Servers without convening-session support behave identically to today.
- Capability advertisement is **additive** — it sits in `extensions[]`, which already exists.
- The convening-id is **opaque** — clients without a Convener role simply don't include it.

## Reference implementation

`specialty-lens-mcp` (TypeScript, `@modelcontextprotocol/sdk` 1.25, Express 5, Streamable HTTP transport) implements:
- Capability advertisement of both the FHIR-context extension and the convening-session extension.
- 403 enforcement at request entry on `tools/call` lacking FHIR-context headers.
- Per-call audit log writes to Supabase, tagged with `convening_id` when present, `null` otherwise.

Source: <https://github.com/council-health-ai/council/tree/main/packages/specialty-lens-mcp>

The Council's nine A2A agents (Convener + 8 peer specialty agents, Python on `google-adk` 1.x + `a2a-sdk` 0.3) emit these headers on every MCP call:

```python
headers = {
    "X-FHIR-Server-URL": ctx.fhir_server_url,
    "X-FHIR-Access-Token": ctx.fhir_access_token,
    "X-Patient-ID": patient_id,
    "X-Council-Convening-Id": convening_id,
    "X-Council-Specialty": "cardiology",
    "X-Council-Round-Id": "1",
}
```

The Convener generates the `convening_id` once per deliberation and propagates it through A2A message metadata; each specialty agent extracts it and forwards on its MCP calls.

## Open questions for community review

1. **Header namespace.** We chose `X-Council-*` because the convening-session pattern was driven by the multi-specialty council use case, but the headers are domain-agnostic. Should they be `X-MCP-Session-Id` and `X-MCP-Session-Role` instead? `X-SHARP-Convening-*`?
2. **Cache TTL recommendation.** 10 minutes is our default. Is this the right order of magnitude?
3. **Specialty enumeration.** Should we publish a controlled vocabulary, or is that scope creep? We suspect *any* free-string specialty value is fine and the controlled vocabulary should live in COIN (the A2A extension), not SHARP-on-MCP.
4. **Interaction with A2A `contextId`.** Should the spec recommend that A2A clients propagate `contextId` to MCP calls under a separate header (e.g., `X-A2A-Context-Id`), or is that overreach into A2A territory?

## Acknowledgments

This RFC was drafted in the course of building [The Council](https://github.com/council-health-ai/council) for Prompt Opinion's *Agents Assemble — The Healthcare AI Endgame* hackathon. Thanks to Prompt Opinion for designing SHARP-on-MCP and to Josh Mandel for [SMART on FHIR](https://scholar.harvard.edu/jmandel/publications/smart-fhir-standards-based-interoperable-apps-platform-electronic-health) (Mandel et al., *JAMIA*, 2016) and the [Banterop](https://x.com/JoshCMandel/status/1963293944873160797) work on language-first interoperability — the architectural lineage SHARP-on-MCP belongs to.

## Changelog

- **2026-04-27** — Draft 0.1 published.
