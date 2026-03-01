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
- `notes/` optional mapping notes from Python symbols to C++ symbols

Only copy the minimal subset needed for active porting work.

## Current Layout

- `reference/python/driver/`
- `reference/python/examples/`
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
