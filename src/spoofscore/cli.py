"""spoofscore CLI: can someone send email pretending to be this domain?"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict

from spoofscore.assess import Assessment
from spoofscore.lookup import DomainNotFound, LookupFailed, check_domain

HEADLINE = {
    "exposed": "Yes, mail forging this domain is likely to be delivered.",
    "partial": "Partly: some forged mail is still delivered.",
    "protected": "Unlikely: receivers are told to reject or quarantine forged mail.",
}


def _render(domain: str, result: Assessment) -> str:
    lines = [f"{domain}: {result.verdict.upper()}", f"  {HEADLINE[result.verdict]}"]
    lines.append(f"  DMARC: {result.dmarc_record or '(none in effect)'}")
    lines.append(f"  SPF:   {result.spf_record or '(none in effect)'}")
    for f in result.findings:
        lines.append(f"  [{f.severity}] {f.code}: {f.title}")
        lines.append(f"      fix: {f.fix}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="spoofscore", description=__doc__)
    parser.add_argument("domains", nargs="+", metavar="DOMAIN")
    parser.add_argument("--json", action="store_true", help="emit JSON lines")
    args = parser.parse_args(argv)

    status = 0
    for raw in args.domains:
        try:
            result = check_domain(raw)
        except ValueError as exc:
            print(f"{raw}: {exc}", file=sys.stderr)
            status = 2
            continue
        except DomainNotFound:
            print(f"{raw}: domain does not exist", file=sys.stderr)
            status = 2
            continue
        except LookupFailed:
            print(f"{raw}: DNS lookup failed; result unknown, try again", file=sys.stderr)
            status = 2
            continue
        if args.json:
            print(json.dumps({"domain": raw, **asdict(result)}))
        else:
            print(_render(raw, result) + "\n")
        if result.verdict != "protected" and status == 0:
            status = 1
    return status


if __name__ == "__main__":
    raise SystemExit(main())
