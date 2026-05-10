"""Deterministic tools for the owned Marketplace Quality MCP."""

from __future__ import annotations

import re
from dataclasses import asdict
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .composites import candidate_to_dict, composite_specs, rank_candidates
from .registry import (
    load_marketplace_resources,
    summarize_resources,
    validate_a2a_agent_card,
    validate_marketplace_resource,
)


def summarize_marketplace(payload: dict[str, Any]) -> dict:
    """Summarize the marketplace export by auth, FHIR, and workflow category."""

    resources = load_marketplace_resources(payload)
    summary = summarize_resources(resources)
    return asdict(summary)


def validate_listing(record: dict[str, Any]) -> dict:
    """Validate a single exported marketplace listing."""

    findings = validate_marketplace_resource(record)
    return _finding_summary(findings)


def validate_marketplace_export(payload: dict[str, Any]) -> dict:
    """Validate every listing in an exported marketplace payload."""

    records = payload.get("resources", [])
    if not isinstance(records, list):
        return {
            "errors": 1,
            "warnings": 0,
            "findings": [
                {
                    "level": "error",
                    "resource": "[payload]",
                    "code": "resources.invalid",
                    "message": "payload.resources must be a list.",
                }
            ],
        }

    findings = []
    for record in records:
        resource_name = str(record.get("name", "[unnamed]")) if isinstance(record, dict) else "[invalid]"
        record_findings = validate_marketplace_resource(record) if isinstance(record, dict) else []
        if not isinstance(record, dict):
            findings.append(
                {
                    "level": "error",
                    "resource": resource_name,
                    "code": "resource.invalid",
                    "message": "Resource must be an object.",
                }
            )
            continue
        for finding in record_findings:
            item = asdict(finding)
            item["resource"] = resource_name
            findings.append(item)
    return _finding_summary_dicts(findings)


def validate_a2a_card(card: dict[str, Any]) -> dict:
    """Validate an A2A agent card for Prompt Opinion compatibility."""

    findings = validate_a2a_agent_card(card)
    return _finding_summary(findings)


def test_endpoint(record: dict[str, Any], dry_run: bool = True, timeout_seconds: float = 5.0) -> dict:
    """Probe one MCP endpoint without sending PHI."""

    endpoint = _endpoint_from_record(record)
    if not endpoint:
        return {
            "dryRun": dry_run,
            "reachable": False,
            "healthy": False,
            "error": "missing_endpoint",
            "sendsPhi": False,
        }
    if dry_run:
        return {
            "dryRun": True,
            "reachable": None,
            "healthy": None,
            "endpoint": endpoint,
            "method": "GET",
            "sendsPhi": False,
            "nextStep": "Run with dryRun=false to perform a no-PHI reachability probe.",
        }

    request = Request(
        endpoint,
        headers={"Accept": "application/json", "User-Agent": "po-marketplace-smoke/0.1"},
        method="GET",
    )
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            return _endpoint_result(endpoint, response.status, dry_run=False)
    except HTTPError as exc:
        return _endpoint_result(endpoint, exc.code, dry_run=False)
    except URLError as exc:
        return {
            "dryRun": False,
            "reachable": False,
            "healthy": False,
            "endpoint": endpoint,
            "error": str(exc.reason),
            "sendsPhi": False,
        }


def recommend_composite_mcps(payload: dict[str, Any], limit: int = 8) -> dict:
    """Recommend existing marketplace MCPs as benchmarks for owned composites."""

    resources = load_marketplace_resources(payload)
    recommendations = []
    for spec in composite_specs():
        candidates = rank_candidates(resources, spec, limit=limit)
        recommendations.append(
            {
                "slug": spec.slug,
                "name": spec.name,
                "purpose": spec.purpose,
                "categories": list(spec.categories),
                "toolContract": [asdict(tool) for tool in spec.tools],
                "candidates": [candidate_to_dict(candidate, spec) for candidate in candidates],
            }
        )
    return {"composites": recommendations}


def build_replacement_plan(payload: dict[str, Any], limit: int = 5) -> dict:
    """Build the safe replacement plan for marketplace MCPs."""

    resources = load_marketplace_resources(payload)
    composites = []
    for spec in composite_specs():
        candidates = rank_candidates(resources, spec)
        composites.append(
            {
                "slug": spec.slug,
                "name": spec.name,
                "candidateCount": len(candidates),
                "fhirCandidateCount": sum(1 for item in candidates if item.supports_fhir_context),
                "authRequiredCandidateCount": sum(1 for item in candidates if item.auth_required),
                "deleteReady": False,
                "implementationStatus": _implementation_status(spec.slug),
                "nextGate": "Run endpoint smoke tests, expand clinical fixtures, and complete workflow parity assertions.",
                "benchmarks": [candidate_to_dict(candidate, spec) for candidate in candidates[:limit]],
            }
        )
    return {
        "deleteMarketplaceRecordsNow": False,
        "reason": "Marketplace records are still the inventory and parity benchmark.",
        "requiredBeforeDelete": [
            "Owned MCP exposes equivalent or better workflow coverage.",
            "Validation passes for owned MCP and benchmark records.",
            "Endpoint smoke tests pass without PHI.",
            "Auth and FHIR behavior is documented.",
            "Rollback path can restore original marketplace listings.",
        ],
        "composites": composites,
    }


def map_owned_tool_coverage(payload: dict[str, Any], limit: int = 10) -> dict:
    """Map owned tool contracts to marketplace benchmark tools."""

    resources = load_marketplace_resources(payload)
    composites = []
    summary = {"covered": 0, "partial": 0, "uncovered": 0}
    for spec in composite_specs():
        candidates = rank_candidates(resources, spec)
        coverage = _tool_coverage_for_spec(spec, candidates, limit=limit)
        for item in coverage:
            summary[item["coverageStatus"]] += 1
        composites.append(
            {
                "slug": spec.slug,
                "name": spec.name,
                "benchmarkCandidateCount": len(candidates),
                "tools": coverage,
            }
        )
    return {
        "deleteMarketplaceRecordsNow": False,
        "coverageSummary": summary,
        "statusLegend": {
            "covered": "Owned tool has benchmark matches and completed workflow parity assertions.",
            "partial": "Owned tool is implemented and has marketplace benchmark matches, but parity assertions are still pending.",
            "uncovered": "Owned tool is implemented but no matching marketplace benchmark tool was found.",
        },
        "composites": composites,
    }


def generate_parity_report(payload: dict[str, Any], limit: int = 10) -> dict:
    """Generate a parity report for owned MCP implementation work."""

    resources = load_marketplace_resources(payload)
    validation = validate_marketplace_export(payload)
    report = {
        "sourceFetchedAt": payload.get("fetchedAt"),
        "sourceApi": payload.get("sourceApi"),
        "ownedServer": {
            "name": "owned-healthcare-mcp",
            "transports": ["stdio-jsonrpc", "http-jsonrpc"],
            "command": "python3.11 scripts/owned_mcp_server.py",
            "httpCommand": "python3.11 scripts/owned_mcp_server.py --http --port 8765",
            "smokeCommand": "python3.11 scripts/smoke_owned_mcp_server.py",
            "httpSmokeCommand": "python3.11 scripts/smoke_owned_mcp_http_server.py",
        },
        "summary": summarize_marketplace(payload),
        "marketplaceValidation": {
            "errors": validation["errors"],
            "warnings": validation["warnings"],
        },
        "deleteMarketplaceRecordsNow": False,
        "ownedComposites": [],
    }
    for spec in composite_specs():
        candidates = rank_candidates(resources, spec, limit=limit)
        all_candidates = rank_candidates(resources, spec)
        tool_names = sorted({tool for candidate in all_candidates for tool in candidate.tools})
        tool_coverage = _tool_coverage_for_spec(spec, all_candidates, limit=limit)
        report["ownedComposites"].append(
            {
                "slug": spec.slug,
                "name": spec.name,
                "purpose": spec.purpose,
                "toolContract": [asdict(tool) for tool in spec.tools],
                "benchmarkCandidateCount": len(all_candidates),
                "benchmarkToolCount": len(tool_names),
                "benchmarkTools": tool_names,
                "toolCoverage": tool_coverage,
                "topBenchmarks": [candidate_to_dict(candidate, spec) for candidate in candidates],
                "parityStatus": _implementation_status(spec.slug),
                "deleteReady": False,
                "missingGates": [
                    "endpoint smoke tests",
                    "expanded fixture coverage",
                    "workflow parity assertions",
                    "rollback plan",
                ],
            }
        )
    return report


def _finding_summary(findings) -> dict:
    return _finding_summary_dicts([asdict(finding) for finding in findings])


def _finding_summary_dicts(findings: list[dict]) -> dict:
    return {
        "errors": sum(1 for finding in findings if finding.get("level") == "error"),
        "warnings": sum(1 for finding in findings if finding.get("level") == "warning"),
        "findings": findings,
    }


def _implementation_status(slug: str) -> str:
    return "local_server_wrapped"


def _endpoint_from_record(record: dict[str, Any]) -> str:
    if not isinstance(record, dict):
        return ""
    return str(record.get("endpoint") or record.get("url") or "").strip()


def _endpoint_result(endpoint: str, status_code: int, dry_run: bool) -> dict:
    reachable = True
    auth_likely_required = status_code in {401, 403}
    method_not_allowed = status_code == 405
    healthy = status_code < 500
    return {
        "dryRun": dry_run,
        "reachable": reachable,
        "healthy": healthy,
        "endpoint": endpoint,
        "httpStatus": status_code,
        "authLikelyRequired": auth_likely_required,
        "methodNotAllowed": method_not_allowed,
        "sendsPhi": False,
    }


def _tool_coverage_for_spec(spec, candidates, limit: int) -> list[dict]:
    benchmark_tools = sorted({tool for candidate in candidates for tool in candidate.tools})
    coverage = []
    for tool in spec.tools:
        matches = _match_benchmark_tools(tool, benchmark_tools, limit=limit)
        coverage.append(
            {
                "ownedTool": tool.name,
                "coverageStatus": "partial" if matches else "uncovered",
                "reason": (
                    "Owned tool is implemented; endpoint parity against benchmark tools is still pending."
                    if matches
                    else "No marketplace benchmark tool name matched this owned tool contract."
                ),
                "benchmarkMatches": matches,
            }
        )
    return coverage


def _match_benchmark_tools(tool, benchmark_tools: list[str], limit: int) -> list[str]:
    query_tokens = _tokens(f"{tool.name} {tool.description}")
    scored = []
    for benchmark_tool in benchmark_tools:
        benchmark_tokens = _tokens(benchmark_tool)
        overlap = query_tokens.intersection(benchmark_tokens)
        if not overlap:
            continue
        scored.append((-len(overlap), benchmark_tool.lower(), benchmark_tool))
    return [item[2] for item in sorted(scored)[:limit]]


def _tokens(value: str) -> set[str]:
    spaced = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", value.replace("_", " "))
    words = set(re.findall(r"[a-z0-9]+", spaced.lower()))
    stopwords = {
        "a",
        "and",
        "contract",
        "contracts",
        "endpoint",
        "for",
        "get",
        "listing",
        "marketplace",
        "mcp",
        "one",
        "or",
        "owned",
        "payload",
        "probe",
        "record",
        "return",
        "server",
        "the",
        "to",
        "tool",
        "tools",
        "with",
    }
    return {word for word in words if len(word) > 2 and word not in stopwords}
