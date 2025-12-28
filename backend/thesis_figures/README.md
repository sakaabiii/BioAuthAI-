# BioAuthAI - Performance Visualization Figures

This directory contains all generated figures for your thesis showing per-user ML model performance.

## 📊 Generated Figures

### 1. **Individual User Performance Comparisons** (51 files - ALL USERS!)
`user_XX_comparison.png` - One chart per user showing:
- **4 subplots**: Accuracy, EER, FAR, FRR
- **Color-coded bars** for each algorithm
- **Gold outline** highlighting the selected/best model
- **Value labels** on each bar

**All 51 Users Included**:
- User 53 through User 103 (IDs 53-103)
- Every single user in the database has their own chart!

**Use in Thesis**: Individual user case studies, detailed performance analysis, appendix

---

### 2. **Accuracy Heatmap - All Users**
`accuracy_heatmap_all_users.png`

Shows accuracy performance for all 51 users across all 5 algorithms in a color-coded heatmap:
- **Green** = High accuracy (90-100%)
- **Yellow** = Medium accuracy (50-90%)
- **Red** = Low accuracy (0-50%)

**All 5 Algorithms**: OneClassSVM, IsolationForest, MLPClassifier, RandomForest, GradientBoosting

**Use in Thesis**: Overview of system-wide performance, identifying patterns

---

### 3. **Best Model Summary**
`best_model_summary.png`

Two-part visualization:
- **Left**: Pie chart showing distribution of selected models across all users
- **Right**: Bar chart comparing average Accuracy and EER per algorithm

**Key Finding**: MLPClassifier was selected for 100% of users!

**Use in Thesis**: Results section, algorithm comparison summary

---

### 4. **Top 15 Performing Users**
`top_15_users.png`

Horizontal bar chart showing the top 15 users ranked by their best model accuracy:
- **Color-coded** by algorithm used
- **Labels** showing exact accuracy and algorithm name
- **Sorted** from highest to lowest performer

**Use in Thesis**: Highlighting best-case performance, success stories

---

## 📁 File Structure

```
thesis_figures/
├── README.md                          # This file
│
├── user_53_comparison.png             # Individual user charts (51 total)
├── user_54_comparison.png             # Each shows 4 metrics:
├── user_55_comparison.png             #   - Accuracy, EER, FAR, FRR
├── user_56_comparison.png             # Color-coded by algorithm
├── ...                                # (51 files total, IDs 53-103)
├── user_101_comparison.png
├── user_102_comparison.png
├── user_103_comparison.png
│
├── accuracy_heatmap_all_users.png     # Heatmap - 51 users × 5 algorithms
├── best_model_summary.png             # Pie + Bar chart summary (5 algorithms)
└── top_15_users.png                   # Top performers ranking
```

Total: **54 high-resolution figures** (300 DPI, PNG format)
- **51 individual user charts** (each showing 5 algorithms)
- **3 summary/overview charts** (showing 5 algorithms)

---

## 🎯 Key Results Summary

### Overall Performance (51 Users)

| Algorithm | Avg Accuracy | Avg EER | Selected For |
|-----------|--------------|---------|--------------|
| **MLPClassifier** | **99.86%** | **0.21%** | **51 users (100%)** |
| OneClassSVM | 83.94% | 24.09% | 0 users (0%) |
| RandomForest | 30.06% | 54.90% | 0 users (0%) |
| GradientBoosting | 30.13% | 54.80% | 0 users (0%) |
| IsolationForest | 25.61% | 61.59% | 0 users (0%) |

### Best Individual User Performances

**Perfect Accuracy (100%)**:
- User 54 (DSL User s003) - MLPClassifier
- User 55 (DSL User s004) - MLPClassifier
- User 56 (DSL User s005) - MLPClassifier
- User 57 (DSL User s007) - MLPClassifier
- ...and 42 more users with 100% accuracy!

**Highest OneClassSVM Performance**:
- User 88 (DSL User s041) - 97.22% accuracy

---

## 📖 Using Figures in Your Thesis

### LaTeX Example

```latex
\begin{figure}[h]
    \centering
    \includegraphics[width=0.9\textwidth]{thesis_figures/best_model_summary.png}
    \caption{Machine Learning Model Selection Summary across 51 Users.
             MLPClassifier was selected for 100\% of users with an average
             accuracy of 99.86\% and EER of 0.21\%.}
    \label{fig:model_summary}
\end{figure}
```

### Word/Google Docs

1. Insert → Picture → From File
2. Select the desired PNG file
3. Add caption below the figure
4. Reference in text

### PowerPoint

1. Drag and drop PNG files into slides
2. Resize as needed (high DPI allows zooming)
3. Add text annotations

---

## 🔧 Regenerating Figures

If you need to regenerate the figures with updated data:

```bash
cd bioauthai/backend
python visualize_user_performance.py
```

This will:
1. Read the most recent `thesis_ml_metrics_*.csv` file
2. Generate all figures in the `thesis_figures/` directory
3. Overwrite existing files

---

## 📊 Figure Descriptions

### Individual User Comparisons

Each user comparison chart contains 4 subplots:

1. **Accuracy (%)** - Overall classification accuracy
   - Higher is better
   - Target: > 90%

2. **EER (%) - Equal Error Rate**
   - Lower is better
   - Represents balance between FAR and FRR
   - Target: < 5%

3. **FAR (%) - False Accept Rate**
   - Lower is better
   - Security metric: rate impostors are accepted
   - Target: < 5%

4. **FRR (%) - False Reject Rate**
   - Lower is better
   - Usability metric: rate genuine users are rejected
   - Target: < 10%

**Gold outline** = Selected model (best performing algorithm for that user)

### Color Scheme (All 5 Algorithms)

- **Blue** (#3498db) - OneClassSVM
- **Red** (#e74c3c) - IsolationForest
- **Green** (#2ecc71) - MLPClassifier
- **Purple** (#9b59b6) - RandomForest
- **Orange** (#f39c12) - GradientBoosting

---

## 📝 Sample Figure Captions

### For Individual User Chart:
> **Figure X**: Performance comparison of five ML algorithms for User 53 (DSL User s002).
> MLPClassifier achieved 96.11% accuracy with 5.83% EER, significantly outperforming
> OneClassSVM (69.44%), RandomForest (33.33%), GradientBoosting (33.33%), and
> IsolationForest (5.00%). Gold outline indicates the selected model.

### For Heatmap:
> **Figure X**: Accuracy heatmap showing performance of five ML algorithms across 51 users.
> Green indicates high accuracy (>90%), yellow medium (50-90%), and red low (<50%).
> MLPClassifier consistently achieved the highest accuracy across all users, while
> RandomForest and GradientBoosting showed moderate performance around 30%.

### For Summary Chart:
> **Figure X**: Model selection summary. (Left) Distribution of selected models showing
> MLPClassifier was chosen for 100% of users. (Right) Average performance metrics
> demonstrating MLPClassifier's superior accuracy (99.86%) and minimal EER (0.21%).

### For Top Performers:
> **Figure X**: Top 15 users ranked by best model accuracy. 46 out of 51 users achieved
> perfect 100% accuracy using MLPClassifier, demonstrating the system's high reliability
> for keystroke dynamics-based authentication.

---

## 🎓 Thesis Recommendations

### Results Section
- Use `best_model_summary.png` to show overall findings
- Use `top_15_users.png` to highlight best performances
- Reference the heatmap to show consistency

### Methodology Section
- Include 1-2 individual user charts as examples
- Show diversity in user performance

### Discussion Section
- Compare individual user charts to explain why some users perform better
- Use heatmap to discuss patterns and outliers

### Appendix
- Include all 51 individual user comparison charts
- Provide full heatmap for complete reference
- Document per-user performance variations

---

## 📧 Questions?

All figures are high-resolution (300 DPI) PNG files suitable for:
- Print publications
- Academic theses
- Conference presentations
- Online documentation

Figures are publication-ready and follow academic visualization standards.

---

**Generated**: 2024-12-24
**Total Figures**: 54 (51 individual + 3 summary)
**Total Users**: 51 (ALL users included!)
**Algorithms**: 5 (OneClassSVM, IsolationForest, MLPClassifier, RandomForest, GradientBoosting)
