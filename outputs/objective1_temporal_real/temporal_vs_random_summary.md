# Temporal vs Random Split Evaluation

- Modeling records: 3000
- Event-time column: `created_at`
- Chronological boundary: 2026-08-27 19:47:00+00:00
- Overall failure rate: 0.1297

## Chronological split (oldest 70% train, newest 30% test)

- Train records: 2100 (failure rate 0.1595)
- Test records: 900 (failure rate 0.0600)
- ROC-AUC: 0.6886

```
              precision    recall  f1-score   support

           0     0.9400    1.0000    0.9691       846
           1     0.0000    0.0000    0.0000        54

    accuracy                         0.9400       900
   macro avg     0.4700    0.5000    0.4845       900
weighted avg     0.8836    0.9400    0.9109       900

```

## Random stratified holdout (seed 42)

- Train records: 2100 (failure rate 0.1295)
- Test records: 900 (failure rate 0.1300)
- ROC-AUC: 0.6160

```
              precision    recall  f1-score   support

           0     0.8802    0.9949    0.9341       783
           1     0.7333    0.0940    0.1667       117

    accuracy                         0.8778       900
   macro avg     0.8068    0.5445    0.5504       900
weighted avg     0.8611    0.8778    0.8343       900

```
