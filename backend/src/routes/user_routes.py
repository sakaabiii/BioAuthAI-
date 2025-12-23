from flask import Blueprint, json, jsonify, request
from datetime import datetime, timedelta
from sqlalchemy import or_

from src.models.user import (
    db,
    User,
    UserDevice,
    SecurityAlert,
    AuthenticationLog,
    KeystrokeData,
    MLModel
)

user_bp = Blueprint("user", __name__)

# =================================================================
#  1) GET ALL USERS (Dashboard)
# =================================================================
@user_bp.route("/users", methods=["GET"])
def get_users():
    try:
        page = int(request.args.get("page", 1))
        per_page = int(request.args.get("per_page", 50))
        search = request.args.get("search", "")
        status = request.args.get("status", "all")
        role = request.args.get("role", "all")
        department = request.args.get("department", "all")

        query = User.query

        if search:
            query = query.filter(
                or_(
                    User.name.contains(search),
                    User.email.contains(search),
                    User.department.contains(search)
                )
            )

        if status != "all":
            query = query.filter(User.status == status)

        if role != "all":
            query = query.filter(User.role == role)

        if department != "all":
            query = query.filter(User.department == department)

        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        users_list = []
        for u in pagination.items:

            model = MLModel.query.filter_by(user_id=u.id, is_active=True).first()
            training_samples = KeystrokeData.query.filter_by(
                user_id=u.id, is_training_data=True
            ).count()

            users_list.append({
                **u.to_dict(),
                "training_samples": training_samples,
                "total_keystrokes": KeystrokeData.query.filter_by(user_id=u.id).count(),
                "active_model": model.to_dict() if model else None,
                "recent_alerts": SecurityAlert.query.filter_by(user_id=u.id)
                    .filter(SecurityAlert.timestamp >= datetime.utcnow() - timedelta(days=7))
                    .count()
            })

        return jsonify({
            "users": users_list,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": pagination.total,
                "pages": pagination.pages,
                "has_next": pagination.has_next,
                "has_prev": pagination.has_prev,
            }
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# =================================================================
#  2) USER STATISTICS (Dashboard Cards)
# =================================================================
@user_bp.route("/users/stats", methods=["GET"])
def get_user_stats():
    try:
        total = User.query.count()
        active = User.query.filter_by(status="active").count()
        locked = User.query.filter_by(status="locked").count()
        inactive = User.query.filter_by(status="inactive").count()

        week_ago = datetime.utcnow() - timedelta(days=7)
        new_users = User.query.filter(User.created_at >= week_ago).count()

        trained_profiles = MLModel.query.filter_by(is_active=True).count()

        return jsonify({
            "total_users": total,
            "active_users": active,
            "locked_users": locked,
            "inactive_users": inactive,
            "new_users_week": new_users,
            "trained_profiles": trained_profiles
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# =================================================================
#  3) CREATE USER
# =================================================================
@user_bp.route("/users", methods=["POST"])
def create_user():
    try:
        data = request.json
        required = ["name", "email", "role"]

        for r in required:
            if r not in data:
                return jsonify({"error": f"{r} is required"}), 400

        if User.query.filter_by(email=data["email"]).first():
            return jsonify({"error": "Email already exists"}), 409

        user = User(
            name=data["name"],
            email=data["email"],
            role=data.get("role", "Employee"),
            department=data.get("department"),
            status=data.get("status", "active")
        )

        db.session.add(user)
        db.session.commit()

        return jsonify({"message": "User created", "user": user.to_dict()}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# =================================================================
#  4) GET USER DETAILS (User Page)
# =================================================================
@user_bp.route("/users/<int:user_id>", methods=["GET"])
def get_user_details(user_id):
    try:
        user = User.query.get_or_404(user_id)

        model = MLModel.query.filter_by(user_id=user_id, is_active=True).first()

        return jsonify({
            **user.to_dict(),
            "devices": [d.to_dict() for d in user.user_devices],
            "recent_logins": [
                l.to_dict()
                for l in AuthenticationLog.query.filter_by(user_id=user_id)
                    .order_by(AuthenticationLog.timestamp.desc())
                    .limit(10).all()
            ],
            "recent_alerts": [
                a.to_dict()
                for a in SecurityAlert.query.filter_by(user_id=user_id)
                    .order_by(SecurityAlert.timestamp.desc())
                    .limit(5).all()
            ],
            "active_model": model.to_dict() if model else None,
            "keystroke_samples": KeystrokeData.query.filter_by(user_id=user_id).count()
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# =================================================================
#  5) UPDATE USER
# =================================================================
@user_bp.route("/users/<int:user_id>", methods=["PUT"])
def update_user(user_id):
    try:
        user = User.query.get_or_404(user_id)
        data = request.json

        if "email" in data and data["email"] != user.email:
            if User.query.filter_by(email=data["email"]).first():
                return jsonify({"error": "Email already exists"}), 409
            user.email = data["email"]

        user.name = data.get("name", user.name)
        user.role = data.get("role", user.role)
        user.department = data.get("department", user.department)

        if "status" in data:
            user.status = data["status"]
            if data["status"] == "active":
                user.failed_attempts = 0
                user.locked_until = None

        db.session.commit()

        return jsonify({"message": "User updated", "user": user.to_dict()})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# =================================================================
#  6) DELETE USER
# =================================================================
@user_bp.route("/users/<int:user_id>", methods=["DELETE"])
def delete_user(user_id):
    try:
        user = User.query.get_or_404(user_id)
        db.session.delete(user)
        db.session.commit()
        return jsonify({"message": "User deleted"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# =================================================================
#  7) LOCK USER
# =================================================================
@user_bp.route("/users/<int:user_id>/lock", methods=["POST"])
def lock_user(user_id):
    try:
        user = User.query.get_or_404(user_id)
        data = request.json or {}

        minutes = data.get("duration_minutes", 30)
        reason = data.get("reason", "Manual lock")

        user.status = "locked"
        user.locked_until = datetime.utcnow() + timedelta(minutes=minutes)

        alert = SecurityAlert(
            user_id=user_id,
            alert_type="account_locked",
            severity="medium",
            title="Account Locked",
            description=f"Account locked. Reason: {reason}",
            alert_metadata=json.dumps({"minutes": minutes}),
        )

        db.session.add(alert)
        db.session.commit()

        return jsonify({"message": "User locked", "user": user.to_dict()})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# =================================================================
#  8) UNLOCK USER
# =================================================================
@user_bp.route("/users/<int:user_id>/unlock", methods=["POST"])
def unlock_user(user_id):
    try:
        user = User.query.get_or_404(user_id)

        user.status = "active"
        user.locked_until = None
        user.failed_attempts = 0

        alert = SecurityAlert(
            user_id=user_id,
            alert_type="account_unlocked",
            severity="low",
            title="Account Unlocked",
            description="Unlocked by admin"
        )

        db.session.add(alert)
        db.session.commit()

        return jsonify({"message": "User unlocked", "user": user.to_dict()})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# =================================================================
#  9) RESET AUTH + KEYSTROKES + MODELS
# =================================================================
@user_bp.route("/users/<int:user_id>/reset-auth", methods=["POST"])
def reset_user_auth(user_id):
    try:
        user = User.query.get_or_404(user_id)

        user.failed_attempts = 0
        user.locked_until = None
        user.auth_score = 0

        KeystrokeData.query.filter_by(user_id=user_id).update(
            {"is_training_data": False}
        )

        MLModel.query.filter_by(user_id=user_id).update(
            {"is_active": False}
        )

        db.session.commit()

        return jsonify({"message": "Auth profile reset", "user": user.to_dict()})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# =================================================================
#  10) BULK ACTIONS
# =================================================================
@user_bp.route("/users/bulk-action", methods=["POST"])
def bulk_actions():
    try:
        data = request.json
        user_ids = data.get("user_ids", [])
        action = data.get("action")

        if not user_ids or not action:
            return jsonify({"error": "Missing user_ids or action"}), 400

        users = User.query.filter(User.id.in_(user_ids)).all()

        count = 0
        for u in users:
            if action == "lock":
                u.status = "locked"
                u.locked_until = datetime.utcnow() + timedelta(minutes=30)
            elif action == "unlock":
                u.status = "active"
                u.locked_until = None
                u.failed_attempts = 0
            elif action == "deactivate":
                u.status = "inactive"
            elif action == "delete":
                db.session.delete(u)

            count += 1

        db.session.commit()

        return jsonify({"message": f"Bulk action '{action}' applied", "affected": count})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# =================================================================
#  11) EXPORT USERS
# =================================================================
@user_bp.route("/users/export", methods=["GET"])
def export_users():
    try:
        include_sensitive = request.args.get("include_sensitive", "false") == "true"

        users = User.query.all()
        export = []

        for u in users:
            d = u.to_dict()
            if not include_sensitive:
                d.pop("failed_attempts", None)
                d.pop("locked_until", None)
            export.append(d)

        return jsonify({
            "exported_at": datetime.utcnow().isoformat(),
            "total_users": len(export),
            "users": export
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500
