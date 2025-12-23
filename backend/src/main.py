import os
import sys
import logging
from flask import Flask
from flask_cors import CORS
from sqlalchemy import text

# Make sure src/ is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Database + models
from src.models.user import db

# Blueprints (routes)
from src.routes.user import user_bp
from src.routes.auth import auth_bp
from src.routes.analytics import analytics_bp
from src.routes.alerts import alerts_bp
from src.routes.settings import settings_bp
from src.routes.keystroke import keystroke_bp
from src.routes.monitoring import monitoring_bp
from src.routes.dataset import dataset_bp
from src.routes.ml_training import ml_bp


# -------------------------------------------------------
#                 FLASK APP SETUP
# -------------------------------------------------------
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

app.config['SECRET_KEY'] = "bioauthai-secure-key-2024"

# =======================================================
#                  DATABASE CONFIG
# =======================================================

# Get the absolute path to the backend directory
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_DIR = os.path.join(BACKEND_DIR, "database")
os.makedirs(DB_DIR, exist_ok=True)

DB_PATH = os.path.join(DB_DIR, "app.db")
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_PATH}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

# -------------------------------------------------------
#        ENABLE WAL MODE (FASTER + FEWER LOCKS)
# -------------------------------------------------------
def enable_wal():
    try:
        with db.engine.connect() as conn:
            current = conn.execute(text("PRAGMA journal_mode;")).scalar()

            if str(current).lower() != "wal":
                conn.execute(text("PRAGMA journal_mode=WAL;"))
                conn.execute(text("PRAGMA busy_timeout=5000;"))
                print("WAL Mode Enabled")
            else:
                print("WAL Mode Already Active")

    except Exception as e:
        print("WAL FAILED:", e)


with app.app_context():
    enable_wal()
    db.create_all()


# -------------------------------------------------------
#                 REGISTER BLUEPRINTS
# -------------------------------------------------------
CORS(app, origins=["*"])

app.register_blueprint(user_bp,       url_prefix="/api")
app.register_blueprint(auth_bp,       url_prefix="/api")
app.register_blueprint(analytics_bp,  url_prefix="/api")
app.register_blueprint(alerts_bp,     url_prefix="/api")
app.register_blueprint(settings_bp,   url_prefix="/api")
app.register_blueprint(keystroke_bp,  url_prefix="/api")
app.register_blueprint(monitoring_bp, url_prefix="/api")
app.register_blueprint(dataset_bp,    url_prefix="/api")
app.register_blueprint(ml_bp,         url_prefix="/api")


# -------------------------------------------------------
#     ROOT ENDPOINT (API INFO)
# -------------------------------------------------------
@app.route("/")
def root():
    return {
        "service": "BioAuthAI Backend API",
        "version": "3.0",
        "status": "running",
        "message": "Backend API is running. Frontend should be served separately on port 5173.",
        "endpoints": {
            "health": "/api/health",
            "auth": "/api/auth/*",
            "users": "/api/users/*",
            "ml_training": "/api/ml/*",
            "analytics": "/api/analytics/*",
            "alerts": "/api/alerts/*",
            "monitoring": "/api/monitoring/*",
            "dataset": "/api/dataset/*",
            "keystroke": "/api/keystroke/*",
            "settings": "/api/settings/*"
        }
    }, 200


# -------------------------------------------------------
#                   HEALTH CHECK
# -------------------------------------------------------
@app.route("/api/health")
def health():
    return {
        "status": "OK",
        "service": "BioAuthAI Backend",
        "version": "3.0"
    }, 200


# -------------------------------------------------------
#                     START SERVER
# -------------------------------------------------------
if __name__ == "__main__":
    print("\n==============================")
    print(">>> USING DATABASE PATH:", DB_PATH)
    print(">>> EXISTS:", os.path.exists(DB_PATH))
    print("==============================")
    print("BioAuthAI Backend Running at http://localhost:5001\n")

    app.run(host="0.0.0.0", port=5001, debug=False)
