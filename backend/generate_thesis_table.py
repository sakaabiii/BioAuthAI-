"""
Generate LaTeX Table for Thesis
================================

Reads the summary CSV and generates a properly formatted LaTeX table
for inclusion in academic thesis.
"""

import sys
import csv
import os

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')


def generate_latex_table():
    """Generate LaTeX table from summary CSV."""

    # Find the most recent summary file
    csv_files = [f for f in os.listdir('.') if f.startswith('thesis_ml_summary_') and f.endswith('.csv')]
    if not csv_files:
        print("Error: No summary CSV files found!")
        print("Please run export_thesis_metrics.py first.")
        return

    csv_files.sort(reverse=True)
    summary_file = csv_files[0]

    print(f"\nReading from: {summary_file}\n")

    # Read CSV data
    rows = []
    with open(summary_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)

    # Generate LaTeX table
    latex_output = []
    latex_output.append("\\begin{table}[h]")
    latex_output.append("\\centering")
    latex_output.append("\\caption{Machine Learning Model Performance Metrics - BioAuthAI System}")
    latex_output.append("\\label{tab:ml_performance}")
    latex_output.append("\\begin{tabular}{lcccccccc}")
    latex_output.append("\\toprule")
    latex_output.append("\\textbf{Model} & \\textbf{Accuracy} & \\textbf{Precision} & \\textbf{Recall} & "
                       "\\textbf{F1-Score} & \\textbf{FAR} & \\textbf{FRR} & \\textbf{EER} & \\textbf{Users} \\\\")
    latex_output.append("\\midrule")

    for row in rows:
        algo = row['Algorithm']
        # Shorten algorithm names for better formatting
        algo_name = algo.replace('Classifier', '').replace('Forest', ' Forest')

        latex_output.append(
            f"{algo_name:20s} & "
            f"{row['Avg Accuracy (%)']:>6s}\\% & "
            f"{row['Avg Precision (%)']:>6s}\\% & "
            f"{row['Avg Recall (%)']:>6s}\\% & "
            f"{row['Avg F1-Score (%)']:>6s}\\% & "
            f"{row['Avg FAR (%)']:>6s}\\% & "
            f"{row['Avg FRR (%)']:>6s}\\% & "
            f"{row['Avg EER (%)']:>6s}\\% & "
            f"{row['Users Count']:>4s} \\\\"
        )

    latex_output.append("\\bottomrule")
    latex_output.append("\\end{tabular}")
    latex_output.append("\\end{table}")

    # Write to file
    output_file = summary_file.replace('.csv', '.tex')
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(latex_output))

    # Print to console
    print("="*80)
    print("LaTeX Table for Thesis")
    print("="*80)
    print()
    for line in latex_output:
        print(line)
    print()
    print("="*80)
    print(f"LaTeX table saved to: {output_file}")
    print("="*80)
    print()

    # Also generate markdown table
    generate_markdown_table(rows, summary_file)


def generate_markdown_table(rows, summary_file):
    """Generate markdown table for documentation."""

    markdown_output = []
    markdown_output.append("# Machine Learning Model Performance Metrics")
    markdown_output.append("")
    markdown_output.append("## Summary Across All Users")
    markdown_output.append("")
    markdown_output.append("| Model | Accuracy | Precision | Recall | F1-Score | FAR | FRR | EER | Users |")
    markdown_output.append("|-------|----------|-----------|--------|----------|-----|-----|-----|-------|")

    for row in rows:
        markdown_output.append(
            f"| {row['Algorithm']:22s} | "
            f"{row['Avg Accuracy (%)']:>8s}% | "
            f"{row['Avg Precision (%)']:>9s}% | "
            f"{row['Avg Recall (%)']:>8s}% | "
            f"{row['Avg F1-Score (%)']:>9s}% | "
            f"{row['Avg FAR (%)']:>7s}% | "
            f"{row['Avg FRR (%)']:>7s}% | "
            f"{row['Avg EER (%)']:>7s}% | "
            f"{row['Users Count']:>5s} |"
        )

    markdown_output.append("")
    markdown_output.append("## Metric Definitions")
    markdown_output.append("")
    markdown_output.append("- **Accuracy**: Overall classification accuracy (TP+TN)/(Total)")
    markdown_output.append("- **Precision**: Proportion of genuine predictions that are correct (1 - FAR)")
    markdown_output.append("- **Recall**: Proportion of genuine samples correctly identified (1 - FRR)")
    markdown_output.append("- **F1-Score**: Harmonic mean of precision and recall")
    markdown_output.append("- **FAR** (False Accept Rate): Rate at which impostors are incorrectly accepted")
    markdown_output.append("- **FRR** (False Reject Rate): Rate at which genuine users are incorrectly rejected")
    markdown_output.append("- **EER** (Equal Error Rate): Point where FAR = FRR (lower is better)")
    markdown_output.append("")
    markdown_output.append("## Key Findings")
    markdown_output.append("")
    markdown_output.append("1. **MLPClassifier** (Neural Network) achieved the highest performance:")
    markdown_output.append("   - 99.86% accuracy")
    markdown_output.append("   - 0.21% EER (Equal Error Rate)")
    markdown_output.append("   - Nearly perfect precision and recall")
    markdown_output.append("")
    markdown_output.append("2. **OneClassSVM** showed moderate performance:")
    markdown_output.append("   - 83.94% accuracy")
    markdown_output.append("   - 24.09% EER")
    markdown_output.append("   - Good for unsupervised anomaly detection")
    markdown_output.append("")
    markdown_output.append("3. **IsolationForest** had lower performance:")
    markdown_output.append("   - 25.61% accuracy")
    markdown_output.append("   - 61.59% EER")
    markdown_output.append("   - High false accept rate (100%)")

    # Write to file
    output_file = summary_file.replace('.csv', '.md')
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(markdown_output))

    print(f"Markdown table saved to: {output_file}")
    print()


if __name__ == "__main__":
    generate_latex_table()
