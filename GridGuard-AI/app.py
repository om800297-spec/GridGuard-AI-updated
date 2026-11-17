from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file
from werkzeug.security import check_password_hash
from functools import wraps
import pandas as pd, os, io
from config import Config
from database.database import connect, init_db
from ml_models.theft_detection import analyze_readings
from ml_models.outage_prediction import predict_area_risk
from ml_models.demand_forecasting import forecast_daily
from ml_models.energy_optimizer import recommendations
from ml_models.energy_waste_prediction import predict_energy_waste
from services.billing import estimate_bill

app=Flask(__name__)
app.config.from_object(Config)

def seed_data():
    con=connect()
    if con.execute("SELECT COUNT(*) FROM readings").fetchone()[0]==0:
        df=pd.read_csv(Config.SAMPLE_CONSUMPTION)
        con.executemany("INSERT INTO readings(meter_code,reading_date,units) VALUES(?,?,?)",
          [(r.meter_code,r.date,float(r.units)) for r in df.itertuples()])
    if con.execute("SELECT COUNT(*) FROM outages").fetchone()[0]==0:
        df=pd.read_csv(Config.SAMPLE_OUTAGES)
        con.executemany("INSERT INTO outages(area,outage_date,duration_hours,temperature,rainfall) VALUES(?,?,?,?,?)",
          [(r.area,r.date,float(r.duration_hours),float(r.temperature),float(r.rainfall)) for r in df.itertuples()])
    con.commit(); con.close()

def login_required(fn):
    @wraps(fn)
    def wrapper(*args,**kwargs):
        if not session.get("user_id"): return jsonify({"error":"Authentication required"}),401
        return fn(*args,**kwargs)
    return wrapper

def admin_required(fn):
    @wraps(fn)
    def wrapper(*args,**kwargs):
        if session.get("role")!="admin": return jsonify({"error":"Admin access required"}),403
        return fn(*args,**kwargs)
    return wrapper

@app.route("/")
def home():
    return render_template("index.html")

@app.post("/api/login")
def login():
    data=request.get_json(force=True)
    con=connect(); user=con.execute("SELECT * FROM users WHERE email=?",(data.get("email","").lower().strip(),)).fetchone(); con.close()
    if not user or not check_password_hash(user["password_hash"],data.get("password","")):
        return jsonify({"error":"Invalid email or password"}),401
    session.update(user_id=user["id"],name=user["name"],role=user["role"],area=user["area"])
    return jsonify({"name":user["name"],"role":user["role"],"area":user["area"]})

@app.post("/api/logout")
def logout():
    session.clear(); return jsonify({"ok":True})

@app.get("/api/me")
def me():
    if not session.get("user_id"): return jsonify({"logged_in":False})
    return jsonify({"logged_in":True,"name":session["name"],"role":session["role"],"area":session["area"]})

@app.get("/api/dashboard")
@login_required
def dashboard():
    con=connect()
    total=con.execute("SELECT COUNT(DISTINCT meter_code) FROM readings").fetchone()[0]
    agg=con.execute("SELECT COALESCE(SUM(units),0) total, COALESCE(AVG(units),0) avg FROM readings").fetchone()
    dates=con.execute("SELECT reading_date,SUM(units) units FROM readings GROUP BY reading_date ORDER BY reading_date").fetchall()
    alerts=con.execute("SELECT COUNT(*) FROM alerts WHERE status='Open'").fetchone()[0]
    areas=con.execute("SELECT area,COUNT(*) meters FROM meters GROUP BY area").fetchall()
    con.close()
    return jsonify({"meters":total,"total_units":round(agg["total"],1),"avg_reading":round(agg["avg"],2),
      "open_alerts":alerts,"daily":[dict(x) for x in dates[-14:]],"areas":[dict(x) for x in areas]})

@app.get("/api/meters")
@login_required
def meters():
    con=connect()
    rows=con.execute("""SELECT m.meter_code,m.customer_name,m.area,m.connection_type,
      ROUND(COALESCE(SUM(r.units),0),2) units FROM meters m LEFT JOIN readings r ON r.meter_code=m.meter_code
      GROUP BY m.meter_code ORDER BY m.meter_code LIMIT 150""").fetchall()
    con.close(); return jsonify([dict(r) for r in rows])

@app.get("/api/theft")
@login_required
def theft():
    con=connect()
    rows=con.execute("SELECT meter_code,reading_date,units FROM readings ORDER BY reading_date").fetchall()
    con.close()
    findings=analyze_readings(rows)
    return jsonify({"count":len(findings),"findings":findings[:30],
      "disclaimer":"Anomaly flags are screening indicators only, not proof of electricity theft."})

@app.get("/api/outages")
@login_required
def outages():
    con=connect(); rows=con.execute("SELECT area,outage_date,duration_hours,temperature,rainfall FROM outages").fetchall(); con.close()
    return jsonify(predict_area_risk(rows))

@app.get("/api/forecast")
@login_required
def forecast():
    con=connect(); rows=con.execute("SELECT reading_date,meter_code,units FROM readings ORDER BY reading_date").fetchall(); con.close()
    result=forecast_daily(rows,7)
    return jsonify({"forecast":result,"note":"Forecasts are estimates based on the included sample history."})

@app.get("/api/bill")
@login_required
def bill():
    units=float(request.args.get("units", "150"))
    rate=float(request.args.get("rate","6.5"))
    return jsonify(estimate_bill(units,rate))

@app.get("/api/energy-waste")
@login_required
def energy_waste():
    con=connect()
    rows=con.execute("SELECT meter_code,reading_date,units FROM readings ORDER BY reading_date").fetchall()
    con.close()
    return jsonify(predict_energy_waste(rows))

@app.get("/api/recommendations")
@login_required
def recs():
    con=connect()
    dates=con.execute("SELECT reading_date,SUM(units) units FROM readings GROUP BY reading_date ORDER BY reading_date DESC LIMIT 60").fetchall()
    con.close()
    current=sum(float(r["units"]) for r in dates[:30]); previous=sum(float(r["units"]) for r in dates[30:])
    bill=estimate_bill(current)["total"]
    return jsonify(recommendations(current,previous,bill))

@app.get("/api/alerts")
@login_required
def get_alerts():
    con=connect(); rows=con.execute("SELECT * FROM alerts ORDER BY id DESC LIMIT 50").fetchall(); con.close()
    return jsonify([dict(r) for r in rows])

@app.post("/api/alerts/scan")
@login_required
@admin_required
def scan_alerts():
    con=connect()
    rows=con.execute("SELECT meter_code,reading_date,units FROM readings ORDER BY reading_date").fetchall()
    findings=analyze_readings(rows)
    con.execute("DELETE FROM alerts WHERE alert_type='Anomaly scan'")
    for f in findings:
        con.execute("INSERT INTO alerts(meter_code,alert_type,severity,message,score) VALUES(?,?,?,?,?)",
          (f["meter_code"],"Anomaly scan","High" if f["score"]>=70 else "Medium",
           f'Unusual reading of {f["units"]} units on {f["date"]}. Verify meter and site records.',f["score"]))
    con.commit(); con.close()
    return jsonify({"created":len(findings)})

@app.post("/api/alerts/<int:alert_id>/resolve")
@login_required
@admin_required
def resolve_alert(alert_id):
    con=connect(); con.execute("UPDATE alerts SET status='Reviewed' WHERE id=?",(alert_id,)); con.commit(); con.close()
    return jsonify({"ok":True})

@app.post("/api/complaints")
@login_required
def complaint():
    data=request.get_json(force=True)
    if not data.get("subject") or not data.get("description"): return jsonify({"error":"Subject and description are required"}),400
    con=connect(); con.execute("INSERT INTO complaints(user_id,subject,description) VALUES(?,?,?)",
      (session["user_id"],data["subject"][:120],data["description"][:2000])); con.commit(); con.close()
    return jsonify({"ok":True})

@app.get("/api/complaints")
@login_required
def complaints():
    con=connect()
    if session["role"]=="admin":
        rows=con.execute("SELECT c.*,u.name FROM complaints c LEFT JOIN users u ON u.id=c.user_id ORDER BY c.id DESC").fetchall()
    else:
        rows=con.execute("SELECT * FROM complaints WHERE user_id=? ORDER BY id DESC",(session["user_id"],)).fetchall()
    con.close(); return jsonify([dict(r) for r in rows])

@app.get("/api/report")
@login_required
def report():
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
    except ImportError: return jsonify({"error":"Install reportlab to generate PDF reports"}),500
    buffer=io.BytesIO(); pdf=canvas.Canvas(buffer,pagesize=A4)
    pdf.setTitle("GridGuard AI Report")
    pdf.setFont("Helvetica-Bold",20); pdf.drawString(50,790,"GridGuard AI - Electricity Intelligence Report")
    pdf.setFont("Helvetica",10); pdf.drawString(50,768,"Generated report | Sample/demo analytics")
    con=connect()
    meters=con.execute("SELECT COUNT(*) FROM meters").fetchone()[0]
    units=con.execute("SELECT COALESCE(SUM(units),0) FROM readings").fetchone()[0]
    alert_count=con.execute("SELECT COUNT(*) FROM alerts WHERE status='Open'").fetchone()[0]
    pdf.drawString(50,725,f"Registered sample meters: {meters}")
    pdf.drawString(50,705,f"Total recorded consumption: {units:.1f} kWh")
    pdf.drawString(50,685,f"Open review alerts: {alert_count}")
    pdf.drawString(50,650,"Note: ML outputs are estimates and require human verification.")
    con.close(); pdf.save(); buffer.seek(0)
    return send_file(buffer,as_attachment=True,download_name="GridGuard_AI_Report.pdf",mimetype="application/pdf")

if __name__=="__main__":
    os.makedirs(os.path.dirname(Config.DATABASE),exist_ok=True)
    init_db()
    if os.path.exists(Config.SAMPLE_CONSUMPTION): seed_data()
    app.run(debug=True)
