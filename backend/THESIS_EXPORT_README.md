# BioAuthAI - Thesis Performance Metrics Export

This directory contains scripts and exported data for including machine learning performance metrics in your academic thesis.

## 📁 Generated Files

### 1. **Main Detailed CSV**
`thesis_ml_metrics_YYYYMMDD_HHMMSS.csv` (26 KB)
- **Per-user, per-algorithm performance metrics**
- Contains 153 rows (51 users × 3 algorithms)
- Each row includes:
  - User information (ID, Name, Email, Department)
  - Sample counts (Total, Training, Testing)
  - Algorithm name
  - 7 performance metrics: Accuracy, Precision, Recall, F1-Score, FAR, FRR, EER
  - Selected model indicator
  - Model version and training date

**Use this for**: Detailed analysis, appendices, per-user comparisons

### 2. **Summary CSV**
`thesis_ml_summary_YYYYMMDD_HHMMSS.csv` (303 bytes)
- **Averaged metrics across all users per algorithm**
- 3 rows (one per algorithm)
- Shows mean performance across all 51 users

**Use this for**: Main results section, quick overview table

### 3. **LaTeX Table**
`thesis_ml_summary_YYYYMMDD_HHMMSS.tex` (705 bytes)
- **Ready-to-use LaTeX table code**
- Professionally formatted with booktabs package
- Copy-paste directly into your thesis `.tex` file

**Use this for**: LaTeX thesis documents

### 4. **Markdown Documentation**
`thesis_ml_summary_YYYYMMDD_HHMMSS.md` (1.6 KB)
- **Formatted summary with explanations**
- Includes metric definitions and key findings
- Great for README or documentation

**Use this for**: Documentation, presentations, README files

---

## 🚀 How to Use

### Step 1: Export Metrics (Already Done!)

The metrics have already been exported. The latest files are:
- `thesis_ml_metrics_20251224_220803.csv`
- `thesis_ml_summary_20251224_220803.csv`
- `thesis_ml_summary_20251224_220803.tex`
- `thesis_ml_summary_20251224_220803.md`

### Step 2: Re-export (If Needed)

If you need to re-export with updated data:

```bash
cd bioauthai/backend
python export_thesis_metrics.py
```

This will generate new timestamped files with the current database state.

### Step 3: Generate LaTeX/Markdown Tables

```bash
python generate_thesis_table.py
```

This reads the most recent summary CSV and generates:
- LaTeX table (.tex)
- Markdown documentation (.md)

---

## 📊 Performance Metrics Summary

### Overall Results (51 Users)

| Algorithm | Accuracy | Precision | Recall | F1-Score | FAR | FRR | EER |
|-----------|----------|-----------|--------|----------|-----|-----|-----|
| **MLPClassifier** | **99.86%** | **100.00%** | **99.57%** | **99.78%** | **0.00%** | **0.43%** | **0.21%** |
| OneClassSVM | 83.94% | 100.00% | 51.83% | 65.17% | 0.00% | 48.17% | 24.09% |
| IsolationForest | 25.61% | 0.00% | 76.83% | 0.00% | 100.00% | 23.17% | 61.59% |

### Key Findings

1. **MLPClassifier (Neural Network)** is the best-performing algorithm:
   - Near-perfect accuracy (99.86%)
   - Extremely low Equal Error Rate (0.21%)
   - Best balance between security (FAR) and usability (FRR)
   - **Recommended for production deployment**

2. **OneClassSVM** provides moderate performance:
   - Good accuracy (83.94%)
   - Acceptable EER (24.09%)
   - Works well for unsupervised anomaly detection
   - Useful when limited impostor samples are available

3. **IsolationForest** has lower performance:
   - Poor accuracy (25.61%)
   - High EER (61.59%)
   - High false accept rate (100%)
   - **Not recommended for biometric authentication**

---

## 📖 Metric Definitions

### Accuracy
Overall classification accuracy: `(TP + TN) / Total`
- Measures how often the model is correct (both accepting genuine users and rejecting impostors)

### Precision
Proportion of genuine predictions that are correct: `1 - FAR`
- Measures how reliable the model is when it accepts a user
- Higher precision = fewer false accepts

### Recall (Sensitivity)
Proportion of genuine samples correctly identified: `1 - FRR`
- Measures how many genuine users are correctly accepted
- Higher recall = fewer false rejects (better user experience)

### F1-Score
Harmonic mean of precision and recall: `2 × (Precision × Recall) / (Precision + Recall)`
- Balanced measure of both precision and recall
- Important when you need to balance security and usability

### FAR (False Accept Rate)
Rate at which impostors are incorrectly accepted
- **Security metric** - lower is better
- Critical for biometric security systems
- Target: < 5% (0.05)

### FRR (False Reject Rate)
Rate at which genuine users are incorrectly rejected
- **Usability metric** - lower is better
- Affects user experience
- Target: < 10% (0.10)

### EER (Equal Error Rate)
Point where FAR = FRR: `(FAR + FRR) / 2`
- **Overall performance metric** - lower is better
- Represents the best trade-off between security and usability
- Commonly used to compare biometric systems

---

## 🎓 Using in Your Thesis

### For LaTeX Thesis

1. Copy the contents of `thesis_ml_summary_YYYYMMDD_HHMMSS.tex`
2. Paste into your thesis `.tex` file where you want the table
3. Make sure you have `\usepackage{booktabs}` in your preamble
4. Compile your thesis

Example:
```latex
\documentclass{article}
\usepackage{booktabs}  % Required for professional tables

\begin{document}

\section{Results}

The performance of all five machine learning algorithms was evaluated
on 51 users from the DSL dataset. Table~\ref{tab:ml_performance} shows
the averaged performance metrics across all users.

% Paste the LaTeX table here
\begin{table}[h]
\centering
\caption{Machine Learning Model Performance Metrics - BioAuthAI System}
\label{tab:ml_performance}
...
\end{table}

\end{document}
```

### For Word/Google Docs

1. Open `thesis_ml_metrics_YYYYMMDD_HHMMSS.csv` in Excel
2. Filter by algorithm or user as needed
3. Create pivot tables or charts
4. Copy formatted table into Word/Google Docs

### For Presentations

1. Use the markdown table from `.md` file
2. Convert to PowerPoint table
3. Add visualizations using the CSV data

---

## 📁 File Structure

```
bioauthai/backend/
│
├── export_thesis_metrics.py          # Main export script
├── generate_thesis_table.py          # LaTeX/Markdown generator
├── THESIS_EXPORT_README.md           # This file
│
├── thesis_ml_metrics_*.csv           # Detailed per-user data
├── thesis_ml_summary_*.csv           # Summary averages
├── thesis_ml_summary_*.tex           # LaTeX table
└── thesis_ml_summary_*.md            # Markdown documentation
```

---

## 🔧 Script Details

### `export_thesis_metrics.py`

**Purpose**: Exports all performance metrics from the database

**What it does**:
1. Connects to SQLite database
2. Queries all users with trained ML models
3. Extracts performance metrics from `training_metadata` JSON field
4. Calculates Precision, Recall, F1-Score from FAR/FRR
5. Generates two CSV files:
   - Detailed per-user CSV (all users, all algorithms)
   - Summary CSV (averaged across users)

**Output**: 2 CSV files with timestamp

**Runtime**: ~2-5 seconds for 51 users

### `generate_thesis_table.py`

**Purpose**: Converts summary CSV to formatted tables

**What it does**:
1. Reads the most recent summary CSV
2. Generates LaTeX table with booktabs formatting
3. Generates Markdown table with explanations
4. Includes metric definitions and key findings

**Output**:
- `.tex` file (LaTeX table)
- `.md` file (Markdown documentation)

**Runtime**: < 1 second

---

## 📊 Sample Data

### Example: User s002 (ID: 53)

| Algorithm | Accuracy | Precision | Recall | F1-Score | FAR | FRR | EER | Selected |
|-----------|----------|-----------|--------|----------|-----|-----|-----|----------|
| OneClassSVM | 69.44% | 100.00% | 8.33% | 15.38% | 0.00% | 91.67% | 45.83% | No |
| IsolationForest | 5.00% | 0.00% | 15.00% | 0.00% | 100.00% | 85.00% | 92.50% | No |
| **MLPClassifier** | **96.11%** | **100.00%** | **88.33%** | **93.80%** | **0.00%** | **11.67%** | **5.83%** | **Yes** |

**Training Data**: 280 samples
**Testing Data**: 60 samples
**Selected Model**: MLPClassifier

---

## ❓ FAQ

### Q: Why are there only 3 algorithms in the summary when the system supports 5?

**A**: The export script filters for the 3 most common algorithms found in the database:
- OneClassSVM
- IsolationForest
- MLPClassifier

If you need RandomForest and GradientBoosting metrics, check the detailed CSV or modify the `algorithm_names` list in `export_thesis_metrics.py`.

### Q: Can I export metrics for a specific user?

**A**: Yes! You can filter the detailed CSV by User ID or use Python/pandas:

```python
import pandas as pd
df = pd.read_csv('thesis_ml_metrics_20251224_220803.csv')
user_data = df[df['User ID'] == 53]
print(user_data)
```

### Q: How do I add more algorithms to the export?

**A**: Edit `export_thesis_metrics.py` and add algorithm names to the `algorithm_names` list:

```python
algorithm_names = [
    'OneClassSVM',
    'IsolationForest',
    'MLPClassifier',
    'RandomForestClassifier',      # Add this
    'GradientBoostingClassifier'   # Add this
]
```

### Q: What if I get "No trained model found" warnings?

**A**: Some users in the database don't have trained ML models yet. The export script automatically skips these users. To train models for all users, use the `/api/ml/train/<user_id>` endpoint.

---

## 🔬 Research Context

### Dataset Information
- **Source**: DSL-StrongPasswordData Keystroke Dynamics Dataset
- **Total Users**: 51 (from original 51 users in dataset)
- **Samples per User**: 400 keystroke sessions
- **Training Split**: 70% (280 samples)
- **Testing Split**: 15% (60 samples)
- **Validation Split**: 15% (60 samples)

### Feature Engineering
Each keystroke session is converted into **21 statistical features**:

**Dwell Time Features (8)**:
1-8. Mean, Std, Median, Min, Max, 25th percentile, 75th percentile, Count

**Flight Time Features (8)**:
9-16. Mean, Std, Median, Min, Max, 25th percentile, 75th percentile, Count

**Pause & Rhythm Features (3)**:
17-19. Pause mean, Pause std, Pause count

**High-Level Behavior Features (2)**:
20. Typing speed (characters/second)
21. Variability (typing stability)

### Evaluation Methodology
- **Cross-user testing**: Each model is tested against samples from other users (realistic impostor simulation)
- **Impostor samples**: 2× genuine test samples (120 impostor samples vs 60 genuine)
- **Metrics calculation**: Based on confusion matrix (TP, FN, FP, TN)

---

## 📚 Citation

If you use this data in your thesis, consider citing the BioAuthAI system:

```bibtex
@mastersthesis{your_thesis,
  author = {Your Name},
  title = {Behavioral Biometric Authentication Using Keystroke Dynamics},
  school = {Your University},
  year = {2024},
  note = {BioAuthAI System - ML Performance Metrics}
}
```

---

## 📧 Support

If you have questions or need additional metrics:
1. Check the detailed CSV for per-user breakdowns
2. Modify the export scripts to add custom metrics
3. Use pandas/Python to analyze the CSV data further

---

**Last Updated**: 2025-12-24
**Export Version**: 1.0
**Total Users Exported**: 51
**Total Algorithms**: 3 (OneClassSVM, IsolationForest, MLPClassifier)
