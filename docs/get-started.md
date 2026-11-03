# Get started

This guide shows you three ways to check whether a domain can be spoofed: the web page, the command line and Python. Each takes about a minute.

## Use the web page

1. Open <https://xeroxzen.github.io/spoofscore/>, or run the page locally:

   ```bash
   git clone https://github.com/xeroxzen/spoofscore.git
   cd spoofscore
   pnpm serve
   ```

   Then open <http://localhost:8080>.

2. Enter a domain or an email address, for example `you@yourcompany.co.zw`, and select **Check**. An email address is reduced to its domain.

3. Read the headline, then each finding. Every finding has a **Fix** line with the record to publish.

To link straight to a result, add `?d=` to the URL: `http://localhost:8080/?d=example.com`.

## Use the command line

1. Install the CLI:

   ```bash
   uv tool install spoofscore
   ```

2. Check one or more domains:

   ```bash
   spoofscore example.com yourcompany.co.zw
   ```

3. For machine-readable output, add `--json`. Each domain is one line of JSON:

   ```bash
   spoofscore --json example.com
   ```

The exit status tells a script the result without parsing output: `0` when every domain is protected, `1` when any is exposed or partial, and `2` on a lookup error. See the [CLI reference](reference/cli.md).

## Use the Python library

1. Add the package:

   ```bash
   uv add spoofscore
   ```

2. Check a domain:

   ```python
   from spoofscore import check_domain

   result = check_domain("example.com")
   print(result.verdict)
   for finding in result.findings:
       print(finding.severity, finding.code, finding.fix)
   ```

3. To assess records you already have, without any DNS lookup, call `assess` directly:

   ```python
   from spoofscore import assess

   result = assess(
       spf_txt=["v=spf1 include:_spf.google.com -all"],
       dmarc_txt=["v=DMARC1; p=none; rua=mailto:dmarc@example.com"],
   )
   print(result.verdict)  # exposed
   ```

## What's next

- Understand the findings in [Checks](reference/checks.md).
- Fix an `exposed` domain without blocking your own mail: [Move a domain to `p=reject` safely](how-to/move-to-p-reject.md).
