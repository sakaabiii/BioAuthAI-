# ============================================================
#  BioAuthAI - Analytics API (FULL | CLEAN | READY)
# ============================================================

from flask import Blueprint, request, jsonify, send_file
from src.models.user import (
    db, User, AuthenticationLog, SecurityAlert, KeystrokeData,
    UserDevice, MLModel
)
from datetime import datetime, timedelta
from sqlalchemy import func, and_, distinct
import pandas as pd
import io
import json

analytics_bp = Blueprint('analytics', __name__)

# DASHBOARD STATS

@analytics_bp.route('/analytics/dashboard-stats', methods=['GET'])
def get_dashboard_stats():
    try:
        hours = int(request.args.get('hours', 24))
        since = datetime.utcnow() - timedelta(hours=hours)

        active_sessions = db.session.query(
            func.count(distinct(AuthenticationLog.session_id))
        ).filter(
            AuthenticationLog.timestamp >= since,
            AuthenticationLog.session_id.isnot(None)
        ).scalar() or 0

        total_auths = AuthenticationLog.query.filter(
            AuthenticationLog.timestamp >= since
        ).count()

        successful_auths = AuthenticationLog.query.filter(
            AuthenticationLog.timestamp >= since,
            AuthenticationLog.result == 'success'
        ).count()

        auth_rate = (successful_auths / total_auths * 100) if total_auths > 0 else 0

        alerts_count = SecurityAlert.query.filter(
            SecurityAlert.timestamp >= since
        ).count()

        total_users = User.query.count()

        return jsonify({
            'active_sessions': active_sessions,
            'authentication_rate': round(auth_rate, 1),
            'security_alerts': alerts_count,
            'total_users': total_users,
            'period_hours': hours
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================
# 2) AUTHENTICATION TRENDS (7 days)
# ============================================================

@analytics_bp.route('/analytics/authentication-trends', methods=['GET'])
def get_authentication_trends():
    try:
        days = int(request.args.get('days', 7))
        trends_data = []

        for i in range(days):
            date = datetime.utcnow() - timedelta(days=days - i - 1)
            start = date.replace(hour=0, minute=0, second=0, microsecond=0)
            end = start + timedelta(days=1)

            logs = AuthenticationLog.query.filter(
                AuthenticationLog.timestamp >= start,
                AuthenticationLog.timestamp < end
            ).all()

            successful = sum(1 for log in logs if log.result == 'success')
            failed = sum(1 for log in logs if log.result == 'failed')
            anomalies = sum(1 for log in logs if log.result == 'anomaly')

            far = 0.0
            frr = 0.0
            if logs:
                false_accepts = sum(1 for log in logs if log.result == 'success' and (log.confidence_score or 1) < 0.5)
                false_rejects = sum(1 for log in logs if log.result == 'failed' and (log.confidence_score or 0) >= 0.5)
                total = len(logs)
                far = false_accepts / total
                frr = false_rejects / total

            trends_data.append({
                'date': date.strftime('%Y-%m-%d'),
                'successful': successful,
                'failed': failed,
                'anomalies': anomalies,
                'far': round(far, 3),
                'frr': round(frr, 3)
            })

        return jsonify(trends_data)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================
# 3) HOURLY ACTIVITY
# ============================================================

@analytics_bp.route('/analytics/hourly-activity', methods=['GET'])
def get_hourly_activity():
    try:
        hourly_data = []

        now = datetime.utcnow().replace(minute=0, second=0, microsecond=0)

        for i in range(24):
            hour_start = now - timedelta(hours=24 - i)
            hour_end = hour_start + timedelta(hours=1)

            logs = AuthenticationLog.query.filter(
                AuthenticationLog.timestamp >= hour_start,
                AuthenticationLog.timestamp < hour_end
            ).all()

            hourly_data.append({
                'hour': hour_start.strftime('%H'),
                'authentications': len(logs),
                'anomalies': sum(1 for log in logs if log.result == 'anomaly')
            })

        return jsonify(hourly_data)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================
# 4) DEVICE DISTRIBUTION
# ============================================================

@analytics_bp.route('/analytics/device-distribution', methods=['GET'])
def get_device_distribution():
    try:
        device_counts = db.session.query(
            UserDevice.device_type,
            func.count(distinct(UserDevice.user_id))
        ).filter(
            UserDevice.status == 'active'
        ).group_by(UserDevice.device_type).all()

        total = sum(c for _, c in device_counts) or 1

        color_map = {
            'desktop': '#3B82F6',
            'mobile': '#10B981',
            'tablet': '#F59E0B'
        }

        result = []
        for device, count in device_counts:
            result.append({
                'name': (device or 'Unknown').capitalize(),
                'value': round((count / total) * 100, 1),
                'users': count,
                'color': color_map.get(device.lower(), '#3B82F6')
            })

        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================
# 5) DEPARTMENT PERFORMANCE
# ============================================================

@analytics_bp.route('/analytics/department-performance', methods=['GET'])
def get_department_performance():
    try:
        departments = db.session.query(
            User.department,
            func.count(User.id),
            func.avg(User.auth_score)
        ).filter(
            User.department.isnot(None),
            User.status == 'active'
        ).group_by(User.department).all()

        result = []

        for dept, count, avg_score in departments:
            user_ids = [u.id for u in User.query.filter_by(department=dept).all()]
            anomalies = AuthenticationLog.query.filter(
                AuthenticationLog.user_id.in_(user_ids),
                AuthenticationLog.result == 'anomaly'
            ).count()

            result.append({
                'name': dept,
                'users': count,
                'anomalies': anomalies,
                'avgScore': round(avg_score or 0, 2)
            })

        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================
# 6) PERFORMANCE METRICS (FAR / FRR / ACC)
# ============================================================

@analytics_bp.route('/analytics/performance-metrics', methods=['GET'])
def get_performance_metrics():
    try:
        logs = AuthenticationLog.query.filter(
            AuthenticationLog.confidence_score.isnot(None)
        ).limit(1000).all()

        if not logs:
            return jsonify([])

        total = len(logs)
        successful = sum(1 for l in logs if l.result == 'success')
        false_accepts = sum(1 for l in logs if l.result == 'success' and l.confidence_score < 0.5)
        false_rejects = sum(1 for l in logs if l.result == 'failed' and l.confidence_score >= 0.5)

        far = false_accepts / total
        frr = false_rejects / total
        accuracy = successful / total

        return jsonify([
            {'metric': 'FAR', 'current': round(far, 3), 'target': 0.05},
            {'metric': 'FRR', 'current': round(frr, 3), 'target': 0.10},
            {'metric': 'Accuracy', 'current': round(accuracy, 3), 'target': 0.90}
        ])

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================
# 7) RECENT ACTIVITIES
# ============================================================

@analytics_bp.route('/analytics/recent-activities', methods=['GET'])
def get_recent_activities():
    try:
        limit = int(request.args.get('limit', 20))

        activities = db.session.query(
            KeystrokeData.id,
            KeystrokeData.timestamp,
            KeystrokeData.session_id,
            User.name,
            User.email,
            User.role
        ).join(
            User, KeystrokeData.user_id == User.id
        ).order_by(
            KeystrokeData.timestamp.desc()
        ).limit(limit).all()

        result = [{
            'id': a.id,
            'timestamp': a.timestamp.isoformat() if a.timestamp else None,
            'session_id': a.session_id,
            'user_name': a.name,
            'user_email': a.email,
            'user_role': a.role,
            'activity_type': 'keystroke_capture'
        } for a in activities]

        return jsonify({'success': True, 'activities': result})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================
# 8) BIOMETRIC METRICS (GLOBAL)
# ============================================================

@analytics_bp.route('/analytics/biometric-metrics', methods=['GET'])
def get_biometric_metrics():
    try:
        models = MLModel.query.filter_by(is_active=True).all()
        if not models:
            return jsonify({'success': True, 'metrics': {}})

        avg_far = sum(m.far or 0 for m in models) / len(models)
        avg_frr = sum(m.frr or 0 for m in models) / len(models)
        avg_acc = sum(m.accuracy or 0 for m in models) / len(models)
        eer = (avg_far + avg_frr) / 2

        return jsonify({
            'success': True,
            'metrics': {
                'far': round(avg_far * 100, 2),
                'frr': round(avg_frr * 100, 2),
                'eer': round(eer * 100, 2),
                'accuracy': round(avg_acc * 100, 2)
            }
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================
# 9) PER-USER METRICS (UPDATED — FAR/FRR/EER INCLUDED)
# ============================================================

@analytics_bp.route('/analytics/per-user-metrics', methods=['GET'])
def get_per_user_metrics():
    try:
        # Use LEFT JOIN to include all users, even without trained models
        users_data = db.session.query(
            User.id,
            User.name,
            User.email,
            User.role,
            MLModel.accuracy,
            MLModel.far,
            MLModel.frr,
            MLModel.training_data_count,
            MLModel.created_at
        ).outerjoin(
            MLModel, (User.id == MLModel.user_id) & (MLModel.is_active == True)
        ).order_by(User.id).all()

        result = []
        for user_data in users_data:
            # Check if user has a model
            has_model = user_data.accuracy is not None

            if has_model:
                from src.models.user import KeystrokeData

                far_pct = (user_data.far or 0) * 100
                frr_pct = (user_data.frr or 0) * 100
                eer = (far_pct + frr_pct) / 2
                accuracy = round((user_data.accuracy or 0) * 100, 2)
                training_samples = user_data.training_data_count or 0
                model_trained_at = user_data.created_at.isoformat() if user_data.created_at else None

                # Get split counts for dataset users
                train_count = KeystrokeData.query.filter_by(user_id=user_data.id, data_split='train').count()
                val_count = KeystrokeData.query.filter_by(user_id=user_data.id, data_split='validation').count()
                test_count = KeystrokeData.query.filter_by(user_id=user_data.id, data_split='test').count()

                split_info = {
                    'train': train_count,
                    'validation': val_count,
                    'test': test_count
                } if train_count > 0 else None
            else:
                # User without model - count collected samples
                from src.models.user import KeystrokeData
                collected_samples = KeystrokeData.query.filter_by(user_id=user_data.id).count()

                far_pct = 0
                frr_pct = 0
                eer = 0
                accuracy = 0
                training_samples = collected_samples
                model_trained_at = None
                split_info = None

            result.append({
                'user_id': user_data.id,
                'user_name': user_data.name,
                'user_email': user_data.email,
                'user_role': user_data.role,
                'accuracy': accuracy,
                'far': round(far_pct, 2),
                'frr': round(frr_pct, 2),
                'eer': round(eer, 2),
                'training_samples': training_samples,
                'model_trained_at': model_trained_at,
                'has_model': has_model,
                'split_info': split_info
            })

        return jsonify({'success': True, 'users': result})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================
# 10) EXPORT USER ANALYTICS (XLSX)
# ============================================================

@analytics_bp.route('/analytics/export-user/<int:user_id>', methods=['GET'])
def export_user_xlsx(user_id):
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404

        logs = AuthenticationLog.query.filter_by(user_id=user_id).order_by(AuthenticationLog.timestamp.desc()).all()
        keystrokes = KeystrokeData.query.filter_by(user_id=user_id).order_by(KeystrokeData.timestamp.desc()).all()
        model = MLModel.query.filter_by(user_id=user_id, is_active=True).first()
        alerts = SecurityAlert.query.filter_by(user_id=user_id).order_by(SecurityAlert.timestamp.desc()).all()
        devices = UserDevice.query.filter_by(user_id=user_id).order_by(UserDevice.last_seen.desc()).all()

        # ===== SHEET 1: FORENSIC SUMMARY =====
        summary_df = pd.DataFrame([{
            'User ID': user.id,
            'Name': user.name,
            'Email': user.email,
            'Role': user.role,
            'Department': user.department,
            'Account Status': user.status,
            'Created At': user.created_at.strftime('%Y-%m-%d %H:%M:%S') if user.created_at else 'N/A',
            'Last Login': user.last_login.strftime('%Y-%m-%d %H:%M:%S') if user.last_login else 'Never',
            'Failed Attempts': user.failed_attempts,
            'Current Auth Score': f"{user.auth_score * 100:.2f}%" if user.auth_score else 'N/A',
            'Total Logins': len([l for l in logs if l.result == 'success']),
            'Failed Logins': len([l for l in logs if l.result == 'failed']),
            'Total Alerts': len(alerts),
            'Critical Alerts': len([a for a in alerts if a.severity == 'critical']),
            'Keystroke Samples': len(keystrokes),
            'Registered Devices': len(devices),
            'Model Trained': 'Yes' if model else 'No',
            'Model Version': model.model_version if model else 'N/A',
            'Model Accuracy': f"{model.accuracy * 100:.2f}%" if model and model.accuracy else 'N/A',
            'FAR': f"{model.far * 100:.2f}%" if model and model.far else 'N/A',
            'FRR': f"{model.frr * 100:.2f}%" if model and model.frr else 'N/A'
        }])

        # ===== SHEET 2: DETAILED AUTHENTICATION LOGS =====
        logs_df = pd.DataFrame([{
            'Timestamp': l.timestamp.strftime('%Y-%m-%d %H:%M:%S') if l.timestamp else 'N/A',
            'Date': l.timestamp.strftime('%Y-%m-%d') if l.timestamp else 'N/A',
            'Time': l.timestamp.strftime('%H:%M:%S') if l.timestamp else 'N/A',
            'Result': l.result.upper(),
            'Access Decision': 'GRANTED' if l.result == 'success' else 'DENIED',
            'Confidence Score': f"{l.confidence_score * 100:.2f}%" if l.confidence_score else 'N/A',
            'Confidence (Raw)': round(l.confidence_score, 4) if l.confidence_score else 0,
            'Threshold Met': 'Yes' if l.confidence_score and l.confidence_score >= 0.60 else 'No',
            'Risk Level': ('LOW' if l.confidence_score and l.confidence_score >= 0.70 else
                          'MEDIUM' if l.confidence_score and l.confidence_score >= 0.65 else
                          'HIGH' if l.confidence_score and l.confidence_score >= 0.60 else
                          'CRITICAL') if l.confidence_score else 'UNKNOWN',
            'Session ID': l.session_id if l.session_id else 'N/A',
            'IP Address': l.ip_address if l.ip_address else 'N/A',
            'User Agent': l.user_agent if l.user_agent else 'N/A'
        } for l in logs])

        # Keystrokes with features expanded
        keystroke_records = []
        for k in keystrokes:
            record = {
                'Timestamp': k.timestamp,
                'Session': k.session_id,
                'Data Split': k.data_split or 'live'
            }
            # Parse features if available
            if k.keystroke_features:
                try:
                    features = json.loads(k.keystroke_features)
                    if 'raw_features' in features:
                        for idx, val in enumerate(features['raw_features']):
                            record[f'Feature_{idx+1}'] = val
                except:
                    pass
            keystroke_records.append(record)

        kdf = pd.DataFrame(keystroke_records)

        # ===== SHEET 3: PERFORMANCE METRICS & MODEL COMPARISON =====
        if model and model.training_metadata:
            metadata = json.loads(model.training_metadata)
            if 'model_comparisons' in metadata:
                # Format model comparisons with best model indicator
                model_comparisons = []
                for comp in metadata['model_comparisons']:
                    model_comparisons.append({
                        'Algorithm': comp.get('algorithm', 'Unknown'),
                        'Accuracy': f"{comp.get('accuracy', 0):.2f}%",
                        'FAR (False Accept Rate)': f"{comp.get('far', 0):.2f}%",
                        'FRR (False Reject Rate)': f"{comp.get('frr', 0):.2f}%",
                        'EER (Equal Error Rate)': f"{comp.get('eer', 0):.2f}%",
                        'Training Samples': comp.get('train_samples', 0),
                        'Test Samples': comp.get('test_samples', 0),
                        'Selected as Best': ' YES' if comp.get('selected') else 'No',
                        'Rank': comp.get('rank', 'N/A')
                    })
                model_comp_df = pd.DataFrame(model_comparisons)
            else:
                model_comp_df = pd.DataFrame([{
                    'Algorithm': metadata.get('algorithm', 'Unknown'),
                    'Accuracy': f"{model.accuracy * 100:.2f}%" if model.accuracy else 'N/A',
                    'FAR (False Accept Rate)': f"{model.far * 100:.2f}%" if model.far else 'N/A',
                    'FRR (False Reject Rate)': f"{model.frr * 100:.2f}%" if model.frr else 'N/A',
                    'EER (Equal Error Rate)': f"{((model.far + model.frr) / 2) * 100:.2f}%" if model.far and model.frr else 'N/A',
                    'Selected as Best': ' YES',
                    'Note': 'Only one model trained'
                }])

            # Feature names
            if 'feature_names' in metadata:
                feature_df = pd.DataFrame({
                    'Feature Index': range(1, len(metadata['feature_names']) + 1),
                    'Feature Name': metadata['feature_names'],
                    'Category': ['Dwell Time' if i < 8 else 'Flight Time' if i < 16 else 'Pause Pattern'
                                for i in range(len(metadata['feature_names']))]
                })
            else:
                feature_df = pd.DataFrame({'Note': ['Feature names not available']})
        else:
            model_comp_df = pd.DataFrame({'Note': ['No trained model available']})
            feature_df = pd.DataFrame({'Note': ['No trained model available']})

        # ===== SHEET 4: SECURITY ALERTS =====
        alerts_df = pd.DataFrame([{
            'Timestamp': a.timestamp.strftime('%Y-%m-%d %H:%M:%S') if a.timestamp else 'N/A',
            'Severity': a.severity.upper(),
            'Type': a.alert_type,
            'Title': a.title,
            'Description': a.description,
            'Status': a.status.upper(),
            'Confidence Score': f"{a.confidence_score * 100:.2f}%" if a.confidence_score else 'N/A',
            'Resolved At': a.resolved_at.strftime('%Y-%m-%d %H:%M:%S') if a.resolved_at else 'Not Resolved',
            'Resolved By': a.resolved_by if a.resolved_by else 'N/A'
        } for a in alerts]) if alerts else pd.DataFrame({'Note': ['No alerts recorded']})

        # ===== SHEET 5: REGISTERED DEVICES =====
        devices_df = pd.DataFrame([{
            'Device Fingerprint': d.device_fingerprint,
            'Device Name': d.device_name,
            'Device Type': d.device_type,
            'Browser': d.browser,
            'OS': d.os,
            'First Seen': d.first_seen.strftime('%Y-%m-%d %H:%M:%S') if d.first_seen else 'N/A',
            'Last Seen': d.last_seen.strftime('%Y-%m-%d %H:%M:%S') if d.last_seen else 'N/A',
            'Trusted': 'Yes' if d.is_trusted else 'No',
            'Total Logins': len([l for l in logs if l.user_agent and d.device_name.lower() in l.user_agent.lower()])
        } for d in devices]) if devices else pd.DataFrame({'Note': ['No devices registered']})

        # ===== SHEET 6: KEYSTROKE SAMPLES (with features) =====
        # Keep existing keystroke_records logic
        kdf = pd.DataFrame(keystroke_records) if keystroke_records else pd.DataFrame({'Note': ['No keystroke data']})

        # Create Excel file with all sheets
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            summary_df.to_excel(writer, sheet_name="1_Forensic_Summary", index=False)
            logs_df.to_excel(writer, sheet_name="2_Authentication_Logs", index=False)
            model_comp_df.to_excel(writer, sheet_name="3_Model_Performance", index=False)
            alerts_df.to_excel(writer, sheet_name="4_Security_Alerts", index=False)
            devices_df.to_excel(writer, sheet_name="5_Devices", index=False)
            feature_df.to_excel(writer, sheet_name="6_Feature_Names", index=False)
            kdf.to_excel(writer, sheet_name="7_Keystroke_Data", index=False)

        output.seek(0)

        return send_file(
            output,
            as_attachment=True,
            download_name=f"user_{user_id}_analytics.xlsx",
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

