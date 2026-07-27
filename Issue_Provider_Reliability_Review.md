# Issue: Improve Provider Reliability & Error Handling

## Objective

Improve the reliability and user experience of the provider layer by
ensuring consistent provider behavior, accurate error reporting, and
cleaner runtime output.

------------------------------------------------------------------------

## Scope

-   Ensure all providers expose a consistent public interface.
-   Verify that provider fallback executes correctly without runtime
    incompatibilities.
-   Improve error classification so temporary provider failures are not
    be reported as invalid or delisted symbols.
-   Reduce unnecessary runtime logging while preserving useful
    diagnostic information.
-   Ensure fallback, cache, and retry mechanisms work together as
    intended.
-   Preserve backward compatibility with the existing screening
    workflow.

------------------------------------------------------------------------

## Expected Outcome

-   Provider fallback operates correctly across all supported providers.
-   Temporary provider failures no longer produce misleading user
    messages.
-   Runtime logs become concise and focused on important events.
-   Screening continues to operate reliably even when individual
    providers fail.
-   Existing CLI behavior remains unchanged from the user's perspective.

------------------------------------------------------------------------

## Acceptance Criteria

-   All configured providers can participate in the fallback chain
    without interface conflicts.
-   Runtime errors caused by provider incompatibilities are eliminated.
-   User-facing messages accurately describe the actual failure
    condition.
-   Logging output is appropriate for normal CLI usage while still
    supporting debugging when needed.
-   Existing tests continue to pass, and new behavior is covered by
    appropriate tests.

------------------------------------------------------------------------

# Issue: Review Provider Integration After Phase 1

## Objective

Review the current provider integration after the Phase 1 implementation
and identify opportunities to simplify or improve the provider
architecture.

------------------------------------------------------------------------

## Scope

-   Evaluate the reliability of each provider during real-world
    screening.
-   Verify that each provider contributes meaningful value to the
    fallback strategy.
-   Identify redundant provider-specific logic.
-   Assess whether the current provider configuration remains
    appropriate for future roadmap phases.

------------------------------------------------------------------------

## Expected Outcome

-   A clear understanding of provider reliability and usefulness.
-   Documented recommendations for future provider improvements.
-   A cleaner foundation for the next roadmap phases.

------------------------------------------------------------------------

## Non-Goals

-   Do not introduce new providers.
-   Do not redesign the symbol discovery architecture.
-   Do not expand into Phase 2 or later roadmap work.
