# TASK.md — Active Stories: US-4.1 & US-4.2

**Stories:** US-4.1 (Experiment Config) & US-4.2 (A/B Testing Engine)
**Sprint:** 4 | **Status:** In Progress

---

## Gherkin ACs
```
Given a dataset in clean_records
When a user specifies variant_column, metric_column, and metric_type
Then an ExperimentConfig object is validated against the dataset schema

Given a valid ExperimentConfig and clean_records dataset
When the engine executes the experiment
Then it runs independent samples t-test (numeric) or chi-square test (categorical)
And calculates p-value, effect size, confidence interval, and statistical significance (p < 0.05)
And stores results in the experiments table
```

---

## Task Breakdown

### A — Tests first (TDD)
- [ ] `tests/test_ab_config.py`:
  - [ ] Valid config passes validation
  - [ ] Missing variant/metric column raises `ConfigValidationError`
  - [ ] Invalid metric_type raises `ConfigValidationError`
- [ ] `tests/test_ab_engine.py`:
  - [ ] Numeric metric -> Welch's t-test, Cohen's d, 95% CI, p-value, significant flag
  - [ ] Categorical metric -> Chi-square test, Cramér's V, p-value, significant flag
  - [ ] Experiment results saved to `experiments` table

### B — Implementation
- [ ] `ab_testing/config.py`: `ExperimentConfig` dataclass & `validate_config()`
- [ ] `ab_testing/engine.py`: `evaluate_experiment()` & `save_experiment_result()`

### C — Verify & close
- [ ] All tests pass (`pytest`)
- [ ] Coverage ≥ 70% on `ab_testing/`
- [ ] BACKLOG.md & SPRINT.md updated
