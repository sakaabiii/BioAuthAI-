from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import json

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=True)  # Hashed password
    role = db.Column(db.String(50), nullable=False, default='Employee')
    department = db.Column(db.String(100), nullable=True)
    status = db.Column(db.String(20), nullable=False, default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    failed_attempts = db.Column(db.Integer, default=0)
    locked_until = db.Column(db.DateTime, nullable=True)
    auth_score = db.Column(db.Float, default=0.0)
    
    # Relationships
    keystroke_data = db.relationship('KeystrokeData', backref='user', lazy=True, cascade='all, delete-orphan')
    authentication_logs = db.relationship('AuthenticationLog', backref='user', lazy=True, cascade='all, delete-orphan')
    user_devices = db.relationship('UserDevice', backref='user', lazy=True, cascade='all, delete-orphan')
    security_alerts = db.relationship('SecurityAlert', backref='user', lazy=True, cascade='all, delete-orphan')

    def set_password(self, password):
        """Hash and set the user's password"""
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')
    
    def check_password(self, password):
        """Verify the user's password against the stored hash"""
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.email}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'role': self.role,
            'department': self.department,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'failed_attempts': self.failed_attempts,
            'locked_until': self.locked_until.isoformat() if self.locked_until else None,
            'auth_score': self.auth_score,
            'device_count': len(self.user_devices)
        }

class KeystrokeData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    session_id = db.Column(db.String(100), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    keystroke_features = db.Column(db.Text, nullable=False)  # JSON string of features
    device_info = db.Column(db.Text, nullable=True)  # JSON string of device info
    is_training_data = db.Column(db.Boolean, default=True)
    anomaly_score = db.Column(db.Float, nullable=True)
    data_split = db.Column(db.String(20), nullable=True)  # 'train', 'validation', 'test'

    def __repr__(self):
        return f'<KeystrokeData {self.id} for User {self.user_id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'session_id': self.session_id,
            'timestamp': self.timestamp.isoformat(),
            'keystroke_features': json.loads(self.keystroke_features) if self.keystroke_features else {},
            'device_info': json.loads(self.device_info) if self.device_info else {},
            'is_training_data': bool(self.is_training_data),
            'anomaly_score': self.anomaly_score,
            'data_split': self.data_split
        }

class AuthenticationLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    result = db.Column(db.String(20), nullable=False)  # 'success', 'failed', 'anomaly'
    confidence_score = db.Column(db.Float, nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.Text, nullable=True)
    location = db.Column(db.String(100), nullable=True)
    device_fingerprint = db.Column(db.String(255), nullable=True)
    session_id = db.Column(db.String(100), nullable=True)
    action_taken = db.Column(db.String(100), nullable=True)  # 'none', 'mfa_required', 'session_locked', etc.

    def __repr__(self):
        return f'<AuthenticationLog {self.id} - {self.result}>'

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'timestamp': self.timestamp.isoformat(),
            'result': self.result,
            'confidence_score': self.confidence_score,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'location': self.location,
            'device_fingerprint': self.device_fingerprint,
            'session_id': self.session_id,
            'action_taken': self.action_taken
        }

class UserDevice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    device_fingerprint = db.Column(db.String(255), nullable=False)
    device_name = db.Column(db.String(100), nullable=True)
    device_type = db.Column(db.String(50), nullable=True)  
    browser = db.Column(db.String(100), nullable=True)
    os = db.Column(db.String(100), nullable=True)
    first_seen = db.Column(db.DateTime, default=datetime.utcnow)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    is_trusted = db.Column(db.Boolean, default=False)
    status = db.Column(db.String(20), default='active')  # 'active', 'blocked'

    def __repr__(self):
        return f'<UserDevice {self.device_name} for User {self.user_id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'device_fingerprint': self.device_fingerprint,
            'device_name': self.device_name,
            'device_type': self.device_type,
            'browser': self.browser,
            'os': self.os,
            'first_seen': self.first_seen.isoformat(),
            'last_seen': self.last_seen.isoformat(),
            'is_trusted': bool(self.is_trusted),
            'status': self.status
        }

class SecurityAlert(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    alert_type = db.Column(db.String(50), nullable=False)  # 'anomaly', 'failed_auth', 'new_device', etc.
    severity = db.Column(db.String(20), nullable=False)  # 'low', 'medium', 'high', 'critical'
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='open')  # 'open', 'investigating', 'resolved', 'false_positive'
    confidence_score = db.Column(db.Float, nullable=True)
    alert_metadata = db.Column(db.Text, nullable=True)  # JSON string for additional data
    resolved_at = db.Column(db.DateTime, nullable=True)
    resolved_by = db.Column(db.String(100), nullable=True)

    def __repr__(self):
        return f'<SecurityAlert {self.id} - {self.title}>'

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'alert_type': self.alert_type,
            'severity': self.severity,
            'title': self.title,
            'description': self.description,
            'timestamp': self.timestamp.isoformat(),
            'status': self.status,
            'confidence_score': self.confidence_score,
            'metadata': json.loads(self.alert_metadata) if self.alert_metadata else {},
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'resolved_by': self.resolved_by
        }

class SystemSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=False)
    data_type = db.Column(db.String(20), nullable=False)  # 'string', 'integer', 'float', 'boolean', 'json'
    description = db.Column(db.Text, nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = db.Column(db.String(100), nullable=True)

    def __repr__(self):
        return f'<SystemSettings {self.key}>'

    def to_dict(self):
        return {
            'id': self.id,
            'key': self.key,
            'value': self.get_typed_value(),
            'data_type': self.data_type,
            'description': self.description,
            'updated_at': self.updated_at.isoformat(),
            'updated_by': self.updated_by
        }

    def get_typed_value(self):
        """Convert the stored string value to its proper type"""
        if self.data_type == 'integer':
            return int(self.value)
        elif self.data_type == 'float':
            return float(self.value)
        elif self.data_type == 'boolean':
            return self.value.lower() == 'true'
        elif self.data_type == 'json':
            return json.loads(self.value)
        else:
            return self.value

class MLModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    model_version = db.Column(db.String(50), nullable=False)
    model_data = db.Column(db.LargeBinary, nullable=False)  # Serialized model
    training_data_count = db.Column(db.Integer, nullable=False)
    accuracy = db.Column(db.Float, nullable=True)
    far = db.Column(db.Float, nullable=True)  # False Accept Rate
    frr = db.Column(db.Float, nullable=True)  # False Reject Rate
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    training_metadata = db.Column(db.Text, nullable=True)  # JSON string

    def __repr__(self):
        return f'<MLModel {self.model_version} for User {self.user_id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'model_version': self.model_version,
            'training_data_count': self.training_data_count,
            'accuracy': self.accuracy,
            'far': self.far,
            'frr': self.frr,
            'created_at': self.created_at.isoformat(),
            'is_active': bool(self.is_active),  # Convert SQLAlchemy Boolean to Python bool
            'training_metadata': json.loads(self.training_metadata) if self.training_metadata else {}
        }

