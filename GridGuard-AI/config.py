import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "change-this-development-secret")
    DATABASE = os.path.join(BASE_DIR, "database", "gridguard.db")
    SAMPLE_CONSUMPTION = os.path.join(BASE_DIR, "data", "sample_consumption.csv")
    SAMPLE_OUTAGES = os.path.join(BASE_DIR, "data", "sample_outages.csv")
