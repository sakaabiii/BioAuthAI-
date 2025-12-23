from flask import Blueprint, request, jsonify
from src.models.user import db, SecurityAlert, User
from datetime import datetime
import json

alerts_bp = Blueprint('alerts', __name__)

@alerts_bp.route('/alerts', methods=['GET'])
def get_alerts():
    """Get security alerts with filtering"""
    try:
        # Query parameters
        status = request.args.get('status', 'all')
        severity = request.args.get('severity', 'all')
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        
        # Build query
        query = SecurityAlert.query
        
        if status != 'all':
            query = query.filter(SecurityAlert.status == status)
        
        if severity != 'all':
            query = query.filter(SecurityAlert.severity == severity)
        
        # Get alerts with pagination
        alerts = query.order_by(SecurityAlert.timestamp.desc()).offset(offset).limit(limit).all()
        total_count = query.count()
        
        # Convert to dict and include user info
        alerts_data = []
        for alert in alerts:
            alert_dict = alert.to_dict()
            if alert.user_id:
                user = User.query.get(alert.user_id)
                alert_dict['user'] = user.to_dict() if user else None
            alerts_data.append(alert_dict)
        
        return jsonify({
            'alerts': alerts_data,
            'total_count': total_count,
            'has_more': (offset + limit) < total_count
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@alerts_bp.route('/alerts/stats', methods=['GET'])
def get_alert_stats():
    """Get alert statistics"""
    try:
        stats = {
            'total': SecurityAlert.query.count(),
            'open': SecurityAlert.query.filter_by(status='open').count(),
            'investigating': SecurityAlert.query.filter_by(status='investigating').count(),
            'resolved': SecurityAlert.query.filter_by(status='resolved').count(),
            'critical': SecurityAlert.query.filter_by(severity='critical').count(),
            'high': SecurityAlert.query.filter_by(severity='high').count(),
            'medium': SecurityAlert.query.filter_by(severity='medium').count(),
            'low': SecurityAlert.query.filter_by(severity='low').count(),
            'impersonation': SecurityAlert.query.filter(SecurityAlert.title.like('%IMPERSONATION%')).count()
        }

        return jsonify(stats)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@alerts_bp.route('/alerts/<int:alert_id>', methods=['GET'])
def get_alert(alert_id):
    """Get specific alert details"""
    try:
        alert = SecurityAlert.query.get_or_404(alert_id)
        alert_dict = alert.to_dict()
        
        if alert.user_id:
            user = User.query.get(alert.user_id)
            alert_dict['user'] = user.to_dict() if user else None
        
        return jsonify(alert_dict)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@alerts_bp.route('/alerts/<int:alert_id>/status', methods=['PUT'])
def update_alert_status(alert_id):
    """Update alert status"""
    try:
        data = request.get_json()
        new_status = data.get('status')
        resolved_by = data.get('resolved_by', 'System')
        
        if new_status not in ['open', 'investigating', 'resolved', 'false_positive']:
            return jsonify({'error': 'Invalid status'}), 400
        
        alert = SecurityAlert.query.get_or_404(alert_id)
        alert.status = new_status
        
        if new_status in ['resolved', 'false_positive']:
            alert.resolved_at = datetime.utcnow()
            alert.resolved_by = resolved_by
        
        db.session.commit()
        
        return jsonify({
            'message': 'Alert status updated successfully',
            'alert': alert.to_dict()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@alerts_bp.route('/alerts', methods=['POST'])
def create_alert():
    """Create a new security alert"""
    try:
        data = request.get_json()
        
        alert = SecurityAlert(
            user_id=data.get('user_id'),
            alert_type=data.get('alert_type'),
            severity=data.get('severity'),
            title=data.get('title'),
            description=data.get('description'),
            confidence_score=data.get('confidence_score'),
            alert_metadata=json.dumps(data.get('metadata', {}))
        )
        
        db.session.add(alert)
        db.session.commit()
        
        return jsonify({
            'message': 'Alert created successfully',
            'alert': alert.to_dict()
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@alerts_bp.route('/alerts/bulk-action', methods=['POST'])
def bulk_alert_action():
    """Perform bulk actions on alerts"""
    try:
        data = request.get_json()
        alert_ids = data.get('alert_ids', [])
        action = data.get('action')
        
        if not alert_ids or not action:
            return jsonify({'error': 'Alert IDs and action are required'}), 400
        
        alerts = SecurityAlert.query.filter(SecurityAlert.id.in_(alert_ids)).all()
        
        if action == 'resolve':
            for alert in alerts:
                alert.status = 'resolved'
                alert.resolved_at = datetime.utcnow()
                alert.resolved_by = 'Bulk Action'
        elif action == 'investigate':
            for alert in alerts:
                alert.status = 'investigating'
        elif action == 'delete':
            for alert in alerts:
                db.session.delete(alert)
        
        db.session.commit()
        
        return jsonify({
            'message': f'Bulk action "{action}" completed successfully',
            'affected_count': len(alerts)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

