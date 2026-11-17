import numpy as np
from sklearn.ensemble import RandomForestRegressor

def forecast_daily(rows, days=7):
    """Forecast total daily usage from lagged daily aggregates."""
    totals={}
    for r in rows:
        totals[r["reading_date"]]=totals.get(r["reading_date"],0)+float(r["units"])
    dates=sorted(totals)
    values=[totals[d] for d in dates]
    if len(values)<5:
        return []
    X=[]; y=[]
    for i in range(3,len(values)):
        X.append([values[i-1],values[i-2],values[i-3],i%7])
        y.append(values[i])
    model=RandomForestRegressor(n_estimators=120,random_state=42)
    model.fit(X,y)
    history=values[:]
    output=[]
    from datetime import datetime,timedelta
    last=datetime.strptime(dates[-1],"%Y-%m-%d")
    for n in range(1,days+1):
        idx=len(history)
        pred=max(0,float(model.predict([[history[-1],history[-2],history[-3],idx%7]])[0]))
        history.append(pred)
        output.append({"date":(last+timedelta(days=n)).strftime("%Y-%m-%d"),"units":round(pred,2)})
    return output
