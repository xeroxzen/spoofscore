# spoofscore

**Can someone send email pretending to be your company?**

spoofscore reads a domain's public SPF and DMARC records and answers that question in plain language, with the exact record to publish to fix each problem.

```console
$ spoofscore example.com
example.com: PROTECTED
  Unlikely: receivers are told to reject or quarantine forged mail.
  DMARC: v=DMARC1;p=reject;sp=reject;adkim=s;aspf=s
  SPF:   v=spf1 -all
  [low] DMARC_NO_REPORTS: No aggregate report address (rua), so nobody sees who sends mail as this domain.
      fix: Add rua=mailto:<reports address>.
```

It comes in two forms that share one rule set:

- **A static web page** (`web/`) that anyone can use. The browser queries public DNS through Cloudflare's DNS-over-HTTPS, so there's no server to run.
- **A Python CLI and library** for scripts, batch checks and CI.

## Install

```bash
uv tool install spoofscore
```

Until the first PyPI release, install from GitHub instead: `uv tool install git+https://github.com/xeroxzen/spoofscore`.

Or run it once without installing: `uvx spoofscore example.com`. Requires Python 3.10 or later.

## Documentation

- [Get started](docs/get-started.md): check a domain from the web page, the CLI or Python.
- Concepts
  - [How email spoofing is stopped](docs/concepts/how-spoofing-is-stopped.md): SPF, DMARC and alignment in one page.
- How-to guides
  - [Move a domain to `p=reject` safely](docs/how-to/move-to-p-reject.md)
  - [Check many domains in CI](docs/how-to/check-domains-in-ci.md)
  - [Host the web page](docs/how-to/host-the-web-page.md)
- Reference
  - [Checks](docs/reference/checks.md): every finding, why it matters and how to fix it.
  - [CLI](docs/reference/cli.md)
  - [Python API](docs/reference/python-api.md)
- [Troubleshooting](docs/troubleshooting.md)
- [Changelog](CHANGELOG.md)

## Verdicts

| Verdict | Meaning |
|---|---|
| `exposed` | No effective DMARC enforcement, or SPF that passes everyone. Forged mail is likely to be delivered. |
| `partial` | Enforcement exists but has gaps. Some forged mail is delivered. |
| `protected` | `p=reject` or `p=quarantine` applies to all mail. |

## What it doesn't check

DKIM (selectors can't be listed from DNS), nested SPF `include:` lookups, lookalike domains, and mailbox security. A `protected` verdict means the domain's published policy is sound. It doesn't mean every mail system honours it.

## Contributing and security

See [CONTRIBUTING.md](CONTRIBUTING.md) and [SECURITY.md](SECURITY.md).

## License

[MIT](LICENSE)
