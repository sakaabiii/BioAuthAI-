# ================================================================
#  BioAuthAI — Dataset Import / Export / Stats Module
# Stores RAW keystroke data (dwell_times, flight_times, etc.)
# Feature extraction happens during ML training for flexibility
# Author: Sharifa Al-Kaabi ️
# ================================================================

from flask import Blueprint, request, jsonify
from src.models.user import db, User, KeystrokeData
from src.utils.feature_extractor import extract_features  #  NEW FEATURE ENGINE
from datetime import datetime
import json
import csv
import io

dataset_bp = Blueprint('dataset', __name__)


# ================================================================
# 1. IMPORT DATASET (CSV) — AUTO FEATURE EXTRACTION
# ================================================================
@dataset_bp.route('/dataset/import', methods=['POST'])
def import_dataset():
    """
    Import keystroke dataset and store raw keystroke data.
    Supported CSV formats:
        A) Aggregated:
           user_email, dwell_times, flight_times, pause_patterns, typing_speed

        B) Raw single key lines:
           user_email, key, dwell_time, flight_time, timestamp

    Stores raw keystroke data (not extracted features).
    Feature extraction happens during ML training for maximum flexibility.
    """

    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']
        if not file.filename.endswith('.csv'):
            return jsonify({'error': 'Only CSV files are supported'}), 400

        # Read CSV content
        stream = io.StringIO(file.stream.read().decode("UTF-8"))
        csv_reader = csv.DictReader(stream)

        imported = 0
        errors = []

        for row_num, row in enumerate(csv_reader, start=2):
            try:
                # ------------------------------------------------------------
                # 1️⃣ Lookup user
                # ------------------------------------------------------------
                user = None
                if "user_email" in row:
                    user = User.query.filter_by(email=row["user_email"]).first()
                elif "user_id" in row:
                    user = User.query.get(int(row["user_id"]))

                if not user:
                    errors.append(f"Row {row_num}: User not found")
                    continue

                # ------------------------------------------------------------
                # 2️⃣ Parse keystroke raw data
                # ------------------------------------------------------------
                if "dwell_times" in row:
                    # Aggregated CSV with JSON arrays
                    raw_k = {
                        "dwell_times": json.loads(row["dwell_times"]),
                        "flight_times": json.loads(row.get("flight_times", "[]")),
                        "pause_patterns": json.loads(row.get("pause_patterns", "[]")),
                        "typing_speed": float(row.get("typing_speed", 0.0)),
                        "total_keys": len(json.loads(row["dwell_times"])),
                    }

                elif "dwell_time" in row:
                    # Individual key rows (rare case)
                    raw_k = {
                        "dwell_times": [float(row.get("dwell_time", 0))],
                        "flight_times": [float(row.get("flight_time", 0))],
                        "pause_patterns": [],
                        "typing_speed": 0,
                        "total_keys": 1,
                    }

                else:
                    errors.append(f"Row {row_num}: No keystroke fields found")
                    continue

                # ------------------------------------------------------------
                # 3️⃣ Validate raw keystroke data (feature extraction happens during training)
                # ------------------------------------------------------------
                # Quick validation that extract_features will work later
                test_features = extract_features(raw_k)
                if test_features is None:
                    errors.append(f"Row {row_num}: Invalid keystroke data format")
                    continue

                # ------------------------------------------------------------
                # 4️⃣ Save RAW keystroke data to database (NOT extracted features)
                # ------------------------------------------------------------
                keystroke = KeystrokeData(
                    user_id=user.id,
                    session_id=row.get("session_id", f"import_{datetime.utcnow().timestamp()}"),
                    keystroke_features=json.dumps(raw_k),   # STORE RAW DATA, extract features during training
                    device_info=json.dumps({
                        "source": "csv_import",
                        "imported_at": datetime.utcnow().isoformat()
                    }),
                    is_training_data=True,
                    anomaly_score=None,
                )

                db.session.add(keystroke)
                imported += 1

            except Exception as e:
                errors.append(f"Row {row_num}: {str(e)}")

        db.session.commit()

        return jsonify({
            "message": "Dataset imported successfully",
            "imported_rows": imported,
            "errors": errors[:10],   # Show only first 10 errors
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500



# ================================================================
# 2. EXPORT DATASET (Raw Keystroke Data)
# ================================================================
@dataset_bp.route('/dataset/export', methods=['GET'])
def export_dataset():
    """
    Export dataset with raw keystroke data (dwell_times, flight_times, etc.).
    """
    try:
        user_id = request.args.get("user_id", type=int)
        include_training = request.args.get("include_training", "true").lower() == "true"

        query = KeystrokeData.query
        if user_id:
            query = query.filter_by(user_id=user_id)
        if include_training:
            query = query.filter_by(is_training_data=True)

        records = query.all()

        # Prepare CSV
        output = io.StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow([
            "user_id", "email", "session_id", "timestamp",
            "features_json", "is_training"
        ])

        for rec in records:
            user = User.query.get(rec.user_id)
            writer.writerow([
                rec.user_id,
                user.email if user else "",
                rec.session_id,
                rec.timestamp.isoformat(),
                rec.keystroke_features,
                rec.is_training_data,
            ])

        output.seek(0)

        return output.getvalue(), 200, {
            "Content-Type": "text/csv",
            "Content-Disposition": f'attachment; filename=bioauthai_features_{datetime.utcnow().strftime("%Y%m%d")}.csv'
        }

    except Exception as e:
        return jsonify({"error": str(e)}), 500



# ================================================================
# 3. DATASET STATS
# ================================================================
@dataset_bp.route('/dataset/stats', methods=['GET'])
def dataset_stats():
    """Return dataset summary with sample counts per user."""
    try:
        total = KeystrokeData.query.count()
        training = KeystrokeData.query.filter_by(is_training_data=True).count()

        users = (
            db.session.query(
                User.id,
                User.email,
                db.func.count(KeystrokeData.id).label("samples")
            )
            .join(KeystrokeData)
            .group_by(User.id)
            .all()
        )

        per_user = []
        for u in users:
            per_user.append({
                "user_id": u.id,
                "email": u.email,
                "samples": u.samples,
            })

        return jsonify({
            "total_samples": total,
            "training_samples": training,
            "users_with_data": len(per_user),
            "user_stats": per_user
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500



# ================================================================
# 4. CLEAR DATASET
# ================================================================
@dataset_bp.route('/dataset/clear', methods=['POST'])
def clear_dataset():
    """
    Deletes either:
    - All training data
    - Only a specific user’s data
    """
    try:
        data = request.get_json()
        user_id = data.get("user_id")
        confirm = data.get("confirm", False)

        if not confirm:
            return jsonify({"error": "Confirmation required"}), 400

        if user_id:
            deleted = KeystrokeData.query.filter_by(user_id=user_id).delete()
        else:
            deleted = KeystrokeData.query.delete()

        db.session.commit()
        return jsonify({"message": "Dataset cleared", "deleted": deleted})

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
