#!/usr/bin/env python3
"""
BioAuthAI - DSL Dataset Import Script
Converts DSL-StrongPasswordData to raw keystroke format
Database: backend/database/app.db
Author: Sharifa Al-Kaabi
"""

import pandas as pd
import numpy as np
import json
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.models.user import db, User, KeystrokeData
from src.main import app

# Path to DSL dataset (Excel file)
DSL_PATH = r"C:\Users\saalk\Downloads\bioauthai-complete-system\bioauthai\backend\DSL-StrongPasswordData.xls"


def convert_dsl_row_to_keystroke(row):
    """
    Convert a single DSL dataset row (33 features) into raw keystroke format.

    DSL features are per-key timings for password ".tie5Roanl":
    - H.X = Hold time (dwell) for key X
    - DD.X.Y = Down-Down time (flight) between keys X and Y
    - UD.X.Y = Up-Down time between keys X and Y

    We extract:
    - dwell_times: All H.* features
    - flight_times: All DD.* features
    - pause_patterns: All UD.* features where UD > DD (indicates pause)
    - typing_speed: Calculated from total time and key count
    """

    # Extract dwell times (H.* columns)
    dwell_cols = ['H.period', 'H.t', 'H.i', 'H.e', 'H.five', 'H.Shift.r', 'H.o', 'H.a', 'H.n', 'H.l', 'H.Return']
    dwell_times = [float(row[col]) for col in dwell_cols if col in row]

    # Extract flight times (DD.* columns)
    flight_cols = ['DD.period.t', 'DD.t.i', 'DD.i.e', 'DD.e.five', 'DD.five.Shift.r',
                   'DD.Shift.r.o', 'DD.o.a', 'DD.a.n', 'DD.n.l', 'DD.l.Return']
    flight_times = [float(row[col]) for col in flight_cols if col in row]

    # Extract pause patterns (UD.* columns - these indicate pauses between keystrokes)
    ud_cols = ['UD.period.t', 'UD.t.i', 'UD.i.e', 'UD.e.five', 'UD.five.Shift.r',
               'UD.Shift.r.o', 'UD.o.a', 'UD.a.n', 'UD.n.l', 'UD.l.Return']
    pause_patterns = []

    for i, ud_col in enumerate(ud_cols):
        if ud_col in row and i < len(flight_times):
            ud_time = float(row[ud_col])
            dd_time = flight_times[i]
            # If UD time significantly exceeds DD time, it indicates a pause/hesitation
            if ud_time > dd_time + 0.05:  # 50ms threshold
                pause_patterns.append(ud_time - dd_time)

    # Calculate typing speed (keys per second)
    total_time = sum(dwell_times) + sum(flight_times)
    typing_speed = len(dwell_times) / total_time if total_time > 0 else 0.0

    return {
        "dwell_times": dwell_times,
        "flight_times": flight_times,
        "pause_patterns": pause_patterns,
        "typing_speed": typing_speed
    }


def import_dsl_dataset():
    """
    Import the DSL-StrongPasswordData dataset into the database.
    Creates users based on subject IDs and stores keystroke data.
    """

    print("=" * 70)
    print("BioAuthAI - DSL Dataset Import")
    print("=" * 70)

    # Check if file exists
    if not os.path.exists(DSL_PATH):
        print(f"ERROR: Dataset file not found at: {DSL_PATH}")
        print("\nPlease ensure DSL-StrongPasswordData.xls is in the backend folder.")
        return False

    print(f"Found dataset file: {DSL_PATH}")

    # Load dataset
    print("\nLoading dataset...")
    try:
        df = pd.read_excel(DSL_PATH)
        print(f"Loaded {len(df)} samples from {df['subject'].nunique()} users")
    except Exception as e:
        print(f"ERROR loading file: {e}")
        return False

    # Show dataset info
    print(f"\nDataset shape: {df.shape[0]} rows × {df.shape[1]} columns")
    print(f"Unique subjects: {df['subject'].nunique()}")
    print(f"Sessions per user: {df.groupby('subject')['sessionIndex'].nunique().mean():.1f}")
    print(f"Samples per user: {len(df) // df['subject'].nunique()}")

    # Create users
    print("\n" + "=" * 70)
    print("Step 1: Creating user accounts")
    print("=" * 70)

    with app.app_context():
        created_users = 0
        existing_users = 0

        for subject_id in df['subject'].unique():
            user_email = f"{subject_id}@dsl.dataset"

            # Check if user already exists
            existing_user = User.query.filter_by(email=user_email).first()

            if not existing_user:
                user = User(
                    name=f"DSL User {subject_id}",
                    email=user_email,
                    role='Employee',
                    department='Dataset Users',
                    status='active'
                )
                user.set_password('dataset123')  # Default password for dataset users
                db.session.add(user)
                created_users += 1
            else:
                existing_users += 1

        db.session.commit()
        print(f"Created {created_users} new users")
        if existing_users > 0:
            print(f"Found {existing_users} existing users")

    # Import keystroke data
    print("\n" + "=" * 70)
    print("Step 2: Importing keystroke data with train/validation/test splits")
    print("=" * 70)

    with app.app_context():
        imported = 0
        errors = 0

        # Group by user for proper train/validation/test split
        for subject_id in df['subject'].unique():
            user = User.query.filter_by(email=f"{subject_id}@dsl.dataset").first()
            if not user:
                continue

            # Get all samples for this user
            user_data = df[df['subject'] == subject_id].copy()
            user_data = user_data.reset_index(drop=True)

            total_samples = len(user_data)

            # Split: 70% train, 15% validation, 15% test (matching Colab's 70/30 split pattern)
            train_end = int(0.70 * total_samples)
            val_end = int(0.85 * total_samples)

            for idx, row in user_data.iterrows():
                try:
                    # Determine data split
                    if idx < train_end:
                        data_split = 'train'
                    elif idx < val_end:
                        data_split = 'validation'
                    else:
                        data_split = 'test'

                    # Convert DSL row to raw keystroke format
                    raw_keystroke = convert_dsl_row_to_keystroke(row)

                    # Create keystroke record
                    keystroke = KeystrokeData(
                        user_id=user.id,
                        session_id=f"{subject_id}_s{row['sessionIndex']}_r{row['rep']}",
                        keystroke_features=json.dumps(raw_keystroke),
                        device_info=json.dumps({
                            "source": "dsl_dataset",
                            "subject": subject_id,
                            "sessionIndex": int(row['sessionIndex']),
                            "rep": int(row['rep'])
                        }),
                        is_training_data=True,
                        data_split=data_split,
                        anomaly_score=None
                    )

                    db.session.add(keystroke)
                    imported += 1

                    # Commit every 100 records
                    if imported % 100 == 0:
                        db.session.commit()
                        print(f"  Imported {imported} samples...", end='\r')

                except Exception as e:
                    errors += 1
                    if errors <= 5:  # Show first 5 errors only
                        print(f"  Error importing row {idx}: {e}")

        # Final commit
        db.session.commit()

        print(f"\nSuccessfully imported {imported} keystroke samples")
        if errors > 0:
            print(f"WARNING: {errors} errors encountered")

    # Show summary
    print("\n" + "=" * 70)
    print("Import Summary")
    print("=" * 70)

    with app.app_context():
        total_users = User.query.filter_by(department='Dataset Users').count()
        total_samples = KeystrokeData.query.count()
        train_samples = KeystrokeData.query.filter_by(data_split='train').count()
        val_samples = KeystrokeData.query.filter_by(data_split='validation').count()
        test_samples = KeystrokeData.query.filter_by(data_split='test').count()

        print(f"Total users: {total_users}")
        print(f"Total samples: {total_samples}")
        print(f"  - Training: {train_samples} ({train_samples/total_samples*100:.1f}%)")
        print(f"  - Validation: {val_samples} ({val_samples/total_samples*100:.1f}%)")
        print(f"  - Test: {test_samples} ({test_samples/total_samples*100:.1f}%)")
        print(f"\nAverage samples per user: {total_samples // total_users}")

    print("\n" + "=" * 70)
    print("Dataset import complete!")
    print("=" * 70)
    print("\nDatabase location:")
    print("  backend/database/app.db")
    print("\nNext steps:")
    print("1. Start Flask backend: python src/main.py")
    print("2. Train models: POST /ml/train-all")
    print("3. Check results: GET /ml/summary")
    print("4. View dashboard: All 5 algorithms will be shown in analytics")
    print(f"\nExpected accuracy: 95-98% (matching Colab performance)")

    return True


if __name__ == "__main__":
    print("\nWARNING: This will clear all existing keystroke data!")
    print("Do you want to continue? (yes/no): ", end='')

    response = input().strip().lower()

    if response == 'yes':
        # Clear existing data
        print("\nClearing existing keystroke data...")
        with app.app_context():
            deleted = KeystrokeData.query.delete()
            db.session.commit()
            print(f"Deleted {deleted} existing records")

        # Import dataset
        success = import_dsl_dataset()

        if success:
            print("\nAll done! You can now train models using the /ml/train-all endpoint.")
        else:
            print("\nImport failed. Please check the errors above.")
    else:
        print("\nImport cancelled.")
