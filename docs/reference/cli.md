# CLI reference

## Synopsis

```text
spoofscore [--json] DOMAIN [DOMAIN ...]
```

## Arguments

| Argument | Description |
|---|---|
| `DOMAIN` | A domain, an email address or a URL. `you@example.com`, `https://example.com/path` and `EXAMPLE.COM.` all check `example.com`. |

## Options

| Option | Description |
|---|---|
| `--json` | Print one JSON object per domain, one per line, instead of text. |
| `-h`, `--help` | Show help and exit. |

## Exit status

| Status | Meaning |
|---|---|
| `0` | Every domain is `protected`. |
| `1` | At least one domain is `exposed` or `partial`, and no lookup failed. |
| `2` | At least one domain was invalid, doesn't exist, or couldn't be looked up. Takes priority over `1`. |

A domain that triggers only low-severity findings, such as `DMARC_NO_REPORTS`, is still `protected` and exits `0`.

## Text output

```text
example.com: PROTECTED
  Unlikely: receivers are told to reject or quarantine forged mail.
  DMARC: v=DMARC1;p=reject;sp=reject;adkim=s;aspf=s
  SPF:   v=spf1 -all
  [low] DMARC_NO_REPORTS: No aggregate report address (rua), so nobody sees who sends mail as this domain.
      fix: Add rua=mailto:<reports address>.
```

`DMARC` and `SPF` show the record that was assessed, or `(none in effect)` when there's no valid record.

Errors go to standard error, one line per domain:

```text
nonexistent.example: domain does not exist
example.com: DNS lookup failed; result unknown, try again
```

## JSON output

```json
{
  "domain": "example.com",
  "verdict": "protected",
  "findings": [
    {
      "code": "DMARC_NO_REPORTS",
      "severity": "low",
      "title": "No aggregate report address (rua), so nobody sees who sends mail as this domain.",
      "fix": "Add rua=mailto:<reports address>."
    }
  ],
  "dmarc_record": "v=DMARC1;p=reject;sp=reject;adkim=s;aspf=s",
  "spf_record": "v=spf1 -all"
}
```

Each line is printed compactly; it's expanded here for reading.

| Field | Type | Description |
|---|---|---|
| `domain` | string | The argument as given, before normalisation. |
| `verdict` | `"exposed"` \| `"partial"` \| `"protected"` | See [Checks](checks.md#how-the-verdict-is-decided). |
| `findings` | array | Sorted by severity, then code. Empty when nothing was found. |
| `findings[].code` | string | A [check code](checks.md). Stable across versions. |
| `findings[].severity` | `"critical"` \| `"high"` \| `"medium"` \| `"low"` | |
| `findings[].title` | string | Plain-language explanation. Wording may change. |
| `findings[].fix` | string | What to publish. Wording may change. |
| `dmarc_record` | string \| null | The DMARC record assessed, or `null` if none is in effect. |
| `spf_record` | string \| null | The SPF record assessed, or `null` if none is in effect. |

Domains that fail are reported on standard error only, with no JSON line.

## DNS behaviour

- Queries use the system resolver, with a 4-second limit per lookup.
- A domain that doesn't exist (NXDOMAIN) is an error, not a missing record.
- A missing `_dmarc` name is a missing DMARC record.
- A timeout or SERVFAIL is reported as a failed lookup, never as a missing record.
- Multi-string TXT records are joined with no separator, as RFC 7208 requires.
