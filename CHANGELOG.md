# Changelog

All notable changes are recorded here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow [Semantic Versioning](https://semver.org/). Finding codes are part of the public interface: renaming or removing one is a breaking change.

## [0.1.0] - 2026-11-04

### Added

- 15 checks across DMARC and SPF, with plain-language titles and suggested fixes.
- Verdicts: `exposed`, `partial`, `protected`.
- Python CLI with text and JSON-lines output and meaningful exit codes.
- Python library: `check_domain`, `assess`, `normalise_domain`.
- Static web page using DNS-over-HTTPS, with `?d=` links.
- Shared test vectors keeping the Python and JavaScript rules identical.

[0.1.0]: https://github.com/xeroxzen/spoofscore/releases/tag/v0.1.0
