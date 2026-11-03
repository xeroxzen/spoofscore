"""Check whether a domain's SPF and DMARC records stop people forging its email."""

from spoofscore.assess import Assessment, Finding, assess
from spoofscore.lookup import DomainNotFound, LookupFailed, check_domain, normalise_domain

__all__ = [
    "Assessment",
    "DomainNotFound",
    "Finding",
    "LookupFailed",
    "assess",
    "check_domain",
    "normalise_domain",
]
