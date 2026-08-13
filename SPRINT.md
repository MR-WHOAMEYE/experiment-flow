# SPRINT.md — Current Sprint

> **Rule:** Wipe and rewrite this file at the start of each new sprint. History lives in RETRO.md.

---

## Sprint 5 — ML Prediction Module ✅ COMPLETE

| Field | Value |
|-------|-------|
| **Sprint Goal** | Users can train ML models (Regression / Classification) on user-selected target columns; models auto-retrain when new dataset rows arrive, saving artifacts to disk and metadata to `predictions`. |
| **Start Date** | 2026-08-13 |
| **End Date** | 2026-08-13 |
| **Total Points** | 13 |
| **Git Tag** | `v0.5.0-sprint5` |

---

## Stories

| Story | Title | Points | Status |
|-------|-------|--------|--------|
| US-5.1 | Train model on user-selected target column | 8 | ✅ Done |
| US-5.2 | Auto-retrain model when new data arrives | 5 | ✅ Done |

---

## Story Checklist

### US-5.1 — ML Model Training
- [x] `ml/trainer.py` — `train_model()`, model type detection (regression vs classification), feature preprocessing, metrics (RMSE/R2, Accuracy/F1), model serialization (`joblib`)
- [x] `ml/predictor.py` — `predict()` loads saved model artifact and computes predictions
- [x] `tests/test_ml_trainer.py` — 4 unit tests for training, metrics, saving, and predicting

### US-5.2 — Auto-Retraining Trigger
- [x] `ml/retrainer.py` — `auto_retrain_if_needed()` triggers retraining when dataset row count increases
- [x] `tests/test_ml_retrainer.py` — 2 unit tests for auto-retrain workflow & DB metadata update
- [x] 64/64 total tests PASSED | overall coverage: 93%

---

## Sign-off
- [x] 64/64 tests pass — `pytest`
- [x] Coverage: `ml/` **97%** (threshold: 70%)
- [x] Gherkin ACs verified
- [x] BACKLOG.md: US-5.1, US-5.2 → Done
- [x] TRACK.md entry appended
- [x] RETRO.md Sprint 5 entry written
- [x] Tag: `v0.5.0-sprint5`

_Sprint 5 closed. Next: Sprint 6 — Dashboard + n8n Automation (US-6.1, US-6.2, US-7.1, 13 pts)_
