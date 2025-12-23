# ================================================================
#  BioAuthAI — System Settings Routes
# Handles system configuration, thresholds, security settings,
# ML parameters, and admin-controlled options.
# Author: Sharifa Al-Kaabi ️
# ================================================================

from flask import Blueprint, request, jsonify
from src.models.user import db, SystemSettings
from datetime import datetime

settings_bp = Blueprint('settings', __name__)

# DEFAULT SYSTEM SETTINGS

DEFAULT_SETTINGS = {
    # ------------------- ML & Authentication Thresholds -------------------
    'far_threshold': {'value': 0.05, 'type': 'float', 'description': 'False Accept Rate limit'},
    'frr_threshold': {'value': 0.10, 'type': 'float', 'description': 'False Reject Rate limit'},
    'anomaly_threshold': {'value': 0.85, 'type': 'float', 'description': 'Anomaly score threshold'},
    'min_training_samples': {'value': 10, 'type': 'integer', 'description': 'Minimum samples required to train model'},
    'feature_count': {'value': 20, 'type': 'integer', 'description': 'Number of features used for training'},

    # ------------------- System Security -------------------
    'session_timeout': {'value': 30, 'type': 'integer', 'description': 'Session timeout (minutes)'},
    'max_failed_attempts': {'value': 3, 'type': 'integer', 'description': 'Maximum failed logins before lock'},
    'enable_mfa': {'value': True, 'type': 'boolean', 'description': 'Enable multi-factor authentication'},
    'enable_device_fingerprinting': {'value': True, 'type': 'boolean', 'description': 'Track user devices'},
    'enable_geolocation': {'value': True, 'type': 'boolean', 'description': 'Track login geolocation'},

    # ------------------- Alerts & Notifications -------------------
    'enable_email_alerts': {'value': True, 'type': 'boolean', 'description': 'Send alert emails'},
    'enable_slack_alerts': {'value': False, 'type': 'boolean', 'description': 'Send Slack alerts'},
    'alert_cooldown': {'value': 5, 'type': 'integer', 'description': 'Alert cooldown period (minutes)'},

    # ------------------- ML Model Management -------------------
    'enable_auto_retraining': {'value': True, 'type': 'boolean', 'description': 'Automatically retrain models'},
    'model_retraining_interval': {'value': 7, 'type': 'integer', 'description': 'Days between auto retraining'},
    'enable_data_drift_detection': {'value': True, 'type': 'boolean', 'description': 'Monitor drift in typing profiles'},

    # ------------------- Data Retention -------------------
    'data_retention_days': {'value': 90, 'type': 'integer', 'description': 'Number of days to keep keystroke logs'},

    # ------------------- Performance & Monitoring -------------------
    'enable_performance_monitoring': {'value': True, 'type': 'boolean', 'description': 'Track API performance'},
    'max_concurrent_sessions': {'value': 1000, 'type': 'integer', 'description': 'Limit concurrent sessions'},
    'cache_timeout': {'value': 300, 'type': 'integer', 'description': 'API cache timeout (seconds)'},

    # ------------------- Logging & Maintenance -------------------
    'log_level': {'value': 'INFO', 'type': 'string', 'description': 'Logging verbosity'},
    'enable_audit_logging': {'value': True, 'type': 'boolean', 'description': 'Track admin actions'},
    'enable_maintenance_mode': {'value': False, 'type': 'boolean', 'description': 'Put system in maintenance'},
    'backup_frequency': {'value': 'daily', 'type': 'string', 'description': 'Database backup schedule'},
}

# ================================================================
#  FUNCTION: Initialize settings if missing
# ================================================================
def initialize_default_settings():
    for key, config in DEFAULT_SETTINGS.items():
        setting = SystemSettings.query.filter_by(key=key).first()
        if not setting:
            db.session.add(SystemSettings(
                key=key,
                value=str(config['value']),
                data_type=config['type'],
                description=config['description'],
                updated_by="System"
            ))
    db.session.commit()


# ================================================================
# GET ALL SETTINGS
# ================================================================
@settings_bp.route('/settings', methods=['GET'])
def get_all_settings():
    try:
        initialize_default_settings()
        settings = SystemSettings.query.all()

        return jsonify({s.key: s.to_dict() for s in settings})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ================================================================
# GET SINGLE SETTING
# ================================================================
@settings_bp.route('/settings/<key>', methods=['GET'])
def get_setting(key):
    try:
        setting = SystemSettings.query.filter_by(key=key).first()

        if setting:
            return jsonify(setting.to_dict())

        if key in DEFAULT_SETTINGS:
            # Return default settings if not in DB
            conf = DEFAULT_SETTINGS[key]
            return jsonify({
                "key": key,
                "value": conf["value"],
                "data_type": conf["type"],
                "description": conf["description"],
                "is_default": True
            })

        return jsonify({"error": "Setting not found"}), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ================================================================
# UPDATE SINGLE SETTING
# ================================================================
@settings_bp.route('/settings/<key>', methods=['PUT'])
def update_setting(key):
    try:
        data = request.get_json()
        new_value = data.get("value")
        updated_by = data.get("updated_by", "Admin")

        if new_value is None:
            return jsonify({"error": "Value is required"}), 400

        setting = SystemSettings.query.filter_by(key=key).first()

        if not setting:
            if key not in DEFAULT_SETTINGS:
                return jsonify({"error": "Setting not found"}), 404
            
            conf = DEFAULT_SETTINGS[key]
            setting = SystemSettings(
                key=key,
                value=str(new_value),
                data_type=conf["type"],
                description=conf["description"],
                updated_by=updated_by
            )
            db.session.add(setting)
        else:
            setting.value = str(new_value)
            setting.updated_at = datetime.utcnow()
            setting.updated_by = updated_by

        db.session.commit()

        return jsonify({"message": "Updated", "setting": setting.to_dict()})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ================================================================
# BULK UPDATE
# ================================================================
@settings_bp.route('/settings/bulk-update', methods=['PUT'])
def bulk_update():
    try:
        data = request.get_json()
        settings_data = data.get("settings", {})
        updated_by = data.get("updated_by", "Admin")

        changed = []

        for key, value in settings_data.items():
            setting = SystemSettings.query.filter_by(key=key).first()

            if not setting:
                if key not in DEFAULT_SETTINGS:
                    continue
                conf = DEFAULT_SETTINGS[key]
                setting = SystemSettings(
                    key=key,
                    value=str(value),
                    data_type=conf["type"],
                    description=conf["description"],
                    updated_by=updated_by
                )
                db.session.add(setting)
            else:
                setting.value = str(value)
                setting.updated_at = datetime.utcnow()
                setting.updated_by = updated_by

            changed.append(key)

        db.session.commit()

        return jsonify({"message": "Bulk update complete", "updated": changed})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ================================================================
# RESET SETTINGS TO DEFAULT
# ================================================================
@settings_bp.route('/settings/reset', methods=['POST'])
def reset_settings():
    try:
        SystemSettings.query.delete()
        db.session.commit()
        initialize_default_settings()
        return jsonify({"message": "All settings reset to defaults"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ================================================================
# EXPORT SETTINGS
# ================================================================
@settings_bp.route('/settings/export', methods=['GET'])
def export_settings():
    try:
        settings = SystemSettings.query.all()
        export = {
            "exported_at": datetime.utcnow().isoformat(),
            "version": "3.0",
            "settings": {s.key: s.to_dict() for s in settings}
        }
        return jsonify(export)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ================================================================
# IMPORT SETTINGS
# ================================================================
@settings_bp.route('/settings/import', methods=['POST'])
def import_settings():
    try:
        data = request.get_json()
        imported_data = data.get("settings", {})
        updated_by = data.get("updated_by", "Import")

        for key, config in imported_data.items():
            setting = SystemSettings.query.filter_by(key=key).first()

            if not setting:
                setting = SystemSettings(
                    key=key,
                    value=str(config["value"]),
                    data_type=config.get("data_type", "string"),
                    description=config.get("description", ""),
                    updated_by=updated_by
                )
                db.session.add(setting)
            else:
                setting.value = str(config["value"])
                setting.updated_at = datetime.utcnow()
                setting.updated_by = updated_by

        db.session.commit()

        return jsonify({"message": "Import complete"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500
