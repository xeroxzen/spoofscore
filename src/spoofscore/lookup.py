"""Fetch the TXT records spoofscore needs, telling 'no record' apart from 'lookup failed'."""

from __future__ import annotations

import dns.exception
import dns.resolver

from spoofscore.assess import Assessment, assess

_TIMEOUT_SECONDS = 4.0


class DomainNotFound(Exception):
    """The domain does not exist (NXDOMAIN)."""


class LookupFailed(Exception):
    """DNS could not answer (timeout, SERVFAIL). Absence of records is unknown."""


def normalise_domain(raw: str) -> str:
    domain = raw.strip().lower().removeprefix("https://").removeprefix("http://")
    domain = domain.split("/", 1)[0].split("@")[-1].rstrip(".")
    if not domain or "." not in domain or len(domain) > 253:
        raise ValueError(f"not a domain name: {raw!r}")
    return domain


def _txt(resolver: dns.resolver.Resolver, name: str, *, missing_ok: bool) -> list[str]:
    try:
        answer = resolver.resolve(name, "TXT")
    except dns.resolver.NXDOMAIN as exc:
        if missing_ok:
            return []
        raise DomainNotFound(name) from exc
    except dns.resolver.NoAnswer:
        return []
    except (dns.exception.Timeout, dns.resolver.NoNameservers) as exc:
        raise LookupFailed(name) from exc
    return [
        b"".join(rdata.strings).decode("utf-8", errors="replace")
        for rdata in answer
        if rdata.rdtype == dns.rdatatype.TXT
    ]


def check_domain(raw_domain: str, resolver: dns.resolver.Resolver | None = None) -> Assessment:
    """Look up <domain> and _dmarc.<domain> TXT records and assess them."""
    domain = normalise_domain(raw_domain)
    res = resolver or dns.resolver.Resolver()
    res.lifetime = _TIMEOUT_SECONDS
    spf_txt = _txt(res, domain, missing_ok=False)
    dmarc_txt = _txt(res, f"_dmarc.{domain}", missing_ok=True)
    return assess(spf_txt, dmarc_txt)
