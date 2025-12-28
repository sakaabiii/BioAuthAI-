"""
Export ML Model Performance Metrics for Thesis
===============================================

This script exports comprehensive machine learning performance metrics for each user
in the BioAuthAI system. The output is formatted for inclusion in academic thesis.

Output: CSV file with per-user performance metrics for all 5 ML algorithms
"""

import sys
import os
import json
import csv
from datetime import datetime

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from database import SessionLocal
from models.user import User, MLModel, KeystrokeData


def extract_model_comparison_metrics(metadata_json):
    """
    Extract performance metrics for all 5 algorithms from training metadata.

    Args:
        metadata_json: JSON string from MLModel.training_metadata

    Returns:
        Dictionary with metrics for each algorithm
    """
    try:
        metadata = json.loads(metadata_json)
        model_comparisons = metadata.get('model_comparisons', [])

        metrics = {}
        for comparison in model_comparisons:
            algo_name = comparison.get('algorithm', 'Unknown')
            metrics[algo_name] = {
                'accuracy': comparison.get('accuracy', 0.0),
                'far': comparison.get('far', 0.0),
                'frr': comparison.get('frr', 0.0),
                'eer': comparison.get('eer', 0.0),
                'precision': comparison.get('precision', 0.0),  # May not exist
                'recall': comparison.get('recall', 0.0),  # May not exist
                'f1_score': comparison.get('f1_score', 0.0),  # May not exist
                'selected': comparison.get('selected', False)
            }

        return metrics
    except (json.JSONDecodeError, AttributeError, KeyError) as e:
        print(f"Error parsing metadata: {e}")
        return {}


def calculate_derived_metrics(metrics):
    """
    Calculate Precision, Recall, and F1-Score from FAR/FRR if not present.

    NOTE: Metrics are stored as percentages (0-100), not fractions (0-1).

    Args:
        metrics: Dictionary with accuracy, far, frr, eer (all in percentages)

    Returns:
        Updated metrics with precision, recall, f1_score (all in percentages)
    """
    # If already calculated, return as-is
    if metrics.get('precision', 0.0) > 0:
        return metrics

    # Convert from percentage to fraction for calculation
    # Metrics are stored as percentages (0-100), so divide by 100
    far = metrics.get('far', 0.0) / 100.0
    frr = metrics.get('frr', 0.0) / 100.0

    # Precision ≈ 1 - FAR (genuine predictions that are correct)
    # Recall ≈ 1 - FRR (genuine samples that are correctly identified)
    precision = 1.0 - far
    recall = 1.0 - frr

    # F1-Score = 2 * (Precision * Recall) / (Precision + Recall)
    if precision + recall > 0:
        f1_score = 2 * (precision * recall) / (precision + recall)
    else:
        f1_score = 0.0

    # Convert back to percentages for storage
    metrics['precision'] = precision * 100.0
    metrics['recall'] = recall * 100.0
    metrics['f1_score'] = f1_score * 100.0

    return metrics


def export_thesis_metrics():
    """
    Main function to export all user metrics to CSV file.
    """
    db = SessionLocal()

    try:
        # Get all users with trained models
        users = db.query(User).all()

        print(f"\n{'='*80}")
        print(f"BioAuthAI - ML Performance Metrics Export for Thesis")
        print(f"{'='*80}")
        print(f"Total Users in Database: {len(users)}\n")

        # Prepare CSV output
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"thesis_ml_metrics_{timestamp}.csv"

        csv_rows = []

        # Algorithm names for consistent ordering (ALL 5 algorithms)
        algorithm_names = [
            'OneClassSVM',
            'IsolationForest',
            'MLPClassifier',
            'RandomForest',
            'GradientBoosting'
        ]

        # Process each user
        for user in users:
            # Get the most recent active model for this user
            model = db.query(MLModel).filter(
                MLModel.user_id == user.id,
                MLModel.is_active == True
            ).order_by(MLModel.created_at.desc()).first()

            if not model or not model.training_metadata:
                print(f"⚠️  User {user.id} ({user.name}): No trained model found - SKIPPING")
                continue

            # Get keystroke data count
            keystroke_count = db.query(KeystrokeData).filter(
                KeystrokeData.user_id == user.id
            ).count()

            # Extract metrics for all algorithms
            all_metrics = extract_model_comparison_metrics(model.training_metadata)

            if not all_metrics:
                print(f"⚠️  User {user.id} ({user.name}): No metrics in model - SKIPPING")
                continue

            # Get metadata for additional info
            try:
                metadata = json.loads(model.training_metadata)
                train_samples = metadata.get('train_samples', 0)
                test_samples = metadata.get('test_samples', 0)
                selected_algorithm = metadata.get('algorithm', 'Unknown')
            except:
                train_samples = 0
                test_samples = 0
                selected_algorithm = 'Unknown'

            print(f"✓ User {user.id} ({user.name}):")
            print(f"  - Total Keystroke Samples: {keystroke_count}")
            print(f"  - Training Samples: {train_samples}")
            print(f"  - Testing Samples: {test_samples}")
            print(f"  - Selected Model: {selected_algorithm}")
            print(f"  - Model Version: {model.model_version}")

            # Create rows for each algorithm
            for algo_name in algorithm_names:
                if algo_name in all_metrics:
                    metrics = calculate_derived_metrics(all_metrics[algo_name])

                    row = {
                        'User ID': user.id,
                        'User Name': user.name,
                        'Email': user.email,
                        'Department': user.department or 'N/A',
                        'Total Samples': keystroke_count,
                        'Training Samples': train_samples,
                        'Testing Samples': test_samples,
                        'Algorithm': algo_name,
                        'Accuracy (%)': f"{metrics['accuracy']:.2f}",
                        'Precision (%)': f"{metrics['precision']:.2f}",
                        'Recall (%)': f"{metrics['recall']:.2f}",
                        'F1-Score (%)': f"{metrics['f1_score']:.2f}",
                        'FAR (%)': f"{metrics['far']:.2f}",
                        'FRR (%)': f"{metrics['frr']:.2f}",
                        'EER (%)': f"{metrics['eer']:.2f}",
                        'Selected Model': 'Yes' if metrics['selected'] else 'No',
                        'Model Version': model.model_version,
                        'Training Date': model.created_at.strftime("%Y-%m-%d %H:%M:%S")
                    }

                    csv_rows.append(row)

                    print(f"    {algo_name:25s} - Acc: {metrics['accuracy']:5.2f}% | "
                          f"FAR: {metrics['far']:5.2f}% | FRR: {metrics['frr']:5.2f}% | "
                          f"EER: {metrics['eer']:5.2f}%"
                          f"{' [SELECTED]' if metrics['selected'] else ''}")

            print()

        # Write CSV file
        if csv_rows:
            fieldnames = [
                'User ID', 'User Name', 'Email', 'Department',
                'Total Samples', 'Training Samples', 'Testing Samples',
                'Algorithm',
                'Accuracy (%)', 'Precision (%)', 'Recall (%)', 'F1-Score (%)',
                'FAR (%)', 'FRR (%)', 'EER (%)',
                'Selected Model', 'Model Version', 'Training Date'
            ]

            with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(csv_rows)

            print(f"{'='*80}")
            print(f"✓ Export Complete!")
            print(f"{'='*80}")
            print(f"Output File: {output_file}")
            print(f"Total Rows: {len(csv_rows)} (5 algorithms × {len(csv_rows)//5} users)")
            print(f"\nYou can now import this CSV into Excel/LaTeX for your thesis.")
            print(f"{'='*80}\n")

            # Also create a summary table for quick reference
            create_summary_table(csv_rows, timestamp)

        else:
            print("⚠️  No users with trained models found. Please train models first.")

    finally:
        db.close()


def create_summary_table(csv_rows, timestamp):
    """
    Create a summary table with average metrics across all users per algorithm.
    """
    output_file = f"thesis_ml_summary_{timestamp}.csv"

    algorithm_names = [
        'OneClassSVM',
        'IsolationForest',
        'MLPClassifier',
        'RandomForest',
        'GradientBoosting'
    ]

    summary_rows = []

    for algo in algorithm_names:
        # Filter rows for this algorithm
        algo_rows = [row for row in csv_rows if row['Algorithm'] == algo]

        if not algo_rows:
            continue

        # Calculate averages
        avg_accuracy = sum(float(row['Accuracy (%)']) for row in algo_rows) / len(algo_rows)
        avg_precision = sum(float(row['Precision (%)']) for row in algo_rows) / len(algo_rows)
        avg_recall = sum(float(row['Recall (%)']) for row in algo_rows) / len(algo_rows)
        avg_f1 = sum(float(row['F1-Score (%)']) for row in algo_rows) / len(algo_rows)
        avg_far = sum(float(row['FAR (%)']) for row in algo_rows) / len(algo_rows)
        avg_frr = sum(float(row['FRR (%)']) for row in algo_rows) / len(algo_rows)
        avg_eer = sum(float(row['EER (%)']) for row in algo_rows) / len(algo_rows)

        summary_rows.append({
            'Algorithm': algo,
            'Users Count': len(algo_rows),
            'Avg Accuracy (%)': f"{avg_accuracy:.2f}",
            'Avg Precision (%)': f"{avg_precision:.2f}",
            'Avg Recall (%)': f"{avg_recall:.2f}",
            'Avg F1-Score (%)': f"{avg_f1:.2f}",
            'Avg FAR (%)': f"{avg_far:.2f}",
            'Avg FRR (%)': f"{avg_frr:.2f}",
            'Avg EER (%)': f"{avg_eer:.2f}"
        })

    # Write summary CSV
    if summary_rows:
        fieldnames = [
            'Algorithm', 'Users Count',
            'Avg Accuracy (%)', 'Avg Precision (%)', 'Avg Recall (%)', 'Avg F1-Score (%)',
            'Avg FAR (%)', 'Avg FRR (%)', 'Avg EER (%)'
        ]

        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(summary_rows)

        print(f"\n📊 Summary Table (Average Across All Users):")
        print(f"{'='*80}")
        print(f"{'Algorithm':<30} {'Accuracy':<10} {'FAR':<10} {'FRR':<10} {'EER':<10}")
        print(f"{'-'*80}")
        for row in summary_rows:
            print(f"{row['Algorithm']:<30} {row['Avg Accuracy (%)']:>8}% "
                  f"{row['Avg FAR (%)']:>8}% {row['Avg FRR (%)']:>8}% {row['Avg EER (%)']:>8}%")
        print(f"{'='*80}")
        print(f"Summary saved to: {output_file}\n")


if __name__ == "__main__":
    print("\nStarting ML Metrics Export for Thesis...\n")
    export_thesis_metrics()
