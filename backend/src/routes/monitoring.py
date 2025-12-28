from flask import Blueprint, request, jsonify
from src.models.user import db, User, KeystrokeData, AuthenticationLog, SecurityAlert, MLModel
from datetime import datetime, timedelta
import json

monitoring_bp = Blueprint("monitoring", __name__)


#  REAL-TIME LOGIN ATTEMPTS

@monitoring_bp.route("/monitoring/recent-logins", methods=["GET"])
def get_recent_logins():
    """Get recent authentication attempts"""
    try:
        limit = int(request.args.get("limit", 50))
        hours = int(request.args.get("hours", 24))
        
        since = datetime.utcnow() - timedelta(hours=hours)
        
        logs = AuthenticationLog.query.filter(
            AuthenticationLog.timestamp >= since
        ).order_by(
            AuthenticationLog.timestamp.desc()
        ).limit(limit).all()
        
        data = []
        for log in logs:
            user = User.query.get(log.user_id)
            data.append({
                "id": log.id,
                "user_id": log.user_id,
                "user_email": user.email if user else "Unknown",
                "timestamp": log.timestamp.isoformat(),
                "result": log.result,
                "confidence_score": log.confidence_score,
                "ip_address": log.ip_address,
                "device_fingerprint": log.device_fingerprint,
                "action_taken": log.action_taken
            })
        
        return jsonify(data), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================
#  USER METRICS
# ============================================================
@monitoring_bp.route("/monitoring/user-metrics/<int:user_id>", methods=["GET"])
def get_user_metrics(user_id):
    """Get metrics for a specific user"""
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        hours = int(request.args.get("hours", 24))
        since = datetime.utcnow() - timedelta(hours=hours)
        
        # Authentication attempts
        total_attempts = AuthenticationLog.query.filter(
            AuthenticationLog.user_id == user_id,
            AuthenticationLog.timestamp >= since
        ).count()
        
        successful = AuthenticationLog.query.filter(
            AuthenticationLog.user_id == user_id,
            AuthenticationLog.timestamp >= since,
            AuthenticationLog.result == "success"
        ).count()
        
        failed = AuthenticationLog.query.filter(
            AuthenticationLog.user_id == user_id,
            AuthenticationLog.timestamp >= since,
            AuthenticationLog.result == "failed"
        ).count()
        
        # Keystroke samples
        keystroke_samples = KeystrokeData.query.filter(
            KeystrokeData.user_id == user_id,
            KeystrokeData.timestamp >= since
        ).count()
        
        # Average confidence
        logs_with_confidence = AuthenticationLog.query.filter(
            AuthenticationLog.user_id == user_id,
            AuthenticationLog.timestamp >= since,
            AuthenticationLog.confidence_score.isnot(None)
        ).all()
        
        avg_confidence = 0.0
        if logs_with_confidence:
            avg_confidence = sum(log.confidence_score for log in logs_with_confidence) / len(logs_with_confidence)
        
        # Anomalies
        anomalies = KeystrokeData.query.filter(
            KeystrokeData.user_id == user_id,
            KeystrokeData.timestamp >= since,
            KeystrokeData.anomaly_score > 0.7
        ).count()
        
        # ML Model info
        ml_model = MLModel.query.filter_by(user_id=user_id, is_active=True).first()
        
        return jsonify({
            "user_id": user_id,
            "user_email": user.email,
            "total_attempts": total_attempts,
            "successful_attempts": successful,
            "failed_attempts": failed,
            "success_rate": round((successful / total_attempts * 100) if total_attempts > 0 else 0, 2),
            "keystroke_samples": keystroke_samples,
            "average_confidence": round(avg_confidence, 4),
            "anomalies_detected": anomalies,
            "ml_model_active": ml_model is not None,
            "model_version": ml_model.model_version if ml_model else None,
            "model_accuracy": ml_model.accuracy if ml_model else None,
            "period_hours": hours
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================
#  KEYSTROKE DATA STREAM
# ============================================================
@monitoring_bp.route("/monitoring/keystroke-stream/<int:user_id>", methods=["GET"])
def get_keystroke_stream(user_id):
    """Get keystroke data stream for a user"""
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        limit = int(request.args.get("limit", 20))
        
        keystroke_data = KeystrokeData.query.filter(
            KeystrokeData.user_id == user_id,
            KeystrokeData.is_training_data == False
        ).order_by(
            KeystrokeData.timestamp.desc()
        ).limit(limit).all()
        
        data = []
        for ks in keystroke_data:
            try:
                features = json.loads(ks.keystroke_features) if ks.keystroke_features else {}
            except:
                features = {}
            
            data.append({
                "id": ks.id,
                "user_id": ks.user_id,
                "timestamp": ks.timestamp.isoformat() if ks.timestamp else None,
                "session_id": ks.session_id,
                "anomaly_score": ks.anomaly_score,
                "is_anomalous": ks.anomaly_score > 0.7 if ks.anomaly_score else False,
                "features_available": len(features) > 0
            })
        
        return jsonify(data), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================
#  SECURITY ALERTS STREAM
# ============================================================
@monitoring_bp.route("/monitoring/alerts-stream", methods=["GET"])
def get_alerts_stream():
    """Get security alerts stream"""
    try:
        limit = int(request.args.get("limit", 50))
        hours = int(request.args.get("hours", 24))
        severity = request.args.get("severity")  # Optional filter
        
        since = datetime.utcnow() - timedelta(hours=hours)
        
        query = SecurityAlert.query.filter(
            SecurityAlert.timestamp >= since
        )
        
        if severity:
            query = query.filter(SecurityAlert.severity == severity)
        
        alerts = query.order_by(
            SecurityAlert.timestamp.desc()
        ).limit(limit).all()
        
        data = []
        for alert in alerts:
            user = User.query.get(alert.user_id) if alert.user_id else None
            data.append({
                "id": alert.id,
                "user_id": alert.user_id,
                "user_email": user.email if user else "System",
                "alert_type": alert.alert_type,
                "severity": alert.severity,
                "title": alert.title,
                "description": alert.description,
                "timestamp": alert.timestamp.isoformat(),
                "status": alert.status,
                "confidence_score": alert.confidence_score
            })
        
        return jsonify(data), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================
#  SYSTEM HEALTH
# ============================================================
@monitoring_bp.route("/monitoring/system-health", methods=["GET"])
def get_system_health():
    """Get system health metrics"""
    try:
        # Total users
        total_users = User.query.count()
        active_users = User.query.filter_by(status="active").count()
        locked_users = User.query.filter_by(status="locked").count()
        
        # Total authentication logs
        total_logs = AuthenticationLog.query.count()
        
        # Recent activity (last hour)
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        recent_logins = AuthenticationLog.query.filter(
            AuthenticationLog.timestamp >= one_hour_ago
        ).count()
        
        # Recent alerts
        recent_alerts = SecurityAlert.query.filter(
            SecurityAlert.timestamp >= one_hour_ago
        ).count()
        
        # ML Models
        total_models = MLModel.query.count()
        active_models = MLModel.query.filter_by(is_active=True).count()
        
        # Database size estimate
        keystroke_data_count = KeystrokeData.query.count()
        
        return jsonify({
            "timestamp": datetime.utcnow().isoformat(),
            "users": {
                "total": total_users,
                "active": active_users,
                "locked": locked_users
            },
            "authentication": {
                "total_logs": total_logs,
                "recent_logins_1h": recent_logins
            },
            "alerts": {
                "total_alerts": SecurityAlert.query.count(),
                "recent_alerts_1h": recent_alerts
            },
            "ml_models": {
                "total": total_models,
                "active": active_models
            },
            "data": {
                "keystroke_samples": keystroke_data_count
            },
            "status": "healthy"
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================
#  ANOMALY DETECTION STATS
# ============================================================
@monitoring_bp.route("/monitoring/anomaly-stats", methods=["GET"])
def get_anomaly_stats():
    """Get anomaly detection statistics"""
    try:
        hours = int(request.args.get("hours", 24))
        since = datetime.utcnow() - timedelta(hours=hours)

        # Anomalous keystroke samples
        anomalous_samples = KeystrokeData.query.filter(
            KeystrokeData.timestamp >= since,
            KeystrokeData.anomaly_score > 0.7
        ).count()

        total_samples = KeystrokeData.query.filter(
            KeystrokeData.timestamp >= since
        ).count()

        # Anomaly rate
        anomaly_rate = (anomalous_samples / total_samples * 100) if total_samples > 0 else 0

        # Anomalies by severity
        critical_alerts = SecurityAlert.query.filter(
            SecurityAlert.timestamp >= since,
            SecurityAlert.severity == "critical"
        ).count()

        high_alerts = SecurityAlert.query.filter(
            SecurityAlert.timestamp >= since,
            SecurityAlert.severity == "high"
        ).count()

        medium_alerts = SecurityAlert.query.filter(
            SecurityAlert.timestamp >= since,
            SecurityAlert.severity == "medium"
        ).count()

        # Top anomalous users
        anomalous_users = db.session.query(
            KeystrokeData.user_id,
            db.func.count(KeystrokeData.id).label('anomaly_count')
        ).filter(
            KeystrokeData.timestamp >= since,
            KeystrokeData.anomaly_score > 0.7
        ).group_by(
            KeystrokeData.user_id
        ).order_by(
            db.func.count(KeystrokeData.id).desc()
        ).limit(10).all()

        top_users = []
        for user_id, count in anomalous_users:
            user = User.query.get(user_id)
            top_users.append({
                "user_id": user_id,
                "user_email": user.email if user else "Unknown",
                "anomaly_count": count
            })

        return jsonify({
            "period_hours": hours,
            "anomalous_samples": anomalous_samples,
            "total_samples": total_samples,
            "anomaly_rate": round(anomaly_rate, 2),
            "alerts_by_severity": {
                "critical": critical_alerts,
                "high": high_alerts,
                "medium": medium_alerts
            },
            "top_anomalous_users": top_users
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================
#  LIVE MONITORING CONTROL (FOR FRONTEND)
# ============================================================

# Global monitoring state (in production, use Redis or database)
MONITORING_STATE = {"active": False}

@monitoring_bp.route("/monitoring/status", methods=["GET"])
def get_monitoring_status():
    """Get current monitoring status"""
    try:
        return jsonify({
            "active": MONITORING_STATE["active"],
            "timestamp": datetime.utcnow().isoformat()
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@monitoring_bp.route("/monitoring/start", methods=["POST"])
def start_monitoring():
    """Start live monitoring"""
    try:
        MONITORING_STATE["active"] = True
        return jsonify({
            "message": "Monitoring started",
            "active": True,
            "timestamp": datetime.utcnow().isoformat()
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@monitoring_bp.route("/monitoring/stop", methods=["POST"])
def stop_monitoring():
    """Stop live monitoring"""
    try:
        MONITORING_STATE["active"] = False
        return jsonify({
            "message": "Monitoring stopped",
            "active": False,
            "timestamp": datetime.utcnow().isoformat()
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@monitoring_bp.route("/monitoring/live-data", methods=["GET"])
def get_live_data():
    """Get live monitoring data"""
    try:
        # Calculate last 5 minutes of activity
        five_min_ago = datetime.utcnow() - timedelta(minutes=5)

        # Active sessions (recent auth attempts)
        active_sessions = AuthenticationLog.query.filter(
            AuthenticationLog.timestamp >= five_min_ago
        ).count()

        # Authentication success rate
        total_auth = AuthenticationLog.query.filter(
            AuthenticationLog.timestamp >= five_min_ago
        ).count()

        successful_auth = AuthenticationLog.query.filter(
            AuthenticationLog.timestamp >= five_min_ago,
            AuthenticationLog.result == "success"
        ).count()

        auth_rate = round((successful_auth / total_auth * 100) if total_auth > 0 else 0, 1)

        # Anomaly rate
        recent_samples = KeystrokeData.query.filter(
            KeystrokeData.timestamp >= five_min_ago
        ).count()

        anomalous = KeystrokeData.query.filter(
            KeystrokeData.timestamp >= five_min_ago,
            KeystrokeData.anomaly_score > 0.7
        ).count()

        anomaly_rate = round((anomalous / recent_samples * 100) if recent_samples > 0 else 0, 1)

        return jsonify({
            "active_sessions_count": active_sessions,
            "authentication_rate": auth_rate,
            "anomaly_rate": anomaly_rate,
            "recent_keystroke_samples": recent_samples,
            "timestamp": datetime.utcnow().isoformat()
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
