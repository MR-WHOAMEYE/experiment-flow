# TASK.md — Active Stories: US-5.1 & US-5.2

**Stories:** US-5.1 (ML Training) & US-5.2 (Auto-Retraining)
**Sprint:** 5 | **Status:** ✅ Complete

---

## Task Breakdown

### US-5.1 — ML Training (8 pts)
- [x] `ml/trainer.py` — `train_model()` for RandomForest Regression & Classification, RMSE/R2 & Accuracy/F1 metrics, `joblib` artifact saving
- [x] `ml/predictor.py` — `predict()` feature alignment & inference
- [x] `tests/test_ml_trainer.py` (4 tests)

### US-5.2 — Auto-Retraining (5 pts)
- [x] `ml/retrainer.py` — `auto_retrain_if_needed()` row count check & metadata update in `predictions` table
- [x] `tests/test_ml_retrainer.py` (2 tests)
