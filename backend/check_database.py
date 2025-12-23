#!/usr/bin/env python3
"""
Quick database checker - see what's in your database
"""
import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.models.user import db, User, KeystrokeData, MLModel
from src.main import app

with app.app_context():
    print("=" * 70)
    print("DATABASE CHECK")
    print("=" * 70)

    # Check users
    total_users = User.query.count()
    dsl_users = User.query.filter(User.email.like('%@dsl.dataset')).count()
    forensic_users = User.query.filter(User.email.like('%@forensiclab.bh')).count()

    print(f"\nUSERS:")
    print(f"  Total: {total_users}")
    print(f"  DSL dataset users (@dsl.dataset): {dsl_users}")
    print(f"  Forensic lab users (@forensiclab.bh): {forensic_users}")

    if dsl_users == 0:
        print("\n  ❌ NO DSL USERS FOUND!")
        print("  👉 You need to run: python import_dsl_dataset.py")
    else:
        print(f"\n  ✅ Found {dsl_users} DSL users")

    # Check keystroke data
    total_samples = KeystrokeData.query.count()
    train_samples = KeystrokeData.query.filter_by(data_split='train').count()
    test_samples = KeystrokeData.query.filter_by(data_split='test').count()

    print(f"\nKEYSTROKE DATA:")
    print(f"  Total samples: {total_samples}")
    print(f"  Train split: {train_samples}")
    print(f"  Test split: {test_samples}")

    if total_samples == 20400:
        print(f"\n  ✅ Correct sample count (20,400)")
    else:
        print(f"\n  ❌ Wrong sample count (expected 20,400, got {total_samples})")

    # Check a sample keystroke data format
    sample = KeystrokeData.query.first()
    if sample:
        features = json.loads(sample.keystroke_features)
        print(f"\nSAMPLE KEYSTROKE DATA FORMAT:")
        print(f"  Type: {type(features)}")

        if isinstance(features, dict):
            print(f"  ✅ Storing RAW data (dict)")
            print(f"  Keys: {list(features.keys())}")
        elif isinstance(features, list):
            print(f"  ❌ Storing EXTRACTED features (list)")
            print(f"  Length: {len(features)}")
            print("  👉 You need to re-import with fixed code!")

    # Check models
    total_models = MLModel.query.filter_by(is_active=True).count()
    print(f"\nTRAINED MODELS:")
    print(f"  Active models: {total_models}")

    if total_models > 0:
        model = MLModel.query.filter_by(is_active=True).first()
        metadata = json.loads(model.training_metadata) if model.training_metadata else {}

        print(f"\nSAMPLE MODEL METADATA:")
        print(f"  Algorithm: {metadata.get('algorithm', 'Unknown')}")
        print(f"  Scaled: {metadata.get('scaled', False)}")
        print(f"  Has model_comparisons: {'model_comparisons' in metadata}")

        if 'model_comparisons' in metadata:
            print(f"  ✅ Model comparisons found ({len(metadata['model_comparisons'])} algorithms)")
            for comp in metadata['model_comparisons']:
                print(f"     - {comp['algorithm']}: {comp['accuracy']:.2f}% accuracy")
        else:
            print(f"  ❌ No model_comparisons found")
            print("  👉 Models were trained with OLD code!")

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    if dsl_users == 51 and total_samples == 20400 and 'model_comparisons' in metadata:
        print("✅ Everything looks good!")
        print("   Your models should show 5 algorithms in the dashboard.")
    else:
        print("❌ Database has issues:")
        if dsl_users != 51:
            print("   1. Re-import dataset: python import_dsl_dataset.py")
        if total_samples != 20400:
            print("   2. Dataset not fully imported")
        if 'model_comparisons' not in metadata:
            print("   3. Re-train models: curl -X POST http://localhost:5000/ml/train-all")

    print("\n")
