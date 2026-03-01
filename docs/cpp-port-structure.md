# C++ Port Structure and Boundaries

## Goal

Keep the C++ implementation independent and production-ready while retaining Python code as a temporary reference during porting.

## Ownership

- C++ production code:
  - `include/`
  - `src/`
  - `examples/` (C++ examples only)
  - `tests/` (C++ tests only)
- Python reference only:
  - `reference/python/`

## Rules

1. C++ code must not import, execute, or depend on Python modules at build or runtime.
2. Python files in `reference/python/` are read-only reference material.
3. Any behavior copied from Python must be captured by C++ tests before marking a porting task complete.
4. Linux hardware details must stay behind the C++ hardware abstraction (`Gpio`, `Spi`), not leak into core display logic.

## Recommended Workflow

1. Pick one feature/behavior from Python reference.
2. Write a small behavior note in `docs/porting-status.md`.
3. Implement/adjust C++ code.
4. Add tests that prove parity.
5. Mark the item as `ported` and `verified`.

## Source Pinning

Python reference should be pinned to an exact upstream commit/tag documented in:

- `reference/python/README.md`

Do not rely on "latest main" for behavior verification.

## Reference Layout

Keep copied Python files under:

- `reference/python/driver/`
- `reference/python/examples/`
- `reference/python/notes/`

Do not place new Python reference files in root-level C++ source folders.
