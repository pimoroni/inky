# Python Reference Snapshot

This directory is for Python reference material only while the C++ port is being completed.

The original repository README has been preserved at:

- `reference/python/README_ORIGINAL.md`

## Intended Use

- Read behavior from Python implementation when porting.
- Do not import or execute Python code from C++ build/runtime paths.
- Keep references pinned to a specific commit/tag.

## Upstream Source

- Repository: `https://github.com/pimoroni/inky`
- Pinned ref: `e4023d974e944da2cd34cf1a15464d8405ebcd6d`
- Date pinned: `2025-11-24 12:27:07 UTC` (`2025-11-24 13:27 CET`)
- Context: `imports sort for linting` (commit where C++ port baseline tracking started)

## Contents

- `driver/` selected upstream modules needed for porting
- `examples/` selected examples used for parity checks
- `tests/` archived Python tests kept only for behavioral reference
- `packaging/` Python packaging and QA metadata from the original project
- `scripts/` original Python install/build helper scripts kept as historical reference
- `notes/` optional mapping notes from Python symbols to C++ symbols

Only copy the minimal subset needed for active porting work.

## Current Layout

- `reference/python/driver/`
- `reference/python/examples/`
- `reference/python/tests/`
- `reference/python/packaging/`
- `reference/python/scripts/`
- `reference/python/notes/`

## Current Snapshot Contents

Driver modules moved for C++ parity work:

- `reference/python/driver/inky/inky.py`
- `reference/python/driver/inky/inky_uc8159.py`
- `reference/python/driver/inky/inky_e673.py`
- `reference/python/driver/inky/eeprom.py`
- `reference/python/driver/inky/mock.py`

Examples moved for behavior checks:

- `reference/python/examples/spectra6/hello_world.py`
- `reference/python/examples/spectra6/image.py`
- `reference/python/examples/spectra6/stripes.py`
- `reference/python/examples/spectra6/buttons.py`
- `reference/python/examples/spectra6/led.py`
- `reference/python/examples/spectra6/comics/comic.py`

Python packaging metadata preserved as reference:

- `reference/python/pyproject.toml`
- `reference/python/packaging/.coveragerc`
- `reference/python/packaging/MANIFEST.in`
- `reference/python/packaging/requirements.txt`
- `reference/python/packaging/requirements-dev.txt`
- `reference/python/packaging/requirements-examples.txt`
- `reference/python/packaging/tox.ini`

Archived Python helper scripts:

- `reference/python/scripts/Makefile`
- `reference/python/scripts/check.sh`
- `reference/python/scripts/install.sh`
- `reference/python/scripts/uninstall.sh`
