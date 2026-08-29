# Objective 1 Analysis Summary

- Total records: 3000
- Modeling records after cleaning: 3000
- Failure rate: 0.1297
- Logistic ROC-AUC: 0.6160

## Top associated parameters (absolute point-biserial)

| feature            |   point_biserial_corr |     p_value |
|:-------------------|----------------------:|------------:|
| duration_sec       |             0.247491  | 4.15939e-43 |
| run_attempt        |             0.141287  | 7.58063e-15 |
| commit_message_len |             0.026155  | 0.152082    |
| deletions          |             0.0128807 | 0.480662    |
| total_changes      |             0.0113568 | 0.534075    |

## Classification report

```
              precision    recall  f1-score   support

           0     0.8802    0.9949    0.9341       783
           1     0.7333    0.0940    0.1667       117

    accuracy                         0.8778       900
   macro avg     0.8068    0.5445    0.5504       900
weighted avg     0.8611    0.8778    0.8343       900

```
