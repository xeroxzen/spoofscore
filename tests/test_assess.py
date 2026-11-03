from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from spoofscore import assess, normalise_domain

VECTORS: list[dict[str, Any]] = json.loads(
    (Path(__file__).parent / "vectors.json").read_text(encoding="utf-8")
)


@pytest.mark.parametrize("case", VECTORS, ids=[v["name"] for v in VECTORS])
def test_shared_vectors(case: dict[str, Any]) -> None:
    result = assess(case["spf"], case["dmarc"])
    assert result.verdict == case["verdict"]
    assert sorted(f.code for f in result.findings) == sorted(case["codes"])


def test_malformed_dmarc_fix_restores_prefix() -> None:
    result = assess(["v=spf1 -all"], ["DMARC1; p=reject; rua=mailto:a@example.com"])
    assert "v=DMARC1; p=reject; rua=mailto:a@example.com" in result.findings[0].fix


def test_findings_sorted_by_severity() -> None:
    result = assess(["v=spf1 +all"], ["v=DMARC1; p=none"])
    severities = [f.severity for f in result.findings]
    assert severities == ["critical", "high", "low"]


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Example.COM", "example.com"),
        ("https://www.example.com/path", "www.example.com"),
        ("ceo@example.co.zw", "example.co.zw"),
        ("example.com.", "example.com"),
    ],
)
def test_normalise_domain(raw: str, expected: str) -> None:
    assert normalise_domain(raw) == expected


@pytest.mark.parametrize("raw", ["", "localhost", "a" * 254 + ".com"])
def test_normalise_domain_rejects(raw: str) -> None:
    with pytest.raises(ValueError):
        normalise_domain(raw)
