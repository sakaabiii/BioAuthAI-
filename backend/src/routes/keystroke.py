# ======================================================================
#  BioAuthAI — KEYSTROKE DATA ROUTES
# Authentication-Oriented Behavioral Biometrics
#
# Includes:
#   - GET /keystrokes
#   - POST /keystroke/capture
#   - POST /keystroke/analyze
#   - GET /keystroke/user-profile/<id>
#   - POST /keystroke/batch-process
#
# Uses 21-feature extractor from:
#   src/utils/feature_extractor.py
# ======================================================================

from flask import Blueprint, jsonify, request
from datetime import datetime
from src.models.user import db, User, KeystrokeData, MLModel
from src.utils.feature_extractor import extract_features
import numpy as np
import json
import pickle


keystroke_bp = Blueprint("keystroke", __name__)


# ======================================================================
#  1. GET ALL KEYSTROKES (Dashboard live feed)
# ======================================================================
@keystroke_bp.route("/keystrokes", methods=["GET"])
def get_all_keystrokes():
    """Return latest keystroke events for dashboard live streaming."""
    try:
        records = (
            KeystrokeData.query
            .order_by(KeystrokeData.timestamp.desc())
            .limit(50)
            .all()
        )

        output = []
        for r in records:
            try:
                feats = json.loads(r.keystroke_features or "{}")
            except:
                feats = {}

            try:
                dev = json.loads(r.device_info or "{}")
            except:
                dev = {}

            output.append({
                "id": r.id,
                "user_id": r.user_id,
                "session_id": r.session_id,
                "keystroke_features": feats,
                "device_info": dev,
                "timestamp": r.timestamp.isoformat() if r.timestamp else None,
                "is_training_data": r.is_training_data,
                "anomaly_score": float(r.anomaly_score) if r.anomaly_score is not None else None
            })

        return jsonify(output), 200

    except Exception as e:
        print("Error loading keystrokes:", e)
        return jsonify([]), 200




#  2. CAPTURE KEYSTROKE DATA

@keystroke_bp.route("/keystroke/capture", methods=["POST"])
def capture_keystroke_data():
    """Save keystroke sample + metadata into DB."""
    try:
        data = request.get_json()
        user_id = data.get("user_id")
        session_id = data.get("session_id")
        features = data.get("keystroke_features", {})
        device_info = data.get("device_info", {})
        is_training = data.get("is_training", True)

        if not user_id or not session_id:
            return jsonify({"error": "user_id and session_id required"}), 400

        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        ks = KeystrokeData(
            user_id=user_id,
            session_id=session_id,
            keystroke_features=json.dumps(features),
            device_info=json.dumps(device_info),
            is_training_data=is_training,
            anomaly_score=None
        )

        db.session.add(ks)
        db.session.commit()

        training_count = KeystrokeData.query.filter_by(
            user_id=user_id,
            is_training_data=True
        ).count()

        return jsonify({
            "message": "Keystroke saved",
            "data_id": ks.id,
            "training_samples": training_count
        }), 201

    except Exception as e:
        print("CAPTURE ERROR:", e)
        return jsonify({"error": str(e)}), 500



# ======================================================================
#  3. ANALYZE (AUTHENTICATION) USING ACTIVE USER MODEL
# ======================================================================
@keystroke_bp.route("/keystroke/analyze", methods=["POST"])
def analyze_keystroke():
    """Use trained ML model to authenticate keystroke pattern."""
    try:
        data = request.get_json()
        user_id = data.get("user_id")
        features = data.get("keystroke_features", {})

        if not user_id:
            return jsonify({"error": "user_id required"}), 400

        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        # Load model
        model_rec = MLModel.query.filter_by(user_id=user_id, is_active=True).first()
        if not model_rec:
            return jsonify({
                "requires_training": True,
                "message": "No trained model exists for this user yet",
                "authenticated": None
            }), 200

        # Load model package (includes scaler if available)
        model_package = pickle.loads(model_rec.model_data)

        # Handle both old models (just model) and new models (model + scaler)
        if isinstance(model_package, dict):
            model = model_package['model']
            scaler = model_package.get('scaler', None)
        else:
            model = model_package  # Old model format
            scaler = None

        # Extract 21 features
        fv = extract_features(features)
        fv = np.array(fv).reshape(1, -1)

        # Apply scaling if scaler is available (new models)
        if scaler is not None:
            fv = scaler.transform(fv)

        # Prediction logic depends on model type
        pred = model.predict(fv)[0]

        if pred == -1:
            authenticated = False
            confidence = 0.25
        else:
            authenticated = True
            confidence = 0.85

        # Save anomaly score into last keystroke event
        last = (
            KeystrokeData.query
            .filter_by(user_id=user_id)
            .order_by(KeystrokeData.timestamp.desc())
            .first()
        )

        if last:
            last.anomaly_score = float(confidence)
            db.session.commit()

        return jsonify({
            "authenticated": authenticated,
            "confidence": confidence,
            "model_version": model_rec.model_version
        }), 200

    except Exception as e:
        print("ANALYZE ERROR:", e)
        return jsonify({"error": str(e)}), 500



# ======================================================================
#  4. USER PROFILE — METRICS + MODEL STATUS
# ======================================================================
@keystroke_bp.route("/keystroke/user-profile/<int:user_id>", methods=["GET"])
def get_user_keystroke_profile(user_id):
    try:
        user = User.query.get_or_404(user_id)

        total = KeystrokeData.query.filter_by(user_id=user_id).count()
        training = KeystrokeData.query.filter_by(user_id=user_id, is_training_data=True).count()

        model = MLModel.query.filter_by(user_id=user_id, is_active=True).first()

        # Recent anomaly trail
        recents = (
            KeystrokeData.query
            .filter_by(user_id=user_id)
            .filter(KeystrokeData.anomaly_score.isnot(None))
            .order_by(KeystrokeData.timestamp.desc())
            .limit(10)
            .all()
        )

        scores = [float(r.anomaly_score) for r in recents]
        avg_score = round(sum(scores) / len(scores), 4) if scores else 0

        return jsonify({
            "user_id": user_id,
            "user_name": user.name,
            "total_samples": total,
            "training_samples": training,
            "model_exists": bool(model),
            "model_info": model.to_dict() if model else None,
            "recent_scores": scores,
            "average_score": avg_score,
            "needs_retraining": training < 10 or not model
        })

    except Exception as e:
        print("PROFILE ERROR:", e)
        return jsonify({"error": str(e)}), 500



# ======================================================================
#  5. BATCH PROCESS (Used by bulk datasets)
# ======================================================================
@keystroke_bp.route("/keystroke/batch-process", methods=["POST"])
def batch_process():
    """Insert many keystroke samples at once."""
    try:
        req = request.get_json()
        batch = req.get("keystroke_batch", [])

        if not batch:
            return jsonify({"error": "No batch data"}), 400

        processed = 0
        results = []

        for item in batch:
            try:
                user_id = item.get("user_id")
                session_id = item.get("session_id")
                feats = item.get("keystroke_features", {})

                if not user_id or not session_id:
                    continue

                ks = KeystrokeData(
                    user_id=user_id,
                    session_id=session_id,
                    keystroke_features=json.dumps(feats),
                    is_training_data=item.get("is_training", True)
                )
                db.session.add(ks)
                processed += 1

                results.append({
                    "user_id": user_id,
                    "session_id": session_id,
                    "status": "ok"
                })

            except Exception as e:
                results.append({
                    "user_id": item.get("user_id"),
                    "session_id": item.get("session_id"),
                    "status": "error",
                    "error": str(e)
                })

        db.session.commit()

        return jsonify({
            "message": "Batch processed",
            "processed": processed,
            "results": results
        })

    except Exception as e:
        print("BATCH ERROR:", e)
        return jsonify({"error": str(e)}), 500
