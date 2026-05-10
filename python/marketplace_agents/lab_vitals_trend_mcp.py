"""Owned Lab and Vitals Trend MCP deterministic tools."""

from __future__ import annotations

from typing import Any

from .clinical_foundation_mcp import get_patient_snapshot
from .fhir_utils import normalize_text
from .workflow_contract import compose_workflow_output, evidence_from_refs, patient_id_from_snapshot, score_workflow_risk


def analyze_observation_trends(snapshot_or_fhir: Any, limit: int = 20) -> dict[str, Any]:
    """Analyze Observation trends without making diagnosis claims."""

    snapshot = _ensure_snapshot(snapshot_or_fhir)
    grouped = _group_numeric_observations(snapshot.get("observations", []))
    trends = []
    urgent_findings = []
    for name, values in grouped.items():
        values = sorted(values, key=lambda item: item.get("date") or "")
        if not values:
            continue
        first = values[0]["number"]
        last = values[-1]["number"]
        direction = _direction(first, last)
        trend = {
            "name": name,
            "count": len(values),
            "firstValue": first,
            "lastValue": last,
            "direction": direction,
            "latestDate": values[-1].get("date", ""),
            "sourceRefs": [item.get("sourceRef", "") for item in values][-5:],
            "risk_level": _risk_for_value(name, last),
        }
        trends.append(trend)
        if trend["risk_level"] in {"high", "critical"}:
            urgent_findings.append(
                {
                    "code": "URGENT_OBSERVATION_THRESHOLD",
                    "severity": trend["risk_level"],
                    "message": f"{name} latest value {last} crossed configured threshold.",
                    "sourceRefs": trend["sourceRefs"],
                }
            )
    trends = sorted(trends, key=lambda item: (item["risk_level"] != "critical", item["risk_level"] != "high", item["name"]))[:limit]
    risk = score_workflow_risk(urgent_findings, urgent=any(item.get("severity") == "critical" for item in urgent_findings))
    output = compose_workflow_output(
        agent_name="Lab/Vitals Trend Agent",
        patient_id=patient_id_from_snapshot(snapshot),
        workflow_step="analyze_observation_trends",
        summary=f"Analyzed {sum(item['count'] for item in trends)} observation values across {len(trends)} analytes or vitals.",
        findings=urgent_findings,
        evidence=evidence_from_refs([ref for trend in trends for ref in trend.get("sourceRefs", [])]),
        confidence="medium",
        risk_level=risk["risk_level"],
        human_reviewer_role="clinician",
        work_completed=[
            f"observation groups analyzed: {len(grouped)}",
            f"trend records returned: {len(trends)}",
            f"urgent threshold findings: {len(urgent_findings)}",
        ],
        recommended_next_action="Review abnormal trends and decide whether follow-up or urgent escalation is needed.",
        blocked_actions=["diagnosis from trend alone", "urgent escalation without clinician review"] if urgent_findings else [],
    )
    return {**output, "trends": trends, "urgentFindings": urgent_findings}


def detect_urgent_observations(snapshot_or_fhir: Any) -> dict[str, Any]:
    """Return only observations crossing high or critical thresholds."""

    analysis = analyze_observation_trends(snapshot_or_fhir)
    urgent = [trend for trend in analysis["trends"] if trend["risk_level"] in {"high", "critical"}]
    return {
        "urgentObservations": urgent,
        "requiresHumanReview": bool(urgent),
        "riskLevel": "critical" if any(item["risk_level"] == "critical" for item in urgent) else ("high" if urgent else "low"),
    }


def recommend_trend_followup(analysis: dict[str, Any]) -> dict[str, Any]:
    """Draft follow-up tasks from trend analysis."""

    tasks = []
    for trend in analysis.get("trends", []):
        if trend.get("risk_level") in {"high", "critical"}:
            tasks.append(
                {
                    "type": "urgent-trend-review",
                    "description": f"Review {trend['name']} trend; latest value {trend['lastValue']}.",
                    "priority": trend["risk_level"],
                    "status": "draft",
                }
            )
        elif trend.get("direction") == "worsening":
            tasks.append(
                {
                    "type": "trend-followup",
                    "description": f"Consider follow-up for worsening {trend['name']} trend.",
                    "priority": "medium",
                    "status": "draft",
                }
            )
    return {
        "tasks": tasks,
        "blockedActions": ["automatic diagnosis", "automatic urgent patient instruction"],
        "requiresHumanReview": bool(tasks),
    }


def _ensure_snapshot(value: Any) -> dict[str, Any]:
    if isinstance(value, dict) and {"observations", "sourceRefs"}.issubset(value.keys()):
        return value
    return get_patient_snapshot(value)


def _group_numeric_observations(observations: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for observation in observations:
        number = _number(observation.get("value", ""))
        if number is None:
            continue
        name = normalize_text(observation.get("name", "")) or "observation"
        grouped.setdefault(name, []).append(
            {
                "number": number,
                "date": observation.get("date", ""),
                "sourceRef": observation.get("sourceRef", ""),
            }
        )
    return grouped


def _number(value: str) -> float | None:
    digits = "".join(ch if ch.isdigit() or ch in ".-" else " " for ch in str(value))
    for part in digits.split():
        try:
            return float(part)
        except ValueError:
            continue
    return None


def _direction(first: float, last: float) -> str:
    if abs(last - first) < 0.01:
        return "stable"
    return "worsening" if last > first else "improving"


def _risk_for_value(name: str, value: float) -> str:
    text = normalize_text(name)
    if "potassium" in text and (value >= 6.0 or value <= 2.8):
        return "critical"
    if "egfr" in text and value < 15:
        return "critical"
    if "systolic" in text and value >= 180:
        return "critical"
    if "glucose" in text and value >= 400:
        return "critical"
    if ("a1c" in text or "hba1c" in text) and value >= 10:
        return "high"
    if "egfr" in text and value < 30:
        return "high"
    return "low"
