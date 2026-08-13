# SPRINT.md — Current Sprint

> **Rule:** Wipe and rewrite this file at the start of each new sprint. History lives in RETRO.md.

---

## Sprint 4 — A/B Testing Engine ✅ COMPLETE

| Field | Value |
|-------|-------|
| **Sprint Goal** | Users can configure and execute statistically valid A/B experiments (t-test / chi-square) with p-value, effect size, and confidence intervals stored in DB. |
| **Start Date** | 2026-08-13 |
| **End Date** | 2026-08-13 |
| **Total Points** | 13 |
| **Git Tag** | `v0.4.0-sprint4` |

---

## Stories

| Story | Title | Points | Status |
|-------|-------|--------|--------|
| US-4.1 | Define experiment config (no-code) | 8 | ✅ Done |
| US-4.2 | Compute statistically valid results | 5 | ✅ Done |

---

## Story Checklist

### US-4.1 — Experiment Config
- [x] `ab_testing/config.py` — `ExperimentConfig` dataclass and schema validator (`ConfigValidationError`)
- [x] `tests/test_ab_config.py` — 5 unit tests for config creation & schema validation

### US-4.2 — Statistical Engine
- [x] `ab_testing/engine.py` — `evaluate_experiment()`: Welch's t-test (`scipy.stats.ttest_ind`), Chi-square (`scipy.stats.chi2_contingency`), Cohen's d, Cramér's V, 95% CI
- [x] `save_experiment_result()` — DB persistence into `experiments` table
- [x] `tests/test_ab_engine.py` — 3 unit tests for numeric/categorical A/B tests & DB persistence
- [x] 58/58 total tests PASSED | overall coverage: 92%

---

## Sign-off
- [x] 58/58 tests pass — `pytest`
- [x] Coverage: `ab_testing/` **98%** (threshold: 70%)
- [x] Gherkin ACs verified (ADR-002 compliant)
- [x] BACKLOG.md: US-4.1, US-4.2 → Done
- [x] TRACK.md entry appended
- [x] RETRO.md Sprint 4 entry written
- [x] Tag: `v0.4.0-sprint4`

_Sprint 4 closed. Next: Sprint 5 — ML Prediction Module (US-5.1, US-5.2, 13 pts)_
