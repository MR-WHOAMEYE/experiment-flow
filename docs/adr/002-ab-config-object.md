# ADR-002 — A/B Testing Engine Accepts a Config Object (Not Hardcoded Per-Experiment)

**Date:** 2026-08-13
**Status:** Accepted — Non-negotiable (per prompt.md §3)
**Story:** US-4.1, US-4.2

---

## Context

The A/B Testing Engine must be reusable across arbitrary datasets and experiments. Without this property, the system is a one-off script, not a service.

## Decision

The engine takes a single config object:

```python
@dataclass
class ExperimentConfig:
    dataset_id: str
    name: str
    variant_column: str       # column containing group labels (e.g. "A", "B")
    metric_column: str        # column to measure (e.g. "revenue", "clicked")
    metric_type: str          # "numeric" | "categorical"
```

The statistical test is selected automatically based on `metric_type`:
- `numeric` → independent samples t-test (`scipy.stats.ttest_ind`)
- `categorical` → chi-square test of independence (`scipy.stats.chi2_contingency`)

The config is validated against the actual `clean_records` schema before being queued.

## Alternatives Considered

| Alternative | Reason Rejected |
|-------------|-----------------|
| Hard-coded functions per dataset/experiment | Violates the "service" requirement; untestable in a general way |
| Passing raw SQL to the engine | Security risk (SQL injection); makes the engine impossible to unit-test without a live DB |
| ML-based test selection | Overkill for capstone; t-test/chi-square are the academically correct defaults |

## Consequences

- **Positive:** Engine is fully reusable — same code runs any experiment on any dataset.
- **Positive:** Validates config before execution; catches column mismatches early.
- **Positive:** Easily testable with synthetic data.
- **Negative:** Users must know which columns to choose — mitigated by the UI form (US-4.1) and auto-inference of `metric_type`.
