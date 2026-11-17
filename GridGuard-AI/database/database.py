import sqlite3
from werkzeug.security import generate_password_hash
from config import Config

def connect():
    con = sqlite3.connect(Config.DATABASE)
    con.row_factory = sqlite3.Row
    return con

def init_db():
    con = connect()
    cur = con.cursor()
    cur.executescript("""
    CREATE TABLE IF NOT EXISTS users(
      id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL,
      email TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL,
      role TEXT NOT NULL DEFAULT 'user', area TEXT DEFAULT 'Bhopal'
    );
    CREATE TABLE IF NOT EXISTS meters(
      id INTEGER PRIMARY KEY AUTOINCREMENT, meter_code TEXT UNIQUE NOT NULL,
      customer_name TEXT NOT NULL, area TEXT NOT NULL, connection_type TEXT DEFAULT 'Residential'
    );
    CREATE TABLE IF NOT EXISTS readings(
      id INTEGER PRIMARY KEY AUTOINCREMENT, meter_code TEXT NOT NULL,
      reading_date TEXT NOT NULL, units REAL NOT NULL
    );
    CREATE TABLE IF NOT EXISTS alerts(
      id INTEGER PRIMARY KEY AUTOINCREMENT, meter_code TEXT NOT NULL,
      alert_type TEXT NOT NULL, severity TEXT NOT NULL, message TEXT NOT NULL,
      score REAL DEFAULT 0, status TEXT DEFAULT 'Open', created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS complaints(
      id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
      subject TEXT NOT NULL, description TEXT NOT NULL,
      status TEXT DEFAULT 'Submitted', created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS outages(
      id INTEGER PRIMARY KEY AUTOINCREMENT, area TEXT NOT NULL,
      outage_date TEXT NOT NULL, duration_hours REAL NOT NULL,
      temperature REAL DEFAULT 30, rainfall REAL DEFAULT 0
    );
    """)
    if cur.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
        cur.executemany("INSERT INTO users(name,email,password_hash,role,area) VALUES(?,?,?,?,?)", [
          ("GridGuard Admin","admin@gridguard.ai",generate_password_hash("Admin@123"),"admin","Bhopal"),
          ("Demo Consumer","user@gridguard.ai",generate_password_hash("User@123"),"user","Bhopal")
        ])
    if cur.execute("SELECT COUNT(*) FROM meters").fetchone()[0] == 0:
        meters = [
          (f"GG-{i:04d}", f"Customer {i:03d}", ["Bhopal Central","Arera Colony","Kolar","MP Nagar"][i%4],
           "Residential" if i%5 else "Commercial") for i in range(1,101)
        ]
        cur.executemany("INSERT INTO meters(meter_code,customer_name,area,connection_type) VALUES(?,?,?,?)", meters)
    con.commit()
    con.close()
