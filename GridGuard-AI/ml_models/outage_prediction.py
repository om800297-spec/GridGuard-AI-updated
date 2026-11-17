import numpy as np
from sklearn.ensemble import RandomForestClassifier

def predict_area_risk(outage_rows):
    """Illustrative area risk model trained on historical outage records."""
    areas = sorted(set(r["area"] for r in outage_rows))
    if not areas:
        return []
    # Features are derived from historical outage frequency and average duration.
    X, y = [], []
    for r in outage_rows:
        X.append([float(r["temperature"]), float(r["rainfall"]), float(r["duration_hours"])])
        y.append(1 if float(r["duration_hours"]) >= 2 else 0)
    if len(set(y)) < 2 or len(X) < 10:
        return [{"area": a, "risk": 25, "level":"Low", "basis":"Insufficient historical examples"} for a in areas]
    model = RandomForestClassifier(n_estimators=100, random_state=42, class_weight="balanced")
    model.fit(np.asarray(X), np.asarray(y))
    results=[]
    for area in areas:
        subset=[r for r in outage_rows if r["area"]==area]
        temp=float(np.mean([float(r["temperature"]) for r in subset]))
        rain=float(np.mean([float(r["rainfall"]) for r in subset]))
        duration=float(np.mean([float(r["duration_hours"]) for r in subset]))
        risk=float(model.predict_proba([[temp,rain,duration]])[0][1]*100)
        results.append({"area":area,"risk":round(risk,1),"level":"High" if risk>=65 else "Medium" if risk>=35 else "Low",
                        "basis":"Historical outage and weather-pattern model"})
    return sorted(results,key=lambda x:x["risk"],reverse=True)
