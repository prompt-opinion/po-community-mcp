"""
Trajectory.OS — Dispatch Postpartum Alert (Tool 2)
==================================================
Companion to AnalyzePostpartumCoverage.  Re-runs the postpartum analysis and,
if the patient is in CRITICAL or EXPIRED status, **actually sends** the drafted
SMS via Twilio. This is the Zero-Click *execution* step — the analyze tool
drafts; this tool dispatches.

Required environment variables (typically loaded from python/.env):
  TWILIO_ACCOUNT_SID            — Twilio account identifier (starts with "AC...")
  TWILIO_AUTH_TOKEN             — Twilio auth token
  TWILIO_FROM_NUMBER            — Twilio-owned sender, E.164 (e.g. "+15551234567")

Optional:
  TWILIO_DEMO_RECIPIENT_OVERRIDE — If set, forces ALL outbound SMS to this
                                   single number. Use this for trial accounts
                                   (Twilio trial only delivers to verified
                                   recipients) and for the recorded demo.
"""

import json
import os
import traceback
from datetime import datetime, timezone
from typing import Annotated

import httpx
from mcp.server.fastmcp import Context
from pydantic import Field

from fhir_client import FhirClient
from fhir_utilities import get_fhir_context
from mcp_utilities import create_text_response
from tools.postpartum_policy_tool import compute_postpartum_analysis


def _build_communication_request(
    patient_id: str,
    sms_body: str,
    twilio_sid: str,
    twilio_status: str,
    to_number: str,
    from_number: str,
    dispatched_at_iso: str,
) -> dict:
    """
    Build a FHIR R4 CommunicationRequest documenting the SMS dispatch back
    to the patient's chart. Recorded so the EHR has a permanent trail of
    the autonomous intervention.
    """
    return {
        "resourceType": "CommunicationRequest",
        "status": "completed" if twilio_status in ("sent", "delivered") else "active",
        "intent": "order",
        "priority": "urgent",
        "category": [{
            "coding": [{
                "system": "http://terminology.hl7.org/CodeSystem/communication-category",
                "code": "notification",
                "display": "Notification",
            }]
        }],
        "medium": [{
            "coding": [{
                "system": "http://terminology.hl7.org/CodeSystem/v3-ParticipationMode",
                "code": "WRITTEN",
                "display": "written",
            }],
            "text": "SMS",
        }],
        "subject": {"reference": f"Patient/{patient_id}"},
        "recipient": [{"reference": f"Patient/{patient_id}"}],
        "requester": {"display": "Trajectory.OS — Autonomous Postpartum Policy Engine"},
        "payload": [{"contentString": sms_body}],
        "occurrenceDateTime": dispatched_at_iso,
        "authoredOn": dispatched_at_iso,
        "reasonCode": [{
            "text": (
                "Postpartum Medicaid coverage cliff — Zero-Click SMS intervention "
                "auto-dispatched by Trajectory.OS."
            )
        }],
        "note": [{
            "text": (
                f"Dispatched via Twilio. SID={twilio_sid}, status={twilio_status}. "
                f"From={from_number}, To={to_number}. "
                f"Body length={len(sms_body)} chars."
            )
        }],
    }


async def _write_back_to_chart(
    ctx: Context | None,
    patient_id: str,
    sms_body: str,
    twilio_sid: str,
    twilio_status: str,
    to_number: str,
    from_number: str,
    dispatched_at_iso: str,
) -> dict:
    """
    Best-effort POST of a CommunicationRequest to the FHIR server. Failure
    here is non-fatal — the dispatch tool returns dispatch success either way.
    Returns an audit-trail dict shaped: {attempted, succeeded, resource_id, error}.
    """
    audit = {"attempted": False, "succeeded": False, "resource_id": None, "error": None}
    fc = get_fhir_context(ctx)
    if not fc:
        audit["error"] = "No FHIR context available (write-back skipped)."
        return audit

    audit["attempted"] = True
    client = FhirClient(base_url=fc.url, token=fc.token)
    body = _build_communication_request(
        patient_id=patient_id,
        sms_body=sms_body,
        twilio_sid=twilio_sid,
        twilio_status=twilio_status,
        to_number=to_number,
        from_number=from_number,
        dispatched_at_iso=dispatched_at_iso,
    )
    try:
        result = await client.create("CommunicationRequest", body)
        audit["succeeded"] = True
        audit["resource_id"] = result.get("id") or result.get("_location")
        audit["resource_type"] = "CommunicationRequest"
    except httpx.HTTPStatusError as e:
        status = e.response.status_code if e.response is not None else "?"
        snippet = ""
        if e.response is not None:
            try:
                snippet = e.response.text[:200]
            except Exception:
                pass
        audit["error"] = (
            f"FHIR write-back failed: HTTP {status}. "
            f"{snippet or '(no body)'}. "
            "Likely missing patient/CommunicationRequest.c scope — re-authorize "
            "the MCP server in Prompt Opinion after the scope was advertised."
        )
    except Exception as e:  # noqa: BLE001
        audit["error"] = f"FHIR write-back failed: {type(e).__name__}: {e}"
    return audit


def _normalize_phone(raw: str | None) -> str | None:
    """
    Best-effort coercion to E.164. Returns None if the input cannot plausibly
    be a US/international phone number. Twilio enforces strict E.164 — passing
    a malformed number causes the SMS create call to fail with a verbose error,
    so we pre-validate.
    """
    if not raw:
        return None
    cleaned = raw.strip()
    has_plus = cleaned.startswith("+")
    digits = "".join(ch for ch in cleaned if ch.isdigit())
    if not digits:
        return None
    if has_plus:
        return f"+{digits}"
    if len(digits) == 10:
        return f"+1{digits}"
    if len(digits) == 11 and digits.startswith("1"):
        return f"+{digits}"
    # Synthetic FHIR phones like "555-019-8372" are rejected by Twilio anyway,
    # but we let them through here so the error message names the offending
    # number rather than a generic "no recipient" error.
    if len(digits) >= 7:
        return f"+{digits}"
    return None


async def dispatch_postpartum_alert(
    patientId: Annotated[  # noqa: N803
        str | None,
        Field(
            description=(
                "The FHIR patient ID. Optional if patient context already "
                "exists via SHARP headers."
            )
        ),
    ] = None,
    ctx: Context = None,
) -> str:
    """
    Trajectory.OS Zero-Click execution step. Re-runs the postpartum coverage
    analysis for the given patient and, if status is CRITICAL or EXPIRED,
    sends the drafted SMS to the patient via Twilio.

    Returns a dispatch confirmation including the Twilio message SID, sent
    body, recipient resolution path, and remaining manual steps.
    """
    try:
        # ── 1. Get a fresh analysis (single source of truth for the SMS body)
        analysis_result = await compute_postpartum_analysis(patientId, ctx)
        if isinstance(analysis_result, str):
            # Propagate analyze-side errors verbatim — they already explain.
            return create_text_response(analysis_result, is_error=False)

        analysis = analysis_result.get("trajectory_os_analysis", {})
        status = analysis.get("status", "UNKNOWN")
        patient_block = analysis.get("patient", {})
        patient_name = patient_block.get("name", "Unknown")

        # ── 2. Guard: only dispatch on imminent / past-due cliffs
        if status not in ("CRITICAL", "EXPIRED"):
            return create_text_response(json.dumps({
                "trajectory_os_dispatch": {
                    "status": "SKIPPED",
                    "reason": (
                        f"Patient {patient_name} is in status '{status}', not "
                        f"CRITICAL/EXPIRED. Zero-Click SMS dispatch only fires "
                        f"when the cliff is within {15} days or has already passed."
                    ),
                    "analysis_summary": analysis.get("summary"),
                }
            }, indent=2))

        sms_draft = analysis.get("zero_click_interventions", {}).get("sms_draft", {})
        message_body = sms_draft.get("message", "")
        if not message_body:
            return create_text_response(
                "ERROR: Analysis returned CRITICAL but no SMS draft was produced. "
                "This is a bug — inspect _build_sms_draft in postpartum_policy_tool.py.",
                is_error=False,
            )

        # ── 3. Resolve Twilio creds from environment
        account_sid = os.environ.get("TWILIO_ACCOUNT_SID", "").strip()
        auth_token = os.environ.get("TWILIO_AUTH_TOKEN", "").strip()
        from_number = os.environ.get("TWILIO_FROM_NUMBER", "").strip()
        if not (account_sid and auth_token and from_number):
            missing = [
                k for k, v in {
                    "TWILIO_ACCOUNT_SID": account_sid,
                    "TWILIO_AUTH_TOKEN": auth_token,
                    "TWILIO_FROM_NUMBER": from_number,
                }.items() if not v
            ]
            return create_text_response(
                f"ERROR: Twilio is not configured on the MCP server. Missing "
                f"environment variable(s): {', '.join(missing)}. Copy "
                f"python/.env.example to python/.env, fill in your Twilio "
                f"credentials, and restart the server.",
                is_error=False,
            )

        # ── 4. Resolve recipient (override > FHIR Patient.telecom)
        recipient_override = os.environ.get("TWILIO_DEMO_RECIPIENT_OVERRIDE", "").strip()
        if recipient_override:
            to_number = _normalize_phone(recipient_override)
            recipient_source = "TWILIO_DEMO_RECIPIENT_OVERRIDE (demo mode)"
            raw_recipient = recipient_override
        else:
            raw_recipient = sms_draft.get("to") or patient_block.get("phone") or ""
            to_number = _normalize_phone(raw_recipient)
            recipient_source = "FHIR Patient.telecom (production mode)"

        if not to_number:
            return create_text_response(
                f"ERROR: Could not resolve a valid E.164 phone number. "
                f"Raw value tried: '{raw_recipient}'. "
                f"For trial Twilio accounts, set TWILIO_DEMO_RECIPIENT_OVERRIDE "
                f"to your verified recipient number in python/.env.",
                is_error=False,
            )

        # ── 5. Lazy-import Twilio so missing-package errors are caught here,
        #     not at module load (which would break the entire MCP server).
        try:
            from twilio.base.exceptions import TwilioRestException
            from twilio.rest import Client
        except ImportError:
            return create_text_response(
                "ERROR: The `twilio` package is not installed. From "
                "po-community-mcp/python/, run: "
                "`pip install -r requirements.txt`",
                is_error=False,
            )

        # ── 6. Send
        try:
            client = Client(account_sid, auth_token)
            message = client.messages.create(
                body=message_body,
                from_=from_number,
                to=to_number,
            )
        except TwilioRestException as e:
            return create_text_response(
                f"ERROR: Twilio rejected the SMS. "
                f"Code {getattr(e, 'code', '?')} — {getattr(e, 'msg', str(e))}. "
                f"Common causes: trial-account recipient is not verified at "
                f"twilio.com/console, the From number is not your Twilio "
                f"number, the message body violates content rules, or the "
                f"account balance is exhausted. "
                f"Outbound to: {to_number}, From: {from_number}.",
                is_error=False,
            )

        dispatched_at_iso = datetime.now(timezone.utc).isoformat()

        # ── 7. Best-effort FHIR write-back (CommunicationRequest)
        # This documents the autonomous intervention in the patient's chart.
        # Failure here does NOT fail the dispatch — the SMS already went out.
        audit_trail = await _write_back_to_chart(
            ctx=ctx,
            patient_id=patient_block.get("fhir_id") or "",
            sms_body=message_body,
            twilio_sid=message.sid,
            twilio_status=message.status,
            to_number=to_number,
            from_number=from_number,
            dispatched_at_iso=dispatched_at_iso,
        )

        # ── 8. Build dispatch confirmation
        dispatch_record = {
            "trajectory_os_dispatch": {
                "status": "DISPATCHED",
                "headline": (
                    f"Zero-Click SMS DISPATCHED to {patient_name} "
                    f"(Twilio SID {message.sid}, status={message.status})"
                    + (
                        f" + chart updated (CommunicationRequest/{audit_trail['resource_id']})"
                        if audit_trail.get("succeeded")
                        else ""
                    )
                ),
                "patient": {
                    "name": patient_name,
                    "fhir_id": patient_block.get("fhir_id"),
                    "state": patient_block.get("state"),
                    "delivery_date": patient_block.get("delivery_date"),
                    "days_until_cliff": patient_block.get("days_until_cliff"),
                    "coverage_cliff_date": patient_block.get(
                        "standard_coverage_cliff_date"
                    ),
                },
                "sms": {
                    "from": from_number,
                    "to": to_number,
                    "recipient_source": recipient_source,
                    "body": message_body,
                    "character_count": len(message_body),
                    "twilio_sid": message.sid,
                    "twilio_status": message.status,
                    "dispatched_at_utc": dispatched_at_iso,
                },
                "audit_trail": {
                    "fhir_writeback_attempted": audit_trail["attempted"],
                    "fhir_writeback_succeeded": audit_trail["succeeded"],
                    "fhir_resource_id": audit_trail["resource_id"],
                    "fhir_resource_type": audit_trail.get("resource_type"),
                    "fhir_writeback_error": audit_trail["error"],
                    "note": (
                        "On success, the patient's FHIR record now contains a "
                        "CommunicationRequest documenting this autonomous SMS "
                        "intervention — providing a permanent audit trail in the EHR."
                    ),
                },
                "remaining_actions": [
                    "Submit the pre-filled state Medicaid extension form "
                    "(see AnalyzePostpartumCoverage → extension_form_prefilled).",
                    "Confirm the 6-week postpartum OB/GYN appointment per the "
                    "ob_appointment_flag.",
                ],
                "analysis_summary": analysis.get("summary"),
            }
        }

        return create_text_response(json.dumps(dispatch_record, indent=2))

    except Exception as e:  # noqa: BLE001
        return create_text_response(
            f"ERROR: DispatchPostpartumAlert crashed unexpectedly: "
            f"{type(e).__name__}: {e}\n\nTraceback:\n{traceback.format_exc()}",
            is_error=False,
        )
