# Contributing

Thanks for helping. Bug reports, new checks and documentation fixes are all welcome.

## Set up

```bash
git clone https://github.com/xeroxzen/spoofscore.git
cd spoofscore
uv sync
pnpm install
```

## One rule set, two implementations

The rules live in `src/spoofscore/assess.py` (Python) and `web/spoofscore.js` (JavaScript). Both are tested against the same cases in `tests/vectors.json`. To change a rule:

1. Add or change a case in `tests/vectors.json` first, with the records, the expected verdict and the expected codes.
2. Run both test suites and watch the new case fail.
3. Change both implementations until both pass.

A pull request that changes one implementation without the other won't be merged.

## Before you open a pull request

All of these must pass with no warnings:

```bash
uv run pytest
uv run mypy src tests
uv run ruff check .
uv run ruff format --check .
pnpm test
```

Also:

- Cite the RFC section for any new check in the pull request description.
- Add the check to [docs/reference/checks.md](docs/reference/checks.md) and the [changelog](CHANGELOG.md).
- Don't use real organisations' domains or records in tests or docs. Use `example.com` and the other names reserved by RFC 2606.

## Security issues

See [SECURITY.md](SECURITY.md).
