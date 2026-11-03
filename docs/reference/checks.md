# Checks

Every finding spoofscore can report, ordered by severity. The Python and JavaScript implementations report the same codes for the same records; both are tested against [`tests/vectors.json`](../../tests/vectors.json).

## How the verdict is decided

1. DMARC decides the starting verdict:
   - No valid record, more than one, an invalid policy, or `p=none`: **exposed**.
   - `p=reject` or `p=quarantine`: **protected**, downgraded to **partial** by `pct` below 100 or `sp=none`.
2. SPF can only make it worse. `+all` forces **exposed**, because forged mail then passes DMARC through SPF alignment.
3. Other SPF findings are reported but don't change the verdict. DMARC enforcement still applies when SPF is weak.

## Summary

| Code | Severity | Verdict effect |
|---|---|---|
| [`DMARC_MALFORMED`](#dmarc_malformed) | critical | exposed |
| [`SPF_PASS_ALL`](#spf_pass_all) | critical | exposed |
| [`DMARC_MISSING`](#dmarc_missing) | high | exposed |
| [`DMARC_MULTIPLE`](#dmarc_multiple) | high | exposed |
| [`DMARC_POLICY_INVALID`](#dmarc_policy_invalid) | high | exposed |
| [`DMARC_MONITOR_ONLY`](#dmarc_monitor_only) | high | exposed |
| [`SPF_MULTIPLE`](#spf_multiple) | high | none |
| [`SPF_TOO_MANY_LOOKUPS`](#spf_too_many_lookups) | high | none |
| [`DMARC_PARTIAL_PCT`](#dmarc_partial_pct) | medium | partial |
| [`DMARC_SUBDOMAIN_NONE`](#dmarc_subdomain_none) | medium | partial |
| [`SPF_MISSING`](#spf_missing) | medium | none |
| [`SPF_NO_ALL`](#spf_no_all) | medium | none |
| [`SPF_NEUTRAL_ALL`](#spf_neutral_all) | medium | none |
| [`DMARC_QUARANTINE`](#dmarc_quarantine) | low | none |
| [`DMARC_NO_REPORTS`](#dmarc_no_reports) | low | none |

## Critical

### `DMARC_MALFORMED`

**What it means.** A TXT record at `_dmarc` looks like DMARC (it contains `DMARC1` or a `p=` tag) but doesn't start with `v=DMARC1`.

**Why it matters.** Receivers discard any record that doesn't begin with `v=DMARC1` (RFC 7489 §6.6.3), so the domain has no policy, however strict the rest of the record is. No reports are sent either, so the owner gets no sign that anything is wrong.

**Example.**

```text
DMARC1; p=reject; rua=mailto:dmarc@example.com
```

**Fix.** Add `v=` at the start. spoofscore suggests the corrected record.

```text
v=DMARC1; p=reject; rua=mailto:dmarc@example.com
```

> [!WARNING]
> The moment the record becomes valid, its policy is enforced. If it says `p=reject` and you haven't confirmed every legitimate sender, publish it with `p=none` first. See [Move a domain to `p=reject` safely](../how-to/move-to-p-reject.md).

### `SPF_PASS_ALL`

**What it means.** SPF ends in `+all` or a bare `all`.

**Why it matters.** Every server on the internet passes SPF for the domain. Because DMARC accepts an aligned SPF pass, forged mail passes DMARC too, even with `p=reject`.

**Fix.** Replace `+all` with `-all`.

## High

### `DMARC_MISSING`

**What it means.** No TXT record at `_dmarc` starts with `v=DMARC1`, and none looks like a broken attempt.

**Why it matters.** Receivers have no instruction from you. Most deliver forged mail.

**Fix.** Start monitoring: `v=DMARC1; p=none; rua=mailto:<reports address>`.

### `DMARC_MULTIPLE`

**What it means.** More than one record at `_dmarc` starts with `v=DMARC1`.

**Why it matters.** RFC 7489 says receivers must treat this as no policy.

**Fix.** Delete all but one.

### `DMARC_POLICY_INVALID`

**What it means.** The `p=` tag is missing or isn't `none`, `quarantine` or `reject`.

**Fix.** Set `p=reject`, or `p=quarantine` while you confirm senders.

### `DMARC_MONITOR_ONLY`

**What it means.** `p=none`.

**Why it matters.** Forged mail is reported to you but still delivered. It's the right first stage of a rollout, and the wrong place to stay.

**Fix.** Read the `rua` reports, make every legitimate sender pass, then move to `p=quarantine` and `p=reject`.

### `SPF_MULTIPLE`

**What it means.** More than one TXT record at the domain starts with `v=spf1`.

**Why it matters.** SPF evaluation returns a permanent error, so SPF never passes for legitimate mail. With DMARC enforced, legitimate mail depends entirely on DKIM.

**Fix.** Merge them into one record.

### `SPF_TOO_MANY_LOOKUPS`

**What it means.** The record has more than 10 terms that need a DNS lookup (`include`, `a`, `mx`, `ptr`, `exists`, `redirect`) at the top level.

**Why it matters.** RFC 7208 caps SPF at 10 lookups. Beyond that, evaluation fails with a permanent error.

**Fix.** Remove services you no longer use, or replace `include:` terms with the IP ranges they publish.

> [!NOTE]
> spoofscore counts top-level terms only. Each `include:` can contain more lookups, so a record that passes this check can still exceed the limit.

## Medium

### `DMARC_PARTIAL_PCT`

**What it means.** `pct` is below 100, or isn't a number.

**Why it matters.** The policy applies only to that percentage of failing mail. The rest is delivered.

**Fix.** Remove `pct` or set `pct=100`.

### `DMARC_SUBDOMAIN_NONE`

**What it means.** `sp=none`.

**Why it matters.** Subdomains have no enforcement. `payments.example.com` can be forged even though `example.com` can't.

**Fix.** Remove `sp=none`. Subdomains then inherit `p`.

### `SPF_MISSING`

**What it means.** No TXT record at the domain starts with `v=spf1`.

**Fix.** Publish a record listing your senders and ending in `-all`. For a domain that sends no mail: `v=spf1 -all`.

### `SPF_NO_ALL`

**What it means.** SPF has no `all` term and no `redirect=`.

**Why it matters.** Unlisted servers get a neutral result instead of a fail.

**Fix.** Append `-all`. spoofscore suggests the full corrected record.

### `SPF_NEUTRAL_ALL`

**What it means.** SPF ends in `?all`.

**Fix.** Replace it with `-all`, or `~all` while testing.

## Low

### `DMARC_QUARANTINE`

**What it means.** `p=quarantine`.

**Why it matters.** Forged mail goes to spam, where recipients can still find and act on it.

**Fix.** Move to `p=reject` when reports are clean.

### `DMARC_NO_REPORTS`

**What it means.** No `rua` tag.

**Why it matters.** Nobody receives reports, so you can't see who sends mail as your domain, legitimately or otherwise.

**Fix.** Add `rua=mailto:<reports address>`.
