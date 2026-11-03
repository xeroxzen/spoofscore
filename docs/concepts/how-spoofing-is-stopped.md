# How email spoofing is stopped

Anyone can send an email with any address in the `From:` line. Email was designed that way. This page explains the two DNS records that let receiving mail servers tell a forgery from the real thing, and why one small mistake in either can switch the protection off.

## The `From:` address isn't checked by default

When a server sends mail, it states two addresses:

- The **envelope sender** (`MAIL FROM`), used for bounces. Recipients usually never see it.
- The **header `From:`**, which is what the recipient's mail app shows.

Neither is verified by the protocol itself. A fraudster can send an invoice that shows `From: accounts@yourcompany.co.zw` from any server on the internet.

## SPF: which servers may send

SPF (RFC 7208) is a TXT record on your domain that lists the servers allowed to send mail for it:

```text
v=spf1 include:spf.protection.outlook.com -all
```

The final `all` term decides what happens to every server that isn't listed:

| Term | Result for unlisted servers |
|---|---|
| `-all` | Fail |
| `~all` | Soft fail, usually treated as suspicious |
| `?all` | Neutral: no statement |
| no `all` | Neutral, the same as `?all` |
| `+all` or `all` | Pass: every server on the internet is authorised |

SPF has two limits. It checks the envelope sender, not the `From:` the recipient sees. And it says nothing about what the receiver should do with a failure.

## DMARC: what to do with a failure

DMARC (RFC 7489) is a TXT record at `_dmarc.<your domain>`:

```text
v=DMARC1; p=reject; rua=mailto:dmarc-reports@yourcompany.co.zw
```

DMARC closes both gaps in SPF:

1. **Alignment.** A message passes DMARC only if SPF or DKIM passes *for a domain that matches the visible `From:`*. A fraudster can pass SPF for their own domain, but that doesn't align with yours.
2. **Policy.** The `p=` tag tells receivers what to do with mail that fails:

| Policy | What receivers do with forged mail |
|---|---|
| `p=none` | Deliver it. Send you a report. |
| `p=quarantine` | Put it in spam. |
| `p=reject` | Refuse it. |

`p=none` is a monitoring mode. It's the right first step, and the wrong place to stay. While it's in place, forged mail is delivered.

The `rua=` tag is where receivers send daily aggregate reports. Those reports show every server sending mail as your domain, which is how you find legitimate senders before enforcing.

## Small mistakes that switch protection off

| Mistake | Effect |
|---|---|
| DMARC record doesn't start with `v=DMARC1` | Receivers discard the whole record (RFC 7489 §6.6.3). Even `p=reject` is ignored, and no reports are sent. |
| Two DMARC records | Receivers treat the domain as having no policy. |
| Two SPF records | SPF evaluation fails with a permanent error. |
| More than 10 DNS lookups in SPF | SPF fails with a permanent error. |
| `+all` in SPF | Every server passes SPF, and so passes DMARC alignment for your domain. |

These are why spoofscore reports a malformed record as worse than a missing one: the owner believes they're protected.

## DKIM

DKIM signs each message with a key published at `<selector>._domainkey.<your domain>`. It's the other way to pass DMARC, and it survives forwarding better than SPF. spoofscore doesn't check DKIM, because selector names can't be discovered from DNS.

## See also

- [Checks](../reference/checks.md): every finding spoofscore reports.
- [Move a domain to `p=reject` safely](../how-to/move-to-p-reject.md).
