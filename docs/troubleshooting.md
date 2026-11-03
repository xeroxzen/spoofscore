# Troubleshooting

## I fixed my record, but spoofscore still shows the old one

DNS answers are cached until the record's TTL expires, often one hour and sometimes a day. Check the authoritative value directly:

```bash
dig +short NS yourcompany.co.zw
dig +short TXT _dmarc.yourcompany.co.zw @<one of those nameservers>
```

If the nameserver shows the new value, wait for caches to expire. If it doesn't, the change wasn't published.

## `DMARC_MALFORMED`, but my DNS panel shows `v=DMARC1`

Some DNS panels add or strip quotes, or split the value. Check what's actually served with `dig +short TXT _dmarc.yourcompany.co.zw`. The answer must start with `"v=DMARC1`. Look for a leading space, a stray quote inside the value, or a second record you didn't know about.

## `DMARC_MULTIPLE`, but I only added one record

Your DNS provider, mail provider or a previous administrator may have added another. `dig +short TXT _dmarc.yourcompany.co.zw` lists every record; delete all but one.

## `DNS lookup failed; result unknown`

The resolver timed out or returned SERVFAIL. This isn't a finding about the domain. Try again, or try another resolver. If it fails consistently, the domain's nameservers may be unreachable or misconfigured, which is worth fixing for its own sake.

## The web page says "Couldn't complete the check" but the CLI works

The web page uses Cloudflare's DNS-over-HTTPS service. A network that blocks `cloudflare-dns.com`, or a browser extension that blocks it, stops the page working. Use the CLI, which uses your system resolver.

## `SPF_TOO_MANY_LOOKUPS` doesn't appear, but my mail provider says I'm over the limit

spoofscore counts only top-level terms. Each `include:` can contain further lookups that also count towards the limit of 10. Use a tool that expands includes recursively to get the full count.

## The web page and the CLI give different results

They implement the same rules and are tested against the same cases, so a difference usually means they received different DNS answers: one resolver had a cached old value. If the records are the same and the results differ, that's a bug. [Open an issue](https://github.com/xeroxzen/spoofscore/issues) with both records.
