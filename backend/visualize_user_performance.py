"""
Visualize Per-User ML Performance with Charts
==============================================

Creates visual charts showing:
1. Per-user performance comparison across all algorithms
2. Best model highlighting for each user
3. Overall performance heatmap
4. Top-performing users
"""

import sys
import os
import csv
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from collections import defaultdict

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')


def load_data(csv_file):
    """Load per-user metrics from CSV file."""
    users_data = defaultdict(dict)

    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            user_id = row['User ID']
            user_name = row['User Name']
            algorithm = row['Algorithm']

            if user_id not in users_data:
                users_data[user_id] = {
                    'name': user_name,
                    'algorithms': {}
                }

            users_data[user_id]['algorithms'][algorithm] = {
                'accuracy': float(row['Accuracy (%)']),
                'precision': float(row['Precision (%)']),
                'recall': float(row['Recall (%)']),
                'f1_score': float(row['F1-Score (%)']),
                'far': float(row['FAR (%)']),
                'frr': float(row['FRR (%)']),
                'eer': float(row['EER (%)']),
                'selected': row['Selected Model'] == 'Yes'
            }

    return users_data


def create_per_user_comparison(users_data, output_dir='thesis_figures'):
    """Create bar charts comparing algorithms for each user."""

    os.makedirs(output_dir, exist_ok=True)

    algorithms = ['OneClassSVM', 'IsolationForest', 'MLPClassifier', 'RandomForest', 'GradientBoosting']
    colors = {
        'OneClassSVM': '#3498db',
        'IsolationForest': '#e74c3c',
        'MLPClassifier': '#2ecc71',
        'RandomForest': '#9b59b6',
        'GradientBoosting': '#f39c12'
    }

    print(f"\n{'='*80}")
    print("Generating Per-User Performance Charts")
    print(f"{'='*80}\n")

    # Create individual charts for ALL users
    all_users = sorted(users_data.keys(), key=lambda x: int(x))  # All users sorted by ID

    for user_id in all_users:
        user_info = users_data[user_id]
        user_name = user_info['name']

        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle(f'{user_name} (ID: {user_id}) - ML Model Performance Comparison',
                     fontsize=16, fontweight='bold')

        # Prepare data
        metrics_to_plot = ['accuracy', 'eer', 'far', 'frr']
        metric_titles = ['Accuracy (%)', 'EER (%) - Lower is Better',
                        'FAR (%) - Lower is Better', 'FRR (%) - Lower is Better']

        for idx, (metric, title) in enumerate(zip(metrics_to_plot, metric_titles)):
            ax = axes[idx // 2, idx % 2]

            values = [user_info['algorithms'][algo][metric] for algo in algorithms]
            bars = ax.bar(algorithms, values,
                         color=[colors[algo] for algo in algorithms],
                         edgecolor='black', linewidth=1.5, alpha=0.8)

            # Highlight the selected model
            for i, algo in enumerate(algorithms):
                if user_info['algorithms'][algo]['selected']:
                    bars[i].set_edgecolor('gold')
                    bars[i].set_linewidth(3)

            ax.set_ylabel(title, fontsize=11, fontweight='bold')
            ax.set_ylim(0, 105 if metric == 'accuracy' else 105)
            ax.grid(axis='y', alpha=0.3, linestyle='--')
            ax.set_axisbelow(True)

            # Add value labels on bars
            for i, (algo, val) in enumerate(zip(algorithms, values)):
                ax.text(i, val + 2, f'{val:.1f}%', ha='center', va='bottom',
                       fontweight='bold', fontsize=9)

        # Add legend
        selected_patch = mpatches.Patch(edgecolor='gold', facecolor='white',
                                       linewidth=3, label='Selected Model')
        fig.legend(handles=[selected_patch], loc='lower center', ncol=1,
                  bbox_to_anchor=(0.5, -0.02), fontsize=11)

        plt.tight_layout(rect=[0, 0.03, 1, 0.96])

        output_file = os.path.join(output_dir, f'user_{user_id}_comparison.png')
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"✓ Generated: {output_file}")

    print(f"\n{'='*80}")
    print(f"Generated {len(all_users)} individual user comparison charts")
    print(f"{'='*80}\n")


def create_overall_heatmap(users_data, output_dir='thesis_figures'):
    """Create heatmap showing accuracy across all users and algorithms."""

    os.makedirs(output_dir, exist_ok=True)

    algorithms = ['OneClassSVM', 'IsolationForest', 'MLPClassifier', 'RandomForest', 'GradientBoosting']
    user_ids = sorted(users_data.keys(), key=lambda x: int(x))

    # Prepare accuracy matrix
    accuracy_matrix = []
    for user_id in user_ids:
        row = [users_data[user_id]['algorithms'][algo]['accuracy']
               for algo in algorithms]
        accuracy_matrix.append(row)

    accuracy_matrix = np.array(accuracy_matrix)

    # Create heatmap
    fig, ax = plt.subplots(figsize=(14, 16))

    im = ax.imshow(accuracy_matrix, cmap='RdYlGn', aspect='auto', vmin=0, vmax=100)

    # Set ticks
    ax.set_xticks(np.arange(len(algorithms)))
    ax.set_yticks(np.arange(len(user_ids)))
    ax.set_xticklabels(algorithms, fontsize=11, fontweight='bold')
    ax.set_yticklabels([f"User {uid}" for uid in user_ids], fontsize=7)

    # Rotate x-axis labels
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")

    # Add colorbar
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label('Accuracy (%)', rotation=270, labelpad=20, fontweight='bold')

    # Add title
    ax.set_title('Accuracy Heatmap: All Users × All Algorithms',
                fontsize=14, fontweight='bold', pad=20)

    # Add grid
    ax.set_xticks(np.arange(len(algorithms)) - 0.5, minor=True)
    ax.set_yticks(np.arange(len(user_ids)) - 0.5, minor=True)
    ax.grid(which="minor", color="white", linestyle='-', linewidth=2)

    plt.tight_layout()

    output_file = os.path.join(output_dir, 'accuracy_heatmap_all_users.png')
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"✓ Generated: {output_file}")


def create_best_model_summary(users_data, output_dir='thesis_figures'):
    """Create summary showing which model was selected for each user."""

    os.makedirs(output_dir, exist_ok=True)

    # Count selections
    model_selections = defaultdict(int)

    for user_id, user_info in users_data.items():
        for algo, metrics in user_info['algorithms'].items():
            if metrics['selected']:
                model_selections[algo] += 1

    # Create pie chart
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7))

    # Pie chart of model selections
    # Color mapping for all 5 algorithms
    color_map = {
        'OneClassSVM': '#3498db',
        'IsolationForest': '#e74c3c',
        'MLPClassifier': '#2ecc71',
        'RandomForest': '#9b59b6',
        'GradientBoosting': '#f39c12'
    }
    colors = [color_map.get(algo, '#95a5a6') for algo in model_selections.keys()]

    wedges, texts, autotexts = ax1.pie(
        model_selections.values(),
        labels=model_selections.keys(),
        autopct='%1.1f%%',
        colors=colors,
        startangle=90,
        textprops={'fontsize': 12, 'fontweight': 'bold'}
    )

    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontsize(14)
        autotext.set_fontweight('bold')

    ax1.set_title('Selected Models Distribution\nAcross All Users',
                 fontsize=14, fontweight='bold')

    # Bar chart of average performance
    algorithms = list(model_selections.keys())
    avg_accuracy = []
    avg_eer = []

    for algo in algorithms:
        accuracies = [user_info['algorithms'][algo]['accuracy']
                     for user_info in users_data.values()
                     if algo in user_info['algorithms']]
        eers = [user_info['algorithms'][algo]['eer']
               for user_info in users_data.values()
               if algo in user_info['algorithms']]

        avg_accuracy.append(np.mean(accuracies))
        avg_eer.append(np.mean(eers))

    x = np.arange(len(algorithms))
    width = 0.35

    bars1 = ax2.bar(x - width/2, avg_accuracy, width, label='Avg Accuracy (%)',
                   color=colors, alpha=0.8, edgecolor='black')
    bars2 = ax2.bar(x + width/2, avg_eer, width, label='Avg EER (%)',
                   color=colors, alpha=0.5, edgecolor='black')

    ax2.set_ylabel('Percentage (%)', fontsize=12, fontweight='bold')
    ax2.set_title('Average Performance Metrics', fontsize=14, fontweight='bold')
    ax2.set_xticks(x)
    ax2.set_xticklabels(algorithms, fontsize=11)
    ax2.legend(fontsize=11)
    ax2.grid(axis='y', alpha=0.3, linestyle='--')

    # Add value labels
    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.1f}%', ha='center', va='bottom', fontsize=9)

    plt.tight_layout()

    output_file = os.path.join(output_dir, 'best_model_summary.png')
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"✓ Generated: {output_file}")

    # Print summary
    print(f"\n{'='*80}")
    print("Model Selection Summary")
    print(f"{'='*80}")
    for algo, count in model_selections.items():
        print(f"{algo:25s}: {count:2d} users ({count/len(users_data)*100:.1f}%)")
    print(f"{'='*80}\n")


def create_top_performers(users_data, output_dir='thesis_figures', top_n=10):
    """Create chart showing top-performing users."""

    os.makedirs(output_dir, exist_ok=True)

    # Get best accuracy for each user
    user_best = []
    for user_id, user_info in users_data.items():
        best_acc = max(metrics['accuracy'] for metrics in user_info['algorithms'].values())
        best_algo = [algo for algo, metrics in user_info['algorithms'].items()
                    if metrics['accuracy'] == best_acc][0]

        user_best.append({
            'id': user_id,
            'name': user_info['name'],
            'accuracy': best_acc,
            'algorithm': best_algo
        })

    # Sort by accuracy
    user_best.sort(key=lambda x: x['accuracy'], reverse=True)
    top_users = user_best[:top_n]

    # Create bar chart
    fig, ax = plt.subplots(figsize=(12, 8))

    colors_map = {
        'OneClassSVM': '#3498db',
        'IsolationForest': '#e74c3c',
        'MLPClassifier': '#2ecc71',
        'RandomForest': '#9b59b6',
        'GradientBoosting': '#f39c12'
    }

    y_pos = np.arange(len(top_users))
    accuracies = [u['accuracy'] for u in top_users]
    bar_colors = [colors_map[u['algorithm']] for u in top_users]

    bars = ax.barh(y_pos, accuracies, color=bar_colors, edgecolor='black',
                  linewidth=1.5, alpha=0.8)

    ax.set_yticks(y_pos)
    ax.set_yticklabels([f"{u['name']}\n(ID: {u['id']})" for u in top_users],
                       fontsize=9)
    ax.invert_yaxis()
    ax.set_xlabel('Best Accuracy (%)', fontsize=12, fontweight='bold')
    ax.set_title(f'Top {top_n} Users by Best Model Accuracy',
                fontsize=14, fontweight='bold')
    ax.grid(axis='x', alpha=0.3, linestyle='--')
    ax.set_xlim(0, 105)

    # Add value labels
    for i, (bar, user) in enumerate(zip(bars, top_users)):
        width = bar.get_width()
        ax.text(width + 1, bar.get_y() + bar.get_height()/2,
               f"{width:.1f}% ({user['algorithm']})",
               ha='left', va='center', fontsize=8, fontweight='bold')

    # Add legend
    legend_elements = [mpatches.Patch(facecolor=color, edgecolor='black', label=algo)
                      for algo, color in colors_map.items()]
    ax.legend(handles=legend_elements, loc='lower right', fontsize=10)

    plt.tight_layout()

    output_file = os.path.join(output_dir, f'top_{top_n}_users.png')
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"✓ Generated: {output_file}")


def main():
    """Main function to generate all visualizations."""

    # Find the most recent CSV file
    csv_files = [f for f in os.listdir('.')
                if f.startswith('thesis_ml_metrics_') and f.endswith('.csv')]

    if not csv_files:
        print("❌ Error: No thesis_ml_metrics CSV file found!")
        print("Please run export_thesis_metrics.py first.")
        return

    csv_files.sort(reverse=True)
    csv_file = csv_files[0]

    print(f"\n{'='*80}")
    print(f"BioAuthAI - Per-User Performance Visualization")
    print(f"{'='*80}")
    print(f"Reading data from: {csv_file}\n")

    # Load data
    users_data = load_data(csv_file)
    print(f"Loaded data for {len(users_data)} users\n")

    # Create output directory
    output_dir = 'thesis_figures'
    os.makedirs(output_dir, exist_ok=True)

    # Generate all visualizations
    print("Generating visualizations...\n")

    create_per_user_comparison(users_data, output_dir)
    create_overall_heatmap(users_data, output_dir)
    create_best_model_summary(users_data, output_dir)
    create_top_performers(users_data, output_dir, top_n=15)

    print(f"\n{'='*80}")
    print(f"✓ All Visualizations Complete!")
    print(f"{'='*80}")
    print(f"\nOutput directory: {os.path.abspath(output_dir)}")
    print(f"\nGenerated files:")
    print(f"  - Individual user comparisons (first 10 users)")
    print(f"  - Accuracy heatmap (all users)")
    print(f"  - Best model summary (pie + bar chart)")
    print(f"  - Top 15 performers")
    print(f"\n{'='*80}\n")


if __name__ == "__main__":
    main()
