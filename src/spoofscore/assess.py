"""Assess whether a domain's published SPF and DMARC records stop From: spoofing.

Pure functions over the TXT strings. No network access here; see ``lookup``.
The rules mirror ``web/spoofscore.js``, and both are tested against ``tests/vectors.json``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

Severity = Literal["critical", "high", "medium", "low"]
Verdict = Literal["exposed", "partial", "protected"]

_SEVERITY_ORDER: dict[Severity, int] = {"critical": 0, "high": 1, "medium": 2, "low": 3}
_DMARC_VERSION = re.compile(r"^[vV]\s*=\s*DMARC1\s*(;|$)")
_DMARC_LOOKALIKE = re.compile(r"DMARC1|(^|;)\s*p\s*=", re.IGNORECASE)
_SPF_VERSION = re.compile(r"^v=spf1(\s|$)", re.IGNORECASE)
_SPF_ALL = re.compile(r"^([+\-~?]?)all$", re.IGNORECASE)
_SPF_LOOKUP = re.compile(r"^[+\-~?]?(include|a|mx|ptr|exists)(:|/|$)|^redirect=", re.IGNORECASE)
_MAX_SPF_LOOKUPS = 10


@dataclass(frozen=True)
class Finding:
    code: str
    severity: Severity
    title: str
    fix: str


@dataclass(frozen=True)
class Assessment:
    verdict: Verdict
    findings: tuple[Finding, ...]
    dmarc_record: str | None
    spf_record: str | None


def dmarc_tags(record: str) -> dict[str, str]:
    tags: dict[str, str] = {}
    for part in record.split(";"):
        key, sep, value = part.partition("=")
        if sep:
            tags[key.strip().lower()] = value.strip()
    return tags


def _assess_dmarc(records: list[str]) -> tuple[Verdict, list[Finding], str | None]:
    valid = [r for r in records if _DMARC_VERSION.match(r.strip())]
    if not valid:
        broken = next((r for r in records if _DMARC_LOOKALIKE.search(r)), None)
        if broken is not None:
            fixed = "v=" + broken.strip() if broken.strip().startswith("DMARC1") else broken
            return (
                "exposed",
                [
                    Finding(
                        "DMARC_MALFORMED",
                        "critical",
                        "A DMARC record exists but is malformed, so receivers ignore it entirely.",
                        f"Publish a record that starts with v=DMARC1, e.g.: {fixed}",
                    )
                ],
                None,
            )
        return (
            "exposed",
            [
                Finding(
                    "DMARC_MISSING",
                    "high",
                    "No DMARC record. Receivers have no instruction to reject mail forging this domain.",
                    "Publish _dmarc TXT: v=DMARC1; p=none; rua=mailto:<reports address>, then move to "
                    "p=reject once reports show all legitimate mail passes.",
                )
            ],
            None,
        )
    if len(valid) > 1:
        return (
            "exposed",
            [
                Finding(
                    "DMARC_MULTIPLE",
                    "high",
                    "More than one DMARC record. Receivers treat this as no policy at all.",
                    "Keep exactly one v=DMARC1 TXT record at _dmarc.",
                )
            ],
            None,
        )
    return _assess_dmarc_policy(valid[0])


def _assess_dmarc_policy(record: str) -> tuple[Verdict, list[Finding], str | None]:
    tags = dmarc_tags(record)
    policy = tags.get("p", "").lower()
    findings: list[Finding] = []
    if "rua" not in tags:
        findings.append(
            Finding(
                "DMARC_NO_REPORTS",
                "low",
                "No aggregate report address (rua), so nobody sees who sends mail as this domain.",
                "Add rua=mailto:<reports address>.",
            )
        )
    if policy not in ("none", "quarantine", "reject"):
        findings.append(
            Finding(
                "DMARC_POLICY_INVALID",
                "high",
                f"DMARC policy is missing or invalid (p={policy or '<absent>'}), so nothing is enforced.",
                "Set p=reject (or p=quarantine while you confirm legitimate senders).",
            )
        )
        return "exposed", findings, record
    if policy == "none":
        findings.append(
            Finding(
                "DMARC_MONITOR_ONLY",
                "high",
                "DMARC is monitor-only (p=none). Forged mail is still delivered.",
                "Review the rua reports, align legitimate senders, then set p=quarantine and p=reject.",
            )
        )
        return "exposed", findings, record
    verdict: Verdict = "protected"
    if policy == "quarantine":
        findings.append(
            Finding(
                "DMARC_QUARANTINE",
                "low",
                "Forged mail is sent to spam rather than rejected.",
                "Move to p=reject when ready.",
            )
        )
    pct = tags.get("pct", "100")
    if not pct.isdigit() or int(pct) < 100:
        verdict = "partial"
        findings.append(
            Finding(
                "DMARC_PARTIAL_PCT",
                "medium",
                f"Policy applies to only pct={pct}% of failing mail; the rest is delivered.",
                "Remove pct or set pct=100.",
            )
        )
    if tags.get("sp", "").lower() == "none":
        verdict = "partial"
        findings.append(
            Finding(
                "DMARC_SUBDOMAIN_NONE",
                "medium",
                "Subdomains are unprotected (sp=none), e.g. payments.<domain> can be forged.",
                "Remove sp=none or set sp=reject.",
            )
        )
    return verdict, findings, record


def _assess_spf(records: list[str]) -> tuple[bool, list[Finding], str | None]:
    """Return (passes_everyone, findings, record)."""
    spf = [r for r in records if _SPF_VERSION.match(r.strip())]
    if not spf:
        return (
            False,
            [
                Finding(
                    "SPF_MISSING",
                    "medium",
                    "No SPF record. If this domain sends no mail, say so explicitly.",
                    "Publish an SPF record listing your senders ending in -all; for a domain that sends "
                    "no mail, publish: v=spf1 -all",
                )
            ],
            None,
        )
    if len(spf) > 1:
        return (
            False,
            [
                Finding(
                    "SPF_MULTIPLE",
                    "high",
                    "More than one SPF record. SPF evaluation fails with a permanent error.",
                    "Merge into a single v=spf1 record.",
                )
            ],
            None,
        )
    record = spf[0].strip()
    terms = record.split()[1:]
    findings: list[Finding] = []
    lookups = sum(1 for t in terms if _SPF_LOOKUP.match(t))
    if lookups > _MAX_SPF_LOOKUPS:
        findings.append(
            Finding(
                "SPF_TOO_MANY_LOOKUPS",
                "high",
                f"{lookups} DNS-lookup terms at the top level alone; SPF allows 10, so it fails.",
                "Flatten or remove includes to stay within 10 lookups.",
            )
        )
    all_match = next((m for m in (_SPF_ALL.match(t) for t in terms) if m), None)
    if all_match is None:
        if not any(t.lower().startswith("redirect=") for t in terms):
            findings.append(
                Finding(
                    "SPF_NO_ALL",
                    "medium",
                    "SPF has no 'all' at the end, so unlisted senders get a neutral result, not a fail.",
                    f"Append -all: {record} -all",
                )
            )
        return False, findings, record
    qualifier = all_match.group(1) or "+"
    if qualifier == "+":
        findings.append(
            Finding(
                "SPF_PASS_ALL",
                "critical",
                "SPF authorises every server on the internet (+all). Forged mail passes SPF and DMARC.",
                "Replace +all with -all.",
            )
        )
        return True, findings, record
    if qualifier == "?":
        findings.append(
            Finding(
                "SPF_NEUTRAL_ALL",
                "medium",
                "SPF ends in ?all, which asserts nothing about unlisted senders.",
                "Replace ?all with -all (or ~all while testing).",
            )
        )
    return False, findings, record


def assess(spf_txt: list[str], dmarc_txt: list[str]) -> Assessment:
    """Assess the TXT records found at <domain> and _dmarc.<domain>."""
    verdict, dmarc_findings, dmarc_record = _assess_dmarc(dmarc_txt)
    passes_everyone, spf_findings, spf_record = _assess_spf(spf_txt)
    if passes_everyone:
        verdict = "exposed"
    findings = sorted(dmarc_findings + spf_findings, key=lambda f: (_SEVERITY_ORDER[f.severity], f.code))
    return Assessment(verdict, tuple(findings), dmarc_record, spf_record)
