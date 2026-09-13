"""
AI Phone Performance Enactor - Machine Learning Pipeline
Trains predictive models for smartphone gaming performance, thermal risk, and battery wear.
"""

import json
import os
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor, RandomForestClassifier
from sklearn.metrics import classification_report, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split


def generate_synthetic_telemetry(n_samples: int = 4000, random_state: int = 42) -> pd.DataFrame:
    """
    Generates a realistic smartphone performance dataset combining device telemetry
    and game workload requirements, calibrated for modern gaming phones like iQOO 13.
    """
    np.random.seed(random_state)

    # Device specifications & current states
    # RAM capacity in GB: 8, 12, 16
    ram_gb = np.random.choice([8.0, 12.0, 16.0], size=n_samples, p=[0.25, 0.55, 0.20])
    # RAM used percentage: 30% to 88%
    ram_used_pct = np.random.uniform(32.0, 88.0, size=n_samples)
    # Available RAM in GB
    ram_avail_gb = ram_gb * (1.0 - ram_used_pct / 100.0)
    # Storage used percentage: 20% to 94%
    storage_used_pct = np.random.uniform(25.0, 94.0, size=n_samples)
    # Current battery percentage: 10% to 100%
    battery_pct = np.random.uniform(12.0, 100.0, size=n_samples)
    # Current device temperature: 28°C to 45°C
    temp_c = np.random.uniform(28.0, 44.5, size=n_samples)
    # Ambient thermal factor / cooling capability (iQOO VC cooling efficiency index: 1.0 to 1.3)
    cooling_efficiency = np.random.uniform(1.0, 1.35, size=n_samples)

    # Game application profile
    # Game RAM demand: 1.5 to 6.5 GB
    app_ram_gb = np.random.uniform(1.8, 6.2, size=n_samples)
    # Game Storage demand: 2 to 32 GB
    app_storage_gb = np.random.uniform(2.0, 30.0, size=n_samples)
    # App GPU intensity: 0.2 (light arcade) to 1.0 (Genshin / Wuthering Waves maximum settings)
    app_gpu_intensity = np.random.uniform(0.25, 0.98, size=n_samples)
    # App CPU intensity: 0.2 to 0.95
    app_cpu_intensity = np.random.uniform(0.20, 0.92, size=n_samples)
    # Target frame rate: 60, 90, 120
    target_fps = np.random.choice([60.0, 90.0, 120.0], size=n_samples, p=[0.5, 0.35, 0.15])

    # Realistic Physical / Heuristic Modeling for Target Variables
    # 1. Memory Headroom Margin
    ram_margin_gb = ram_avail_gb - app_ram_gb

    # 2. Thermal Headroom
    # Throttling threshold for Snapdragon 8 Elite is around 42.0°C; severe throttling at 45.0°C
    thermal_stress = (
        (temp_c - 30.0) * 1.5
        + (app_gpu_intensity * 18.0 + app_cpu_intensity * 10.0) / cooling_efficiency
    )

    # 3. Performance Score (0 - 100)
    base_score = 95.0
    # Penalty for RAM pressure
    ram_penalty = np.where(ram_margin_gb < 0, np.abs(ram_margin_gb) * 16.0, np.where(ram_margin_gb < 1.2, (1.2 - ram_margin_gb) * 7.0, 0.0))
    # Penalty for high temperature & throttling
    temp_penalty = np.where(temp_c > 41.0, (temp_c - 41.0) * 8.0, np.where(temp_c > 38.0, (temp_c - 38.0) * 3.5, 0.0))
    # Penalty for low battery throttling (Android power saver kicks in < 20%)
    battery_penalty = np.where(battery_pct < 20.0, (20.0 - battery_pct) * 0.8, 0.0)
    # Penalty for excessive storage pressure (> 88% causes slower swap and I/O wait)
    storage_penalty = np.where(storage_used_pct > 85.0, (storage_used_pct - 85.0) * 0.6, 0.0)
    # Workload intensity scaling
    workload_penalty = (app_gpu_intensity * 0.6 + app_cpu_intensity * 0.4) * 14.0

    raw_score = base_score - (ram_penalty + temp_penalty + battery_penalty + storage_penalty + workload_penalty)
    noise = np.random.normal(0, 2.2, size=n_samples)
    performance_score = np.clip(np.round(raw_score + noise, 1), 18.0, 99.0)

    # 4. Predicted Achievable FPS
    fps_ratio = performance_score / 100.0
    predicted_fps = np.round(np.clip(target_fps * (0.55 + 0.45 * fps_ratio) - np.maximum(0, (temp_c - 40.0) * 1.8), 22.0, target_fps))

    # 5. Thermal Risk (LOW, MEDIUM, HIGH)
    thermal_risk = []
    for t, stress in zip(temp_c, thermal_stress):
        if t >= 41.5 or stress > 28.0:
            thermal_risk.append("HIGH")
        elif t >= 37.5 or stress > 18.0:
            thermal_risk.append("MEDIUM")
        else:
            thermal_risk.append("LOW")

    # 6. Battery Drain Impact (LOW, MEDIUM, HIGH)
    battery_impact = []
    drain_factor = app_gpu_intensity * 1.5 + app_cpu_intensity * 0.9 + (100.0 - battery_pct) * 0.015
    for df in drain_factor:
        if df > 1.95:
            battery_impact.append("HIGH")
        elif df > 1.30:
            battery_impact.append("MEDIUM")
        else:
            battery_impact.append("LOW")

    df = pd.DataFrame({
        "ram_gb": ram_gb,
        "ram_used_percent": np.round(ram_used_pct, 1),
        "storage_used_percent": np.round(storage_used_pct, 1),
        "temperature_c": np.round(temp_c, 1),
        "battery_percent": np.round(battery_pct, 1),
        "app_ram_gb": np.round(app_ram_gb, 1),
        "app_storage_gb": np.round(app_storage_gb, 1),
        "app_gpu_intensity": np.round(app_gpu_intensity, 2),
        "app_cpu_intensity": np.round(app_cpu_intensity, 2),
        "target_fps": target_fps,
        "performance_score": performance_score,
        "predicted_fps": predicted_fps,
        "thermal_risk": thermal_risk,
        "battery_impact": battery_impact,
    })
    return df


def train_models():
    print("[*] Generating smartphone telemetry dataset (4000 samples)...")
    df = generate_synthetic_telemetry(n_samples=4000)

    # Save dataset to ml/data
    data_dir = Path("ml/data")
    data_dir.mkdir(parents=True, exist_ok=True)
    csv_path = data_dir / "telemetry_benchmark_data.csv"
    df.to_csv(csv_path, index=False)
    print(f"[+] Dataset saved to {csv_path}")

    feature_cols = [
        "ram_gb",
        "ram_used_percent",
        "storage_used_percent",
        "temperature_c",
        "battery_percent",
        "app_ram_gb",
        "app_storage_gb",
        "app_gpu_intensity",
        "app_cpu_intensity",
        "target_fps",
    ]

    X = df[feature_cols]
    y_score = df["performance_score"]
    y_fps = df["predicted_fps"]
    y_thermal = df["thermal_risk"]
    y_battery = df["battery_impact"]

    X_train, X_test, y_score_train, y_score_test = train_test_split(X, y_score, test_size=0.2, random_state=42)
    _, _, y_fps_train, y_fps_test = train_test_split(X, y_fps, test_size=0.2, random_state=42)
    _, _, y_thermal_train, y_thermal_test = train_test_split(X, y_thermal, test_size=0.2, random_state=42)
    _, _, y_battery_train, y_battery_test = train_test_split(X, y_battery, test_size=0.2, random_state=42)

    # 1. Regressor for Performance Score
    print("[*] Training GradientBoostingRegressor for Performance Score...")
    score_model = GradientBoostingRegressor(n_estimators=120, max_depth=4, learning_rate=0.08, random_state=42)
    score_model.fit(X_train, y_score_train)
    y_score_pred = score_model.predict(X_test)
    score_r2 = r2_score(y_score_test, y_score_pred)
    score_mse = mean_squared_error(y_score_test, y_score_pred)
    print(f"    Performance Score Model -> R²: {score_r2:.4f}, MSE: {score_mse:.4f}")

    # 2. Regressor for Predicted FPS
    print("[*] Training GradientBoostingRegressor for FPS...")
    fps_model = GradientBoostingRegressor(n_estimators=100, max_depth=4, learning_rate=0.1, random_state=42)
    fps_model.fit(X_train, y_fps_train)
    y_fps_pred = fps_model.predict(X_test)
    fps_r2 = r2_score(y_fps_test, y_fps_pred)
    print(f"    FPS Prediction Model -> R²: {fps_r2:.4f}")

    # 3. Classifier for Thermal Risk
    print("[*] Training RandomForestClassifier for Thermal Risk...")
    thermal_model = RandomForestClassifier(n_estimators=100, max_depth=6, random_state=42)
    thermal_model.fit(X_train, y_thermal_train)
    y_thermal_pred = thermal_model.predict(X_test)
    print("    Thermal Risk Classification Report:")
    print(classification_report(y_thermal_test, y_thermal_pred, digits=3))

    # 4. Classifier for Battery Impact
    print("[*] Training RandomForestClassifier for Battery Impact...")
    battery_model = RandomForestClassifier(n_estimators=100, max_depth=6, random_state=42)
    battery_model.fit(X_train, y_battery_train)
    y_battery_pred = battery_model.predict(X_test)
    print("    Battery Impact Classification Report:")
    print(classification_report(y_battery_test, y_battery_pred, digits=3))

    # Feature Importance for Explainability
    importances = dict(zip(feature_cols, [round(float(v), 4) for v in score_model.feature_importances_]))
    print(f"[+] Score Feature Importances: {importances}")

    # Save models
    models_dir = Path("ml/models")
    models_dir.mkdir(parents=True, exist_ok=True)

    bundle = {
        "score_model": score_model,
        "fps_model": fps_model,
        "thermal_model": thermal_model,
        "battery_model": battery_model,
        "feature_cols": feature_cols,
        "feature_importances": importances,
        "metrics": {
            "score_r2": round(score_r2, 4),
            "score_mse": round(score_mse, 4),
            "fps_r2": round(fps_r2, 4),
        }
    }
    model_path = models_dir / "performance_model.joblib"
    joblib.dump(bundle, model_path)
    print(f"[+] Saved model bundle to {model_path}")

    # Also export JSON configuration for client-side matching inference
    json_path = models_dir / "model_weights.json"
    with open(json_path, "w") as f:
        json.dump({
            "feature_cols": feature_cols,
            "feature_importances": importances,
            "metrics": bundle["metrics"],
            "model_version": "1.0.0-iqoo-snapdragon8elite"
        }, f, indent=2)
    print(f"[+] Saved model metadata to {json_path}")
    print("[OK] ML pipeline trained and exported successfully!")


if __name__ == "__main__":
    train_models()
