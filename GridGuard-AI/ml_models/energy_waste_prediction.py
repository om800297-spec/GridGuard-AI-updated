from collections import defaultdict
from statistics import mean, median


def predict_energy_waste(rows):
    """Estimate potential excess use against each meter's own recent baseline."""
    by_meter = defaultdict(list)
    for row in rows:
        meter = row["meter_code"]
        units = float(row["units"])
        date = str(row["reading_date"])
        by_meter[meter].append((date, max(0.0, units)))

    results = []
    for meter, readings in by_meter.items():
        readings.sort(key=lambda x: x[0])
        values = [x[1] for x in readings]
        if len(values) < 14:
            continue
        recent = values[-7:]
        history = values[-28:-7]
        baseline = median(history) if history else median(values[:-7])
        recent_avg = mean(recent)
        if baseline <= 0:
            continue
        excess = max(0.0, recent_avg - baseline)
        pct = (excess / baseline) * 100
        if pct < 10:
            continue
        level = "High" if pct >= 35 else ("Medium" if pct >= 20 else "Low")
        results.append({
            "meter_code": meter,
            "recent_daily_avg": round(recent_avg, 2),
            "baseline_daily_avg": round(baseline, 2),
            "extra_daily_kwh": round(excess, 2),
            "projected_extra_week_kwh": round(excess * 7, 2),
            "increase_percent": round(pct, 1),
            "level": level,
            "basis": "Last 7 days compared with this meter's preceding 21-day median."
        })
    results.sort(key=lambda x: x["projected_extra_week_kwh"], reverse=True)
    return {
        "count": len(results),
        "projected_extra_week_kwh": round(sum(x["projected_extra_week_kwh"] for x in results), 2),
        "findings": results[:50],
        "note": "Potential excess-use indicators only. Higher usage may be legitimate due to weather, occupancy or changed operating hours; verify before calling it waste."
    }
