# ======================================================================
#  BioAuthAI — ML TRAINING PIPELINE (Authentication-Oriented)
# Works with 21-feature extractor
# Evaluates 5 algorithms (matching Colab):
#   - RandomForest
#   - GradientBoosting
#   - OneClass SVM
#   - Isolation Forest
#   - MLP Classifier
#
# Stores best model + scaler into MLModel table
# ======================================================================

from flask import Blueprint, jsonify, request
from datetime import datetime
import numpy as np
import json
import pickle

from sklearn.svm import OneClassSVM
from sklearn.ensemble import IsolationForest, RandomForestClassifier, GradientBoostingClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from src.models.user import db, User, KeystrokeData, MLModel
from src.utils.feature_extractor import extract_features


ml_bp = Blueprint("ml_training", __name__)



#  METRIC CALCULATIONS (WITH CROSS-USER IMPOSTOR TESTING)

def compute_metrics(model, X_test, X_train, user_id):
    """
    Realistic evaluation using OTHER USERS as impostors.

    Args:
        model: Trained sklearn model (OneClassSVM, IsolationForest, or MLPClassifier)
        X_test: Test samples from the genuine user (numpy array)
        X_train: Training samples from the genuine user (numpy array)
        user_id: ID of the user being evaluated

    Returns:
        tuple: (accuracy, far, frr, confusion_matrix_dict)
            - accuracy: Overall classification accuracy (0.0-1.0)
            - far: False Accept Rate - impostors incorrectly accepted (0.0-1.0)
            - frr: False Reject Rate - genuine users incorrectly rejected (0.0-1.0)
            - confusion_matrix_dict: {"TP": int, "FN": int, "FP": int, "TN": int}

    Process:
        1. Test on genuine samples (from same user)
        2. Use samples from different users as impostors (cross-user testing)
        3. Calculate TP, FN, FP, TN for realistic FAR/FRR
    """
    # Test on genuine samples
    raw_genuine = model.predict(X_test)
    pred_genuine = np.where(raw_genuine == 1, 1, 0)

    tp = int(np.sum(pred_genuine == 1))  # Genuine accepted
    fn = int(np.sum(pred_genuine == 0))  # Genuine rejected (False Reject)

    # Get impostor samples from OTHER users (cross-user testing)
    # Use 2x genuine test samples for realistic evaluation (matching Colab approach)
    impostor_count = max(20, len(X_test) * 2)

    # Query more users for better impostor representation
    other_users = User.query.filter(User.id != user_id).limit(20).all()
    X_impostor_list = []

    for other_user in other_users:
        # Get test samples from this other user to use as impostors
        samples = KeystrokeData.query.filter_by(
            user_id=other_user.id,
            data_split='test'
        ).limit(impostor_count // len(other_users) + 1).all()

        for s in samples:
            if len(X_impostor_list) >= impostor_count:
                break
            feat_dict = json.loads(s.keystroke_features)
            fv = extract_features(feat_dict)
            if fv:
                X_impostor_list.append(fv)

        if len(X_impostor_list) >= impostor_count:
            break

    # Convert to numpy array
    if len(X_impostor_list) < 5:
        # Fallback: not enough other users, use simulated
        print(f"WARNING: Not enough impostor data for user {user_id}, using simulation")
        X_impostor = np.random.normal(X_test.mean(axis=0), X_test.std(axis=0), (impostor_count, X_test.shape[1]))
    else:
        X_impostor = np.array(X_impostor_list[:impostor_count], dtype=np.float32)

    # Test on impostor samples
    raw_impostor = model.predict(X_impostor)
    pred_impostor = np.where(raw_impostor == 1, 1, 0)

    fp = int(np.sum(pred_impostor == 1))  # Impostor accepted (False Accept - BAD!)
    tn = int(np.sum(pred_impostor == 0))  # Impostor rejected (True Negative - GOOD!)

    # Calculate metrics
    total = tp + fn + fp + tn
    accuracy = (tp + tn) / total if total else 0
    frr = fn / (tp + fn) if (tp + fn) else 0
    far = fp / (fp + tn) if (fp + tn) else 0

    return accuracy, far, frr, {"TP": tp, "FN": fn, "FP": fp, "TN": tn}



# ======================================================================
#  TRAIN USER MODEL (Uses data_split if available)
# ======================================================================
def train_user_model(user_id):
    """
    Train machine learning models for a specific user's keystroke biometrics.

    Args:
        user_id (int): Database ID of the user to train models for

    Returns:
        tuple: (result_dict, error_message)
            - result_dict: Success dictionary with model info and metrics, or None if error
            - error_message: Error string if failed, or None if successful

    Process:
        1. Load keystroke data (uses data_split field if available, else manual split)
        2. Extract 21 features from each sample
        3. Train 3 different algorithms (OneClassSVM, IsolationForest, MLPClassifier)
        4. Evaluate each model using cross-user impostor testing
        5. Select best model based on accuracy
        6. Store model in database with metadata

    Models Trained:
        - OneClassSVM: One-class classifier, learns boundary of genuine behavior
        - IsolationForest: Anomaly detector using random forest approach
        - MLPClassifier: Neural network trained with genuine + simulated impostor samples

    Evaluation:
        - Uses OTHER users' keystroke data as realistic impostor samples
        - Calculates Accuracy, FAR (False Accept Rate), FRR (False Reject Rate)
        - Generates confusion matrix (TP, FN, FP, TN)
    """

    # load samples using data_split field (for dataset users)
    train_samples = KeystrokeData.query.filter_by(
        user_id=user_id, data_split='train'
    ).all()

    test_samples = KeystrokeData.query.filter_by(
        user_id=user_id, data_split='test'
    ).all()

    # If no split data (e.g., Sharifa's live data), use all training data
    if not train_samples:
        all_samples = KeystrokeData.query.filter_by(
            user_id=user_id, is_training_data=True
        ).all()

        if len(all_samples) < 10:
            return None, f"User {user_id} needs at least 10 training samples."

        # Extract features from all samples
        X = []
        for s in all_samples:
            feat_dict = json.loads(s.keystroke_features)
            fv = extract_features(feat_dict)
            if fv:
                X.append(fv)

        X = np.array(X, dtype=np.float32)

        if X.shape[0] < 10:
            return None, "Not enough valid feature vectors."

        # Train/test split 
        X_train, X_test = train_test_split(
            X, test_size=0.3, random_state=42
        )
    else:
        # Use pre-split data
        X_train = []
        for s in train_samples:
            feat_dict = json.loads(s.keystroke_features)
            fv = extract_features(feat_dict)
            if fv:
                X_train.append(fv)

        X_train = np.array(X_train, dtype=np.float32)

        if len(X_train) < 10:
            return None, f"User {user_id} needs at least 10 training samples."

        # Use test split if available, otherwise use validation
        if test_samples:
            X_test = []
            for s in test_samples:
                feat_dict = json.loads(s.keystroke_features)
                fv = extract_features(feat_dict)
                if fv:
                    X_test.append(fv)
            X_test = np.array(X_test, dtype=np.float32)
        else:
            # Fallback: use 30% of training data as test
            X_train, X_test = train_test_split(
                X_train, test_size=0.3, random_state=42
            )


    # NORMALIZE FEATURES (Critical for SVM, MLP, and better accuracy)

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    results = []

    # Prepare impostor samples for supervised learning (RF, GB)
    
    X_train_impostor_list = []  # Initialize here to avoid undefined variable warnings
    try:
        # Get impostor samples for training (not just evaluation)
        impostor_train_count = len(X_train_scaled) // 2

        # Collect impostor training samples from other users
        other_users_train = User.query.filter(User.id != user_id).limit(15).all()

        for other_user in other_users_train:
            samples = KeystrokeData.query.filter_by(
                user_id=other_user.id,
                data_split='train'
            ).limit(impostor_train_count // len(other_users_train) + 1).all()

            for s in samples:
                if len(X_train_impostor_list) >= impostor_train_count:
                    break
                feat_dict = json.loads(s.keystroke_features)
                fv = extract_features(feat_dict)
                if fv:
                    X_train_impostor_list.append(fv)

            if len(X_train_impostor_list) >= impostor_train_count:
                break
    except Exception as e:
        print(f"Error collecting impostor samples: {e}")

   
    # RandomForest 
 
    try:
        # If we have enough impostor data, train RandomForest
        if len(X_train_impostor_list) >= 10:
            X_train_impostor = np.array(X_train_impostor_list, dtype=np.float32)
            X_train_impostor_scaled = scaler.transform(X_train_impostor)

            # Combine genuine + impostor for supervised learning
            X_rf_train = np.vstack([X_train_scaled, X_train_impostor_scaled])
            y_rf_train = np.concatenate([
                np.ones(len(X_train_scaled)),      # Genuine = 1
                np.zeros(len(X_train_impostor_scaled))  # Impostor = 0
            ])

            rf = RandomForestClassifier(n_estimators=300, max_depth=25, random_state=42)
            rf.fit(X_rf_train, y_rf_train)

            # Evaluate (compute_metrics will handle test impostor samples)
            acc, far, frr, mat = compute_metrics(rf, X_test_scaled, X_train_scaled, user_id)
            results.append(("RandomForest", rf, acc, far, frr, mat))
            print(f"✓ RandomForest trained: Acc={acc:.4f}, FAR={far:.4f}, FRR={frr:.4f}")
        else:
            print("Not enough impostor data for RandomForest, skipping")
    except Exception as e:
        print(f"RandomForest ERROR: {e}")

    
    # GradientBoosting (supervised learning)
    try:
        # Reuse impostor samples from RandomForest if available
        if len(X_train_impostor_list) >= 10:
            X_train_impostor = np.array(X_train_impostor_list, dtype=np.float32)
            X_train_impostor_scaled = scaler.transform(X_train_impostor)

            X_gb_train = np.vstack([X_train_scaled, X_train_impostor_scaled])
            y_gb_train = np.concatenate([
                np.ones(len(X_train_scaled)),
                np.zeros(len(X_train_impostor_scaled))
            ])

            gb = GradientBoostingClassifier(random_state=42)
            gb.fit(X_gb_train, y_gb_train)

            acc, far, frr, mat = compute_metrics(gb, X_test_scaled, X_train_scaled, user_id)
            results.append(("GradientBoosting", gb, acc, far, frr, mat))
            print(f"✓ GradientBoosting trained: Acc={acc:.4f}, FAR={far:.4f}, FRR={frr:.4f}")
        else:
            print("Not enough impostor data for GradientBoosting, skipping")
    except Exception as e:
        print(f"GradientBoosting ERROR: {e}")

   
    # One-Class SVM (with scaling for better performance)

    try:
        svm = OneClassSVM(kernel="rbf", gamma="scale", nu=0.15)
        svm.fit(X_train_scaled)
        acc, far, frr, mat = compute_metrics(svm, X_test_scaled, X_train_scaled, user_id)

        results.append(("OneClassSVM", svm, acc, far, frr, mat))
        print(f"✓ OneClassSVM trained: Acc={acc:.4f}, FAR={far:.4f}, FRR={frr:.4f}")
    except Exception as e:
        print("OneClassSVM ERROR:", e)

   
    # Isolation Forest (with scaling)
   
    try:
        iso = IsolationForest(
            contamination=0.10,
            n_estimators=300,
            random_state=42
        )
        iso.fit(X_train_scaled)
        acc, far, frr, mat = compute_metrics(iso, X_test_scaled, X_train_scaled, user_id)

        results.append(("IsolationForest", iso, acc, far, frr, mat))
        print(f"✓ IsolationForest trained: Acc={acc:.4f}, FAR={far:.4f}, FRR={frr:.4f}")
    except Exception as e:
        print("IsolationForest ERROR:", e)

    # MLP (Trained with genuine + simulated impostor samples, with scaling)

    try:
        # Generate simulated impostor samples for training
        np.random.seed(42)
        impostor_count = len(X_train_scaled) // 2
        indices = np.random.choice(len(X_train_scaled), size=impostor_count, replace=False)
        X_train_impostor = X_train_scaled[indices].copy()
        X_train_impostor += np.random.normal(0, 0.8, X_train_impostor.shape)
        X_train_impostor *= np.random.uniform(0.7, 1.3, X_train_impostor.shape)

        # Combine genuine + impostor
        X_train_combined = np.vstack([X_train_scaled, X_train_impostor])
        y_train_combined = np.concatenate([np.ones(len(X_train_scaled)), np.zeros(len(X_train_impostor))])

        mlp = MLPClassifier(
            hidden_layer_sizes=(64, 32, 16),
            max_iter=800,
            random_state=42
        )
        mlp.fit(X_train_combined, y_train_combined)

        # Evaluate using compute_metrics
        acc, far, frr, mat = compute_metrics(mlp, X_test_scaled, X_train_scaled, user_id)

        results.append(("MLPClassifier", mlp, acc, far, frr, mat))
        print(f"✓ MLPClassifier trained: Acc={acc:.4f}, FAR={far:.4f}, FRR={frr:.4f}")
    except Exception as e:
        print("MLP ERROR:", e)

    # Pick BEST model
    if not results:
        return None, "All models failed."

    best = max(results, key=lambda r: r[2])  # highest accuracy
    best_name, best_model, best_acc, best_far, best_frr, best_matrix = best

    version = f"{best_name}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

    # Deactivate old models
    MLModel.query.filter_by(user_id=user_id, is_active=True).update({"is_active": False})

    # Calculate total samples used
    total_samples = len(X_train) + len(X_test)

    # Prepare all model comparisons for export
    model_comparisons = []
    for model_name, model_obj, acc, model_far, model_frr, matrix in results:
        model_comparisons.append({
            "algorithm": model_name,
            "accuracy": round(acc * 100, 2),
            "far": round(model_far * 100, 2),
            "frr": round(model_frr * 100, 2),
            "eer": round(((model_far + model_frr) / 2) * 100, 2),
            "confusion_matrix": matrix,
            "selected": model_name == best_name
        })

    # Store new model WITH scaler (critical for inference)
    model_package = {
        'model': best_model,
        'scaler': scaler  # Store scaler for consistent preprocessing during authentication
    }

    saved = MLModel(
        user_id=user_id,
        model_version=version,
        model_data=pickle.dumps(model_package),  # Store both model and scaler
        training_data_count=total_samples,
        accuracy=best_acc,
        far=best_far,
        frr=best_frr,
        created_at=datetime.utcnow(),
        is_active=True,
        training_metadata=json.dumps({
            "algorithm": best_name,
            "samples": total_samples,
            "train_samples": len(X_train),
            "test_samples": len(X_test),
            "features": X_train.shape[1] if len(X_train) > 0 else 21,
            "scaled": True,  # Indicate that scaler is included
            "confusion_matrix": best_matrix,
            "model_comparisons": model_comparisons,
            "feature_names": [
                "dwell_mean", "dwell_std", "dwell_median", "dwell_min", "dwell_max", "dwell_p25", "dwell_p75", "dwell_count",
                "flight_mean", "flight_std", "flight_median", "flight_min", "flight_max", "flight_p25", "flight_p75", "flight_count",
                "pause_mean", "pause_std", "pause_count",
                "typing_speed", "variability"
            ]
        })
    )

    db.session.add(saved)
    db.session.commit()

    return {
        "user_id": user_id,
        "best_model": best_name,
        "version": version,
        "accuracy": best_acc,
        "far": best_far,
        "frr": best_frr,
        "matrix": best_matrix
    }, None



#  ROUTES

@ml_bp.route("/ml/train/<int:user_id>", methods=["POST"])
def api_train_single(user_id):
    result, err = train_user_model(user_id)
    if err:
        return jsonify({"success": False, "error": err}), 400
    return jsonify({"success": True, "result": result}), 200


@ml_bp.route("/ml/train-all", methods=["POST"])
def api_train_all():
    users = User.query.all()
    summary = []

    for u in users:
        result, err = train_user_model(u.id)
        if result:
            summary.append(result)

    return jsonify({"success": True, "trained": summary}), 200


@ml_bp.route("/ml/model-info/<int:user_id>", methods=["GET"])
def api_model_info(user_id):
    m = MLModel.query.filter_by(user_id=user_id, is_active=True).first()
    if not m:
        return jsonify({"model_exists": False})
    return jsonify({"model_exists": True, "model": m.to_dict()})


@ml_bp.route("/ml/summary", methods=["GET"])
def api_summary():
    models = MLModel.query.filter_by(is_active=True).all()
    return jsonify({
        "models": [
            {
                "user_id": m.user_id,
                "version": m.model_version,
                "accuracy": m.accuracy,
                "frr": m.frr,
                "far": m.far,
                "samples": m.training_data_count
            }
            for m in models
        ]
    })
