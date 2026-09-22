# Feature: sagaz-cli-releases

Rename the vendored laya fork distribution to **sagaz-cli** and set up releases for
Linux and macOS (universal wheel + standalone per-platform binaries).

Decisions (user-confirmed):
- Name: `sagaz-cli` (free on PyPI; `laya-cli` is taken by an unrelated active project).
- Release format: both — universal wheel AND standalone binaries (user accepted the size cost of shipping torch).
- Import package stays `laya` (no code refactor); CLI gains `sagaz` entry point, `laya` kept as alias.

## Tasks

- [x] T1 — Track feature (this file + Engram mirror + todo)
- [x] T2 — pyproject.toml: name = "sagaz-cli", scripts: sagaz (primary) + laya (alias), python classifiers
- [x] T3 — .github/workflows/release.yml: build wheel+sdist (tests first), PyInstaller
      binaries matrix (ubuntu-latest x86_64, macos-latest arm64, CPU-only torch, onedir,
      tar.gz, ad-hoc codesign on mac), version/tag check, GitHub Release publish,
      PyPI trusted-publisher job (needs one-time PyPI setup by user)
- [x] T3b — Vendored .github/workflows/ci.yml (tests/test_packaging.py requires it)
- [x] T4 — Local validation (see Evidence)
- [x] T5 — Work-unit commit on feature branch `feat/sagaz-cli-releases`

## Evidence

- Linux binary built locally: PyInstaller 6.22.3, onedir, CPU-only torch 2.14.0+cpu — 2m32s.
- Bundle: dist/pyinstaller/sagaz-cli = 868 MB; dist/sagaz-cli-0.3.6-linux-x86_64.tar.gz = 282 MB.
- Binary smoke tests: `--help` exit 0 (1.6 s startup), `presets` exit 0 (real code path). No global `--version` flag exists in the CLI.
- macOS binary: NOT buildable on Linux (PyInstaller cannot cross-compile); produced by the `binaries` job on `macos-latest` (arm64) in release.yml.
- Wheel: `sagaz_cli-0.3.6-py3-none-any.whl`, console_scripts: sagaz + laya.
- tests/test_packaging.py: 9 passed, 0 failed (after vendoring ci.yml + adding classifiers).
- YAML parse: release.yml + ci.yml OK. TOML: name sagaz-cli OK.
- Extra files: packaging/sagaz_cli_entry.py (PyInstaller launcher); packaging/*.spec gitignored (machine-specific paths).

## Out of scope / user decisions pending

- Push, tag (v0.3.6 or bump), and actual release creation remain user actions.
- PyPI publishing requires the user to add a Trusted Publisher for eddraz/laya -> sagaz-cli.
- README rebranding to sagaz-cli (user owns README content per their preference).
