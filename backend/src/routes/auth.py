from flask import Blueprint, request, jsonify
from src.models.user import (
    User,
    UserDevice,
    AuthenticationLog,
    SecurityAlert,
    KeystrokeData,
    MLModel,
    SystemSettings,
    db
)
from src.utils.feature_extractor import extract_features
from datetime import datetime, timedelta, timezone
import json
import pickle
import numpy as np
import uuid

auth_bp = Blueprint("auth", __name__)


def get_threshold(key, default_value):
    """Get threshold from SystemSettings or use default."""
    setting = SystemSettings.query.filter_by(key=key).first()
    if setting:
        return float(setting.value)
    return default_value


def _log_auth_attempt(user_id, success, method="keystroke", confidence=None, device_info=None, ip_address=None, user_agent=None):
    """Log authentication attempt with device information."""
    log = AuthenticationLog(
        user_id=user_id,
        timestamp=datetime.now(timezone.utc).replace(tzinfo=None),
        result="success" if success else "failed",
        confidence_score=confidence,
        ip_address=ip_address or request.remote_addr,
        user_agent=user_agent or request.headers.get('User-Agent'),
        device_fingerprint=device_info.get('device_id') if device_info else None,
        location=None  # Can be populated with geolocation API
    )
    db.session.add(log)


def _create_alert(user_id, title, desc, severity):
    """Create security alert."""
    alert = SecurityAlert(
        user_id=user_id,
        alert_type="anomaly",
        severity=severity,
        title=title,
        description=desc,
        timestamp=datetime.now(timezone.utc).replace(tzinfo=None)
    )
    db.session.add(alert)


def _failed_login(email):
    """Handle failed login attempt."""
    user = User.query.filter_by(email=email).first()
    
    if user:
        user.failed_attempts += 1
        if user.failed_attempts >= 3:
            user.status = "locked"
            user.locked_until = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(minutes=30)
            _create_alert(
                user.id,
                title="Account Locked",
                desc="3 failed password attempts",
                severity="high"
            )
        db.session.commit()
    
    if user:
        _log_auth_attempt(user.id, success=False, method="password", device_info=None, ip_address=request.remote_addr, user_agent=request.headers.get('User-Agent'))

    return jsonify({"error": "Invalid email or password"}), 401


@auth_bp.route("/auth/login", methods=["POST"])
def login():
    """
    Main login endpoint with keystroke authentication.

    Expected JSON:
        {
            "email": "user@example.com",
            "password": "password123",
            "keystroke_data": {
                "dwell_times": [...],
                "flight_times": [...],
                "pause_patterns": [...],
                "typing_speed": float
            },
            "device_info": {
                "device_id": "...",
                "device_name": "...",
                "browser": "...",
                "os_name": "..."
            }
        }

    Returns:
        JSON response with authentication result
    """
    try:
        data = request.json or {}
        email = data.get("email", "").strip().lower()
        password = data.get("password", "")
        keystroke_data = data.get("keystroke_data")
        device_info = data.get("device_info", {})

        # Validate input
        if not email or not password:
            return jsonify({"error": "Email and password required"}), 400

        # Find user
        user = User.query.filter_by(email=email).first()

        if not user or not user.check_password(password):
            return _failed_login(email)

        # Check account status
        if user.status == "locked" and user.locked_until:
            if datetime.now(timezone.utc).replace(tzinfo=None) < user.locked_until:
                return jsonify({
                    "error": "Account locked",
                    "locked_until": user.locked_until.isoformat()
                }), 403
            else:
                user.status = "active"
                user.locked_until = None
                user.failed_attempts = 0
                db.session.commit()

        # Device tracking
        device_id = device_info.get("device_id", "unknown-device")
        device = UserDevice.query.filter_by(
            user_id=user.id,
            device_fingerprint=device_id
        ).first()
        
        is_new_device = False
        if not device:
            device = UserDevice(
                user_id=user.id,
                device_fingerprint=device_id,
                device_name=device_info.get("device_name", "Unknown"),
                device_type=device_info.get("device_type", "desktop"),
                browser=device_info.get("browser", "Unknown"),
                os=device_info.get("os_name", "Unknown"),
                is_trusted=False
            )
            db.session.add(device)
            is_new_device = True
        else:
            device.last_seen = datetime.now(timezone.utc).replace(tzinfo=None)

        db.session.commit()

        # Handle password-only login (no keystroke data)
        if not keystroke_data:
            user.last_login = datetime.now(timezone.utc).replace(tzinfo=None)
            user.failed_attempts = 0
            db.session.commit()

            _log_auth_attempt(user.id, success=True, method="password_only", device_info=device_info, ip_address=request.remote_addr, user_agent=request.headers.get('User-Agent'))
            db.session.commit()
            
            return jsonify({
                "success": True,
                "message": "Password verified (no keystroke data)",
                "user": user.to_dict(),
                "new_device": bool(is_new_device),
                "confidence": None,
                "session_id": str(uuid.uuid4())
            }), 200

        # Collect keystroke data for training
        keystroke_record = KeystrokeData(
            user_id=user.id,
            session_id=f"login_{datetime.now(timezone.utc).timestamp()}",
            keystroke_features=json.dumps(keystroke_data),
            device_info=json.dumps(device_info),
            is_training_data=True,
            anomaly_score=0.0,
            data_split=None
        )
        db.session.add(keystroke_record)
        db.session.commit()

        sample_count = KeystrokeData.query.filter_by(user_id=user.id).count()

        # Extract keystroke features
        try:
            features = extract_features(keystroke_data)
            if not features or len(features) != 21:
                return jsonify({
                    "error": f"Feature extraction error: got {len(features) if features else 0} features, expected 21"
                }), 400
            features = np.array(features, dtype=np.float32)
        except Exception as e:
            return jsonify({"error": f"Feature extraction failed: {str(e)}"}), 400

        # Load user's ML model
        ml_model = MLModel.query.filter_by(user_id=user.id, is_active=True).first()
        if not ml_model:
            user.last_login = datetime.now(timezone.utc).replace(tzinfo=None)
            user.failed_attempts = 0
            db.session.commit()

            _log_auth_attempt(user.id, success=True, method="keystroke_no_model", device_info=device_info, ip_address=request.remote_addr, user_agent=request.headers.get('User-Agent'))
            db.session.commit()

            model_ready = sample_count >= 280

            return jsonify({
                "success": True,
                "message": f"Login successful - collecting keystroke data ({sample_count}/340)",
                "user": user.to_dict(),
                "model_missing": True,
                "model_building": True,
                "samples_collected": sample_count,
                "samples_needed": 340,
                "model_ready": bool(model_ready),
                "new_device": bool(is_new_device),
                "session_id": str(uuid.uuid4())
            }), 200

        # Perform model prediction
        try:
            # Load model package (includes scaler if available)
            model_package = pickle.loads(ml_model.model_data)

            # Handle both old models (just model) and new models (model + scaler)
            if isinstance(model_package, dict):
                model = model_package['model']
                scaler = model_package.get('scaler', None)
            else:
                model = model_package  # Old model format
                scaler = None

            X = features.reshape(1, -1)

            # Apply scaling if scaler is available (new models)
            if scaler is not None:
                X = scaler.transform(X)

            prediction = model.predict(X)[0]
            is_genuine = prediction == 1

            try:
                proba = model.predict_proba(X)[0]
                confidence = float(proba[-1])
            except:
                confidence = 0.95 if is_genuine else 0.15

            # Get dynamic thresholds from system settings
            anomaly_threshold = get_threshold('anomaly_threshold', 0.85)  # Default 85%
            far_threshold = get_threshold('far_threshold', 0.05)  # Default 5%

            # Access denied if confidence is too low (inverse of anomaly threshold)
            # Higher anomaly threshold = more strict (requires higher confidence)
            access_denied_threshold = 1.0 - anomaly_threshold

            anomaly = not is_genuine or confidence < (1.0 - far_threshold)
            access_denied = confidence < access_denied_threshold

        except Exception as e:
            return jsonify({"error": f"Model prediction failed: {str(e)}"}), 500

        # Log authentication attempt
        _log_auth_attempt(user.id, success=(not access_denied), confidence=confidence, device_info=device_info, ip_address=request.remote_addr, user_agent=request.headers.get('User-Agent'))

        # Create security alerts if needed
        if access_denied:
            severity = "critical"
            _create_alert(
                user.id,
                title="IMPERSONATION ATTEMPT DETECTED",
                desc=f"Access DENIED. Confidence score: {confidence:.2%}. Behavioral pattern does not match legitimate user profile. Possible impersonation attempt.",
                severity=severity
            )
        elif anomaly:
            severity = "high" if confidence < 0.65 else "medium"
            _create_alert(
                user.id,
                title="Suspicious Keystroke Pattern Detected",
                desc=f"Confidence score: {confidence:.2%}. Pattern differs from baseline but access granted.",
                severity=severity
            )

        if is_new_device:
            _create_alert(
                user.id,
                title="New Device Detected",
                desc=f"Login from new device: {device_info.get('device_name', 'Unknown')}",
                severity="low"
            )

        # Update user status
        user.auth_score = confidence
        if access_denied:
            user.failed_attempts += 1
            if user.failed_attempts >= 3:
                user.status = "locked"
                user.locked_until = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(minutes=30)
                _create_alert(
                    user.id,
                    title="Account Locked",
                    desc="3 consecutive impersonation attempts detected",
                    severity="critical"
                )
        elif is_genuine and not anomaly:
            user.failed_attempts = 0
            user.last_login = datetime.now(timezone.utc).replace(tzinfo=None)
        elif is_genuine and anomaly:
            user.failed_attempts = 0
            user.last_login = datetime.now(timezone.utc).replace(tzinfo=None)
        else:
            user.failed_attempts += 1
            if user.failed_attempts >= 3:
                user.status = "locked"
                user.locked_until = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(minutes=30)
                _create_alert(
                    user.id,
                    title="Account Locked",
                    desc="3 consecutive authentication failures detected",
                    severity="critical"
                )

        db.session.commit()

        # Return response
        if access_denied:
            return jsonify({
                "success": False,
                "message": f"Access DENIED: Behavioral mismatch detected (confidence: {confidence:.2%})",
                "user": user.to_dict(),
                "prediction": "impostor",
                "confidence": round(confidence, 4),
                "anomaly": True,
                "access_denied": True,
                "reason": "Confidence score below threshold (< 60%)",
                "new_device": bool(is_new_device),
                "model_version": ml_model.model_version,
                "session_id": str(uuid.uuid4())
            }), 403
        else:
            return jsonify({
                "success": bool(is_genuine),
                "message": "Authentication successful" if is_genuine else "Authentication successful with warning",
                "user": user.to_dict(),
                "prediction": "genuine" if is_genuine else "genuine_with_warning",
                "confidence": round(confidence, 4),
                "anomaly": bool(anomaly),
                "access_denied": False,
                "new_device": bool(is_new_device),
                "model_version": ml_model.model_version,
                "session_id": str(uuid.uuid4())
            }), 200

    except Exception as e:
        db.session.rollback()
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Login error: {str(e)}"}), 500


@auth_bp.route("/auth/logout", methods=["POST"])
def logout():
    """Logout endpoint."""
    try:
        data = request.json or {}
        user_id = data.get("user_id")


        if user_id:
            user = User.query.get(user_id)
            if user:
                log = AuthenticationLog(
                    user_id=user_id,
                    timestamp=datetime.now(timezone.utc).replace(tzinfo=None),
                    result="logout"
                )
                db.session.add(log)
                db.session.commit()

        return jsonify({"success": True, "message": "Logged out successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@auth_bp.route("/auth/verify", methods=["POST"])
def verify():
    """Verify user session."""
    try:
        data = request.json or {}
        user_id = data.get("user_id")

        if not user_id:
            return jsonify({"error": "user_id required"}), 400

        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        return jsonify({
            "success": True,
            "user": user.to_dict()
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@auth_bp.route("/auth/keystroke-status/<int:user_id>", methods=["GET"])
def get_keystroke_status(user_id):
    """Get keystroke collection status for a user."""
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        sample_count = KeystrokeData.query.filter_by(user_id=user_id).count()
        ml_model = MLModel.query.filter_by(user_id=user_id, is_active=True).first()

        progress_percent = min(100, (sample_count / 340) * 100)
        model_ready = sample_count >= 280

        return jsonify({
            "user_id": user_id,
            "user_email": user.email,
            "samples_collected": sample_count,
            "samples_needed": 340,
            "progress_percent": round(progress_percent, 1),
            "model_ready": bool(model_ready),
            "model_exists": bool(ml_model is not None),
            "model_version": ml_model.model_version if ml_model else None
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
