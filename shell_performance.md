# Shell Performance Benchmark Results

**Date:** 2026-02-22 13:13:11
**Iterations per test:** 10
**Target:** <100ms prompt latency

## Baseline Measurements

| Scenario | Average Time | Status |
|----------|--------------|--------|
| Empty directory | 24ms | ✅ PASS |
| Git repository | 48ms | ✅ PASS |
| Python project | 32ms | ✅ PASS |
| Current project | 61ms | ✅ PASS |

## Analysis

- **Overall status:** All tests passing ✅
- **Improvement:** Python project reduced from 131ms to 32ms by disabling pyenv calls

## Notes

- Measurements taken using `starship prompt` command
- Times include full prompt rendering with configured modules
- Target is sub-100ms for responsive shell experience
- Python version detection uses interpreter instead of pyenv for speed
