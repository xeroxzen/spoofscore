# Check many domains in CI

This guide shows you how to run spoofscore on a schedule against every domain you own, so a DNS change that weakens protection fails a build instead of going unnoticed.

## Before you begin

- A list of your domains, including parked ones and country variants.
- A CI system that can run a scheduled job. The example uses GitHub Actions.

## Steps

1. Put your domains in a file, one per line:

   ```text
   # domains.txt
   yourcompany.co.zw
   yourcompany.com
   yourcompany-parked.co.zw
   ```

2. Run spoofscore against the file. `grep` skips lines starting with `#`:

   ```bash
   uvx spoofscore $(grep -v '^#' domains.txt)
   ```

   Don't pipe through `xargs`: it replaces any non-zero exit status with `123`, which hides the difference between exposed and failed.

   The command exits `1` if any domain is exposed or partial, and `2` if any lookup failed.

3. Schedule it. This GitHub Actions workflow runs every Monday at 06:00 UTC:

   ```yaml
   # .github/workflows/mail-posture.yml
   name: Mail posture
   on:
     schedule:
       - cron: "0 6 * * 1"
     workflow_dispatch:
   jobs:
     check:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v4
         - uses: astral-sh/setup-uv@v6
         - run: uvx spoofscore $(grep -v '^#' domains.txt)
   ```

## Treat a lookup failure differently

Exit status `2` means DNS didn't answer, not that the domain is unprotected. If you'd rather retry than alert, check the status explicitly:

```bash
status=0
uvx spoofscore $(grep -v '^#' domains.txt) || status=$?
if [ "$status" -eq 2 ]; then
  echo "DNS lookup failed; retry later"
  exit 0
fi
exit "$status"
```

> [!CAUTION]
> Status `2` takes priority over `1`. If one lookup fails and another domain is exposed in the same run, the run exits `2`, and this script hides the exposed domain. Run one domain per invocation if you need both signals.

## Keep a history

With `--json`, each run produces one line per domain. Save the output as a build artifact to see when a record changed:

```bash
uvx spoofscore --json $(grep -v '^#' domains.txt) > posture.jsonl
```

The fields are described in the [CLI reference](../reference/cli.md#json-output).
