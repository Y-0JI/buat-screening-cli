# Phase 2 — Symbol Validation

## Objective

Prevent invalid symbol formats from reaching providers. Add consistent validation across all execution paths.

## Scope

- SymbolValidator module — single source of truth for format rules
- Gate at FallbackProvider — authoritative validation point covering all paths
- CLI pre-check — faster UX feedback, same validator
- Fix existing bug in _fetch_and_screen error type

## Not in Scope

- Symbol normalization (Phase 3)
- Provider-specific validation rules (future)
- Dynamic symbol discovery (Phase 2+)
- Changes to provider implementations

## Architecture

### Baseline Rule: `^[A-Z0-9.]{1,10}$`

Provider-agnostic. Covers IDX, NYSE, NASDAQ formats. Extensible via provider_name parameter in future.

### Data Flow

```
CLI user inputs "BBCA"
  → CLI: validate("BBCA") → OK (pre-check UX)
  → FallbackProvider.fetch("BBCA")
    → validate("BBCA") → OK (authoritative gate)
    → provider.fetch("BBCA") → ...

CLI user inputs "123"
  → CLI: validate("123") → error message (fast feedback)
  → FallbackProvider.fetch("123")
    → validate("123") → None (safety net)

AI agent or future API
  → FallbackProvider.fetch("BAD")
    → validate("BAD") → None
    → No provider call
```
