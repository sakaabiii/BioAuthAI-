# Machine Learning Model Performance Metrics

## Summary Across All Users

| Model | Accuracy | Precision | Recall | F1-Score | FAR | FRR | EER | Users |
|-------|----------|-----------|--------|----------|-----|-----|-----|-------|
| OneClassSVM            |    83.94% |    100.00% |    51.83% |     65.17% |    0.00% |   48.17% |   24.09% |    51 |
| IsolationForest        |    25.61% |      0.00% |    76.83% |      0.00% |  100.00% |   23.17% |   61.59% |    51 |
| MLPClassifier          |    99.86% |    100.00% |    99.57% |     99.78% |    0.00% |    0.43% |    0.21% |    51 |

## Metric Definitions

- **Accuracy**: Overall classification accuracy (TP+TN)/(Total)
- **Precision**: Proportion of genuine predictions that are correct (1 - FAR)
- **Recall**: Proportion of genuine samples correctly identified (1 - FRR)
- **F1-Score**: Harmonic mean of precision and recall
- **FAR** (False Accept Rate): Rate at which impostors are incorrectly accepted
- **FRR** (False Reject Rate): Rate at which genuine users are incorrectly rejected
- **EER** (Equal Error Rate): Point where FAR = FRR (lower is better)

## Key Findings

1. **MLPClassifier** (Neural Network) achieved the highest performance:
   - 99.86% accuracy
   - 0.21% EER (Equal Error Rate)
   - Nearly perfect precision and recall

2. **OneClassSVM** showed moderate performance:
   - 83.94% accuracy
   - 24.09% EER
   - Good for unsupervised anomaly detection

3. **IsolationForest** had lower performance:
   - 25.61% accuracy
   - 61.59% EER
   - High false accept rate (100%)