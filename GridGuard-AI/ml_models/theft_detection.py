import numpy as np
from sklearn.ensemble import IsolationForest

def analyze_readings(rows):
    """Unsupervised anomaly screening; a flag is not proof of electricity theft."""
    if len(rows) < 8:
        return []
    values = np.array([float(r["units"]) for r in rows]).reshape(-1,1)
    model = IsolationForest(contamination=0.06, random_state=42)
    labels = model.fit_predict(values)
    scores = model.decision_function(values)
    results = []
    for row, label, score in zip(rows, labels, scores):
        if label == -1:
            risk = round(float(max(0, min(100, (0.15-score)*250))), 1)
            results.append({
              "meter_code": row["meter_code"], "date": row["reading_date"],
              "units": float(row["units"]), "score": risk,
              "reason": "Consumption differs substantially from the dataset pattern"
            })
    return sorted(results, key=lambda x:x["score"], reverse=True)
