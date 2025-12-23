from flask import Blueprint, jsonify, request
from src.models.user import (
    User,
    UserDevice,
    AuthenticationLog,
    SecurityAlert,
    KeystrokeData,
    MLModel,
    db
)
from datetime import datetime, timedelta
from sqlalchemy import or_





user_bp = Blueprint("user", __name__)
#  GET ALL USERS (Supports filters + pagination + training stats)

@user_bp.route("/users", methods=["GET"])
def get_users():
    try:
        page = int(request.args.get("page", 1))
        per_page = int(request.args.get("per_page", 50))
        status = request.args.get("status", "all")
        role = request.args.get("role", "all")
        department = request.args.get("department", "all")
        search = request.args.get("search", "")

        query = User.query

        if status != "all":
            query = query.filter(User.status == status)

        if role != "all":
            query = query.filter(User.role == role)

        if department != "all":
            query = query.filter(User.department == department)

        if search:
            query = query.filter(
                or_(
                    User.name.contains(search),
                    User.email.contains(search),
                    User.department.contains(search),
                )
            )

        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        users_response = []

        for user in pagination.items:

            # active ML model
            active_model = MLModel.query.filter_by(
                user_id=user.id, is_active=True
            ).first()

            model_info = (
                {
                    "version": active_model.model_version,
                    "accuracy": active_model.accuracy,
                    "far": active_model.far,
                    "frr": active_model.frr,
                    "samples": active_model.training_data_count,
                }
                if active_model
                else None
            )

            users_response.append({
                **user.to_dict(),
                "training_samples": KeystrokeData.query.filter_by(
                    user_id=user.id, is_training_data=True
                ).count(),
                "total_keystrokes": KeystrokeData.query.filter_by(
                    user_id=user.id
                ).count(),
                "device_count": len(user.user_devices),
                "recent_alerts": SecurityAlert.query.filter_by(
                    user_id=user.id
                )
                .filter(SecurityAlert.timestamp >= datetime.utcnow() - timedelta(days=7))
                .count(),
                "active_model": model_info,
            })

        return jsonify({
            "users": users_response,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": pagination.total,
                "pages": pagination.pages,
                "has_next": pagination.has_next,
                "has_prev": pagination.has_prev,
            },
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# 
#  USER STATS FOR DASHBOARD
# 
@user_bp.route("/users/stats", methods=["GET"])
def get_user_stats():
    try:
        total_users = User.query.count()
        active_users = User.query.filter_by(status="active").count()
        locked_users = User.query.filter_by(status="locked").count()
        inactive_users = User.query.filter_by(status="inactive").count()

        week_ago = datetime.utcnow() - timedelta(days=7)
        new_users = User.query.filter(User.created_at >= week_ago).count()

        trained_profiles = MLModel.query.filter_by(is_active=True).count()

        return jsonify({
            "total_users": total_users,
            "active_users": active_users,
            "locked_users": locked_users,
            "inactive_users": inactive_users,
            "new_users_week": new_users,
            "trained_profiles": trained_profiles
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# =====================================================================
#  CREATE USER
# =====================================================================
@user_bp.route("/users", methods=["POST"])
def create_user():
    try:
        data = request.json
        required = ["name", "email", "role"]

        for field in required:
            if field not in data:
                return jsonify({"error": f"{field} is required"}), 400

        if User.query.filter_by(email=data["email"]).first():
            return jsonify({"error": "Email already exists"}), 409

        new_user = User(
            name=data["name"],
            email=data["email"],
            role=data.get("role", "User"),
            department=data.get("department"),
            status=data.get("status", "active")
        )

        db.session.add(new_user)
        db.session.commit()

        return jsonify({
            "message": "User created successfully",
            "user": new_user.to_dict()
        }), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# =====================================================================
#  GET USER DETAILS
# =====================================================================
@user_bp.route("/users/<int:user_id>", methods=["GET"])
def get_user(user_id):
    try:
        user = User.query.get_or_404(user_id)

        active_model = MLModel.query.filter_by(
            user_id=user_id, is_active=True
        ).first()

        details = {
            **user.to_dict(),
            "devices": [d.to_dict() for d in user.user_devices],
            "recent_logins": [
                log.to_dict() for log in AuthenticationLog.query.filter_by(user_id=user_id)
                .order_by(AuthenticationLog.timestamp.desc())
                .limit(10)
            ],
            "recent_alerts": [
                a.to_dict() for a in SecurityAlert.query.filter_by(user_id=user_id)
                .order_by(SecurityAlert.timestamp.desc())
                .limit(5)
            ],
            "active_model": active_model.to_dict() if active_model else None,
            "keystroke_samples": KeystrokeData.query.filter_by(user_id=user_id).count(),
        }

        return jsonify(details)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# =====================================================================
#  UPDATE USER
# =====================================================================
@user_bp.route("/users/<int:user_id>", methods=["PUT"])
def update_user(user_id):
    try:
        user = User.query.get_or_404(user_id)
        data = request.json

        if "email" in data:
            if data["email"] != user.email and User.query.filter_by(email=data["email"]).first():
                return jsonify({"error": "Email already exists"}), 409
            user.email = data["email"]

        if "name" in data:
            user.name = data["name"]

        if "role" in data:
            user.role = data["role"]

        if "department" in data:
            user.department = data["department"]

        if "status" in data:
            user.status = data["status"]
            if data["status"] == "active":
                user.failed_attempts = 0
                user.locked_until = None

        db.session.commit()

        return jsonify({"message": "User updated", "user": user.to_dict()})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# =====================================================================
#  DELETE USER
# =====================================================================
@user_bp.route("/users/<int:user_id>", methods=["DELETE"])
def delete_user(user_id):
    try:
        user = User.query.get_or_404(user_id)
        db.session.delete(user)
        db.session.commit()
        return jsonify({"message": "User deleted"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# =====================================================================
#  LOCK USER
# =====================================================================
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
            description=f"Locked by admin. Reason: {reason}",
            metadata={"minutes": minutes}
        )

        db.session.add(alert)
        db.session.commit()

        return jsonify({"message": "User locked", "user": user.to_dict()})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# =====================================================================
#  UNLOCK USER
# =====================================================================
@user_bp.route("/users/<int:user_id>/unlock", methods=["POST"])
def unlock_user(user_id):
    try:
        user = User.query.get_or_404(user_id)

        user.status = "active"
        user.failed_attempts = 0
        user.locked_until = None

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


# =====================================================================
#  RESET AUTHENTICATION PROFILE
# =====================================================================
@user_bp.route("/users/<int:user_id>/reset-auth", methods=["POST"])
def reset_auth(user_id):
    try:
        user = User.query.get_or_404(user_id)

        user.failed_attempts = 0
        user.auth_score = 0
        user.locked_until = None

        # Mark all keystrokes as not training
        KeystrokeData.query.filter_by(user_id=user_id).update({
            "is_training_data": False
        })

        # Deactivate all ML models
        MLModel.query.filter_by(user_id=user_id).update({"is_active": False})

        db.session.commit()

        return jsonify({"message": "Authentication reset", "user": user.to_dict()})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# =====================================================================
#  BULK USER ACTIONS
# =====================================================================
@user_bp.route("/users/bulk-action", methods=["POST"])
def bulk_user_action():
    try:
        data = request.json
        user_ids = data.get("user_ids", [])
        action = data.get("action")

        if not user_ids or not action:
            return jsonify({"error": "user_ids and action are required"}), 400

        users = User.query.filter(User.id.in_(user_ids)).all()
        affected = 0

        if action == "lock":
            for u in users:
                u.status = "locked"
                u.locked_until = datetime.utcnow() + timedelta(minutes=30)
                affected += 1

        elif action == "unlock":
            for u in users:
                u.status = "active"
                u.failed_attempts = 0
                u.locked_until = None
                affected += 1

        elif action == "deactivate":
            for u in users:
                u.status = "inactive"
                affected += 1

        elif action == "delete":
            for u in users:
                db.session.delete(u)
                affected += 1

        db.session.commit()

        return jsonify({"message": f"Bulk action '{action}' applied", "affected": affected})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# =====================================================================
#  EXPORT USERS
# =====================================================================
@user_bp.route("/users/export", methods=["GET"])
def export_users():
    try:
        include_sensitive = request.args.get("include_sensitive", "false").lower() == "true"

        users = User.query.all()
        data_out = []

        for user in users:
            u = user.to_dict()
            if not include_sensitive:
                u.pop("failed_attempts", None)
                u.pop("locked_until", None)
            data_out.append(u)

        return jsonify({
            "exported_at": datetime.utcnow().isoformat(),
            "total_users": len(data_out),
            "users": data_out
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500
