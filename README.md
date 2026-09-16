# KATSU - AI Phone Performance Enactor (iQOO 13 Edition)

> An AI-powered predictive performance intelligence layer for modern smartphones, calibrated for the **iQOO 13 (Snapdragon® 8 Elite)**.

---

## Overview

Modern gaming smartphones provide elite hardware, but users often don't know whether their phone can sustain a demanding game given its current thermal, memory, and battery state.

**NEXUS** transforms raw telemetry into predictive, actionable intelligence across three phases:
1. **Pre-install Predictor**: Models application workload against live hardware conditions to forecast frame rates, thermal throttling probability, and memory pressure before launching.
2. **Live Gaming Mode**: Real-time streaming telemetry, rolling FPS graphs, 1% low metrics, and one-tap "Optimize For Me" background cleanup.
3. **Post-Usage Degradation Tracking**: 30-day battery health retention curve, per-title thermal exposure breakdown, and weekly AI wear-prevention digests.

---

## Key Features

- **Strict iQOO 13 Mobile Dimensions**: Formatted in authentic mobile phone proportions ($396\text{px} \times 820\text{px}$, $19.8:9$ aspect ratio), complete with front punch-hole camera, Android status bar, dynamic `MONSTER MODE` pill, and gesture home indicator.
- **Slide Options for Extended Content**: All content longer than the screen height is partitioned into 1-tap slide selectors (`Slide 1` $\leftrightarrow$ `Slide 2`), eliminating endless page-level vertical scrolling.
- **Persistent Bottom Navigation Dock**: 4-item dock (`OVERVIEW`, `PREDICT`, `SESSION`, `WEAR`) mirroring Vivo/iQOO OriginOS.
- **Explainable AI Layer ("Why This Result?")**: Shows feature importance breakdowns from the underlying scikit-learn model:
  - Snapdragon® 8 Elite (Adreno 830) GPU tier ($+38.5\%$)
  - Device thermal headroom ($-26.0\%$ to $-34.0\%$)
  - RAM memory margin ($-18.0\%$ to $-24.5\%$)
  - Background process contention ($-16.0\%$)
- **Custom Game & APK Analyzer**: Test any unlisted game or custom workload by specifying RAM requirement and GPU intensity.
- **Dual-Mode ML Inference**: Automatically queries the FastAPI backend when online, and seamlessly falls back to on-device ML inference if offline.
- **Audio AI Briefing**: Native speech synthesis readout via the Web Speech API.

---

## Machine Learning Pipeline (`ml/`)

Trained on 4,000 synthetic telemetry samples calibrated against modern flagship device thermal throttling and memory behavior:

- **Performance Score Model**: `GradientBoostingRegressor` ($R^2 = 0.9629$, $\text{MSE} = 12.18$)
- **FPS Prediction Model**: `GradientBoostingRegressor` ($R^2 = 0.9930$)
- **Thermal Risk Classifier**: `RandomForestClassifier` ($88.4\%$ accuracy)
- **Battery Impact Classifier**: `RandomForestClassifier` ($87.3\%$ accuracy)

Model artifacts:
- `ml/models/performance_model.joblib`
- `ml/models/model_weights.json`
- `ml/data/telemetry_benchmark_data.csv`

---

## Quickstart

### 1. Run the Python Backend
```bash
# Install dependencies
pip install -r backend/requirements.txt

# Start FastAPI server
uvicorn backend.main:app --host 127.0.0.1 --port 8000
```
- API Docs: `http://127.0.0.1:8000/docs`
- Health Check: `http://127.0.0.1:8000/health`

### 2. Run the Web Application
```bash
# In the project root, start any static web server:
python -m http.server 3000
```
Open `http://localhost:3000` in your browser.

---

## Repository Structure

```
.
├── backend/
│   ├── main.py              # FastAPI endpoints (/health, /predict, /history, /games)
│   └── requirements.txt     # Backend dependencies
├── ml/
│   ├── train.py             # Dataset generator and scikit-learn training pipeline
│   ├── requirements.txt     # ML dependencies
│   ├── data/                # Generated telemetry benchmark data
│   └── models/              # Trained joblib bundle and model weights JSON
├── index.html               # iQOO 13 phone dimension shell & multi-slide views
├── styles.css               # Authentic iQOO dark glassmorphism & phone styling
├── app.js                   # Client engine, ML fallback, charts, and navigation
├── .gitignore
└── README.md
```
