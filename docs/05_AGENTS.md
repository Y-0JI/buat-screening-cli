# AGENTS.md

## Project Rules

-   Keep modules independent.
-   No business logic inside CLI.
-   Indicator calculations belong to Indicator Engine.
-   AI never calculates indicators.
-   Use Yahoo Finance through tool abstraction.
-   Environment variables only from .env.
-   Prefer readable code over clever code.
-   Every feature must include tests.
-   Update documentation with each feature.
-   Keep architecture provider agnostic.

## Architecture Authority

The project documentation is the single source of truth.

Do not simplify, redesign, or remove architectural components because they appear unnecessary for the current MVP.

If an implementation conflicts with the documented architecture, follow the documentation unless explicitly instructed otherwise.

If you believe the documentation should change, propose the change first instead of implementing it directly.
