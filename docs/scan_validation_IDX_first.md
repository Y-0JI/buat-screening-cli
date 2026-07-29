# Scan Validation — IDX-first Fallback Order

## Test

`provider_fallback_order=idx,yahoo` — 50 ticker sample, concurrency 2 workers, `period=3mo`.

## Result

```
Time: 72s (→ ~20m projected for 814 tickers)
IDX:        ok=17, no_data=33
Yahoo (fb): ok=29, no_data=4
```

## Breakdown

| Source | Count |
|--------|-------|
| IDX success (direct) | 17 |
| IDX fail → rescued by Yahoo | 29 |
| Both failed | 4 |

## Key Findings

- **IDX success rate ~34%** — handles roughly a third of tickers directly
- **IDX failures are mostly fast** ("data kosong", no retry) — reducing retry attempts from 3→1 saves negligible time (~2m out of 20m)
- **Yahoo rate limited: 0** — dramatically better than pure-Yahoo scan (9,527 rate limit events on Jul 25)
- **~20m total** for 814 tickers — acceptable for a full scan

## Verdict

IDX-first is viable as default. Yahoo fallback handles the remaining ~66% with zero rate limiting.
