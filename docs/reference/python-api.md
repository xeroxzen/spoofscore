# Python API reference

Everything below is importable from `spoofscore`.

| Name | Kind | Purpose |
|---|---|---|
| [`check_domain`](#check_domain) | function | Look up a domain's records and assess them |
| [`assess`](#assess) | function | Assess records you already have, with no network access |
| [`normalise_domain`](#normalise_domain) | function | Reduce an email address or URL to a domain |
| [`Assessment`](#assessment) | dataclass | Result of an assessment |
| [`Finding`](#finding) | dataclass | One problem and its fix |
| [`DomainNotFound`](#domainnotfound) | exception | The domain doesn't exist |
| [`LookupFailed`](#lookupfailed) | exception | DNS couldn't answer |

## `check_domain`

```python
check_domain(raw_domain: str, resolver: dns.resolver.Resolver | None = None) -> Assessment
```

Normalises `raw_domain`, looks up TXT records at the domain and at `_dmarc.<domain>`, and returns `assess` of the results.

| Parameter | Description |
|---|---|
| `raw_domain` | A domain, email address or URL. |
| `resolver` | A [dnspython](https://www.dnspython.org/) resolver. Defaults to the system resolver. Its `lifetime` is set to 4 seconds. |

**Raises:**

- `ValueError` if `raw_domain` isn't a domain name.
- `DomainNotFound` if the domain doesn't exist.
- `LookupFailed` on a timeout or when no nameserver answers.

To query a specific resolver:

```python
import dns.resolver
from spoofscore import check_domain

resolver = dns.resolver.Resolver(configure=False)
resolver.nameservers = ["1.1.1.1"]
result = check_domain("example.com", resolver)
```

## `assess`

```python
assess(spf_txt: list[str], dmarc_txt: list[str]) -> Assessment
```

A pure function over TXT strings. Pass every TXT record found at the domain as `spf_txt`, and every one at `_dmarc` as `dmarc_txt`. Records that aren't SPF or DMARC are ignored. Join multi-string records before passing them.

**Raises:** nothing.

## `normalise_domain`

```python
normalise_domain(raw: str) -> str
```

Lowercases, strips `http://` or `https://`, a path, anything up to `@`, and a trailing dot.

**Raises:** `ValueError` if the result has no dot or is longer than 253 characters.

```python
normalise_domain("Accounts@Example.COM")  # "example.com"
normalise_domain("https://example.com/about")  # "example.com"
```

## `Assessment`

```python
@dataclass(frozen=True)
class Assessment:
    verdict: Literal["exposed", "partial", "protected"]
    findings: tuple[Finding, ...]
    dmarc_record: str | None
    spf_record: str | None
```

`findings` is sorted by severity, then code. `dmarc_record` and `spf_record` are the records that were assessed, or `None` when no valid one is in effect.

## `Finding`

```python
@dataclass(frozen=True)
class Finding:
    code: str
    severity: Literal["critical", "high", "medium", "low"]
    title: str
    fix: str
```

`code` is stable and listed in [Checks](checks.md). `title` and `fix` are for people, and their wording may change between versions.

## `DomainNotFound`

Raised when the domain returns NXDOMAIN. Subclass of `Exception`.

## `LookupFailed`

Raised when DNS can't answer: a timeout or no responding nameserver. The records may exist. Subclass of `Exception`.
