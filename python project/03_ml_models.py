"""
=============================================================
STEP 3 — MACHINE LEARNING MODEL BUILDING
Predictive Modeling & Model Validation Framework
=============================================================

Algorithms:
  1. Logistic Regression  (baseline)
  2. Decision Tree
  3. Random Forest        (best interpretable)
  4. XGBoost              (top performer)

Target Variable:
  IsOverdue — whether a loan is in default/overdue status

Features:
  PrincipalAmount_INR, InterestRate, LoanToBalanceRatio,
  TxnFrequency_90d, AvgTxnAmount_INR, AccountTypeID,
  LoanDurationDays

Output:
  • Classification reports printed to console
  • ROC-AUC comparison plot saved
  • Best model saved to /models/best_model.pkl

Run:  python 03_ml_models.py
"""

import os
import json
import joblib
import warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

from sklearn.model_selection     import train_test_split, StratifiedKFold, cross_val_score
from sklearn.preprocessing       import StandardScaler, LabelEncoder
from sklearn.linear_model        import LogisticRegression
from sklearn.tree                import DecisionTreeClassifier
from sklearn.ensemble            import RandomForestClassifier
from sklearn.metrics             import (
    classification_report, confusion_matrix,
    roc_auc_score, roc_curve, accuracy_score,
    precision_score, recall_score, f1_score
)
try:
    from xgboost import XGBClassifier
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    print("  [INFO] XGBoost not installed — skipping XGBClassifier")

warnings.filterwarnings('ignore')

# -- Config ------------------------------------------------─
CLEAN_DIR = os.path.join(os.path.dirname(__file__), 'cleaned')
MODEL_DIR = os.path.join(os.path.dirname(__file__), 'models')
CHART_DIR = os.path.join(os.path.dirname(__file__), 'reports', 'ml_charts')
os.makedirs(MODEL_DIR, exist_ok=True)
os.makedirs(CHART_DIR, exist_ok=True)

plt.style.use('dark_background')
COLORS = ['#6366f1', '#10b981', '#f59e0b', '#ef4444']

print("=" * 60)
print("BANKGUARD — Step 3: Machine Learning")
print("=" * 60)

# -- 1. Load & Merge Feature Table ------------------------─
accounts = pd.read_csv(os.path.join(CLEAN_DIR, 'accounts_clean.csv'))
loans    = pd.read_csv(os.path.join(CLEAN_DIR, 'loans_clean.csv'))

# Join accounts to loans
df = loans.merge(
    accounts[['AccountID', 'AccountTypeID', 'Balance_INR',
              'TxnFrequency_90d', 'AvgTxnAmount_INR']],
    on='AccountID', how='left'
)

# Loan duration in days
df['StartDate']        = pd.to_datetime(df['StartDate'], errors='coerce')
df['EstimatedEndDate'] = pd.to_datetime(df['EstimatedEndDate'], errors='coerce')
df['LoanDurationDays'] = (df['EstimatedEndDate'] - df['StartDate']).dt.days.fillna(365)

print(f"\n  Feature table: {len(df)} rows x {df.shape[1]} columns")
print(f"  Class balance: {df['IsOverdue'].sum()} overdue / {(~df['IsOverdue'].astype(bool)).sum()} non-overdue")

# -- 2. Feature Engineering --------------------------------─
FEATURES = [
    'PrincipalAmount_INR',
    'InterestRate',
    'LoanToBalanceRatio',
    'TxnFrequency_90d',
    'AvgTxnAmount_INR',
    'AccountTypeID',
    'LoanDurationDays',
]
TARGET = 'IsOverdue'

# Fill any remaining NaNs
for col in FEATURES:
    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(df[col].median() if col != 'AccountTypeID' else 1)

X = df[FEATURES].values
y = df[TARGET].values

print(f"\n  Features used: {FEATURES}")

# -- 3. Train / Test Split (80:20) --------------------------
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.20, random_state=42, stratify=y
)
print(f"\n  Train size: {len(X_train)}  |  Test size: {len(X_test)}")

# -- 4. Scaling (for Logistic Regression) ------------------
scaler  = StandardScaler()
X_train_sc = scaler.fit_transform(X_train)
X_test_sc  = scaler.transform(X_test)

# -- 5. Define Models --------------------------------------─
models = {
    'Logistic Regression': LogisticRegression(max_iter=1000, class_weight='balanced', random_state=42),
    'Decision Tree':       DecisionTreeClassifier(max_depth=6, class_weight='balanced', random_state=42),
    'Random Forest':       RandomForestClassifier(n_estimators=200, max_depth=8, class_weight='balanced',
                                                  random_state=42, n_jobs=-1),
}
if XGBOOST_AVAILABLE:
    scale_ratio = (y == 0).sum() / (y == 1).sum()
    models['XGBoost'] = XGBClassifier(
        n_estimators=200, max_depth=6, learning_rate=0.1,
        scale_pos_weight=scale_ratio, random_state=42,
        eval_metric='logloss', verbosity=0
    )

# -- 6. Train & Evaluate ------------------------------------
results = {}
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

print()
print("=" * 60)
for name, model in models.items():
    print(f"\n-- {name} --")

    # Use scaled features for Logistic Regression
    Xtr = X_train_sc if name == 'Logistic Regression' else X_train
    Xte = X_test_sc  if name == 'Logistic Regression' else X_test

    # Fit
    model.fit(Xtr, y_train)
    y_pred  = model.predict(Xte)
    y_proba = model.predict_proba(Xte)[:, 1]

    # Metrics
    acc  = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred, zero_division=0)
    rec  = recall_score(y_test, y_pred, zero_division=0)
    f1   = f1_score(y_test, y_pred, zero_division=0)
    auc  = roc_auc_score(y_test, y_proba)

    # 5-fold cross-validated AUC
    cv_auc = cross_val_score(model, Xtr, y_train, cv=cv, scoring='roc_auc').mean()

    print(f"  Accuracy  : {acc:.4f}  ({acc*100:.1f}%)")
    print(f"  Precision : {prec:.4f}  ({prec*100:.1f}%)")
    print(f"  Recall    : {rec:.4f}  ({rec*100:.1f}%)")
    print(f"  F1-Score  : {f1:.4f}  ({f1*100:.1f}%)")
    print(f"  ROC-AUC   : {auc:.4f}")
    print(f"  CV-AUC(5x): {cv_auc:.4f}")

    results[name] = {
        'model':     model,
        'accuracy':  round(acc, 4),
        'precision': round(prec, 4),
        'recall':    round(rec, 4),
        'f1':        round(f1, 4),
        'roc_auc':   round(auc, 4),
        'cv_auc':    round(cv_auc, 4),
        'y_proba':   y_proba,
        'fpr_tpr':   roc_curve(y_test, y_proba)[:2],
    }

    print("  Classification Report:")
    print(classification_report(y_test, y_pred, target_names=['Not Overdue','Overdue'],
                                 zero_division=0))

# -- 7. Pick Best Model ------------------------------------─
best_name = max(results, key=lambda k: results[k]['roc_auc'])
best_model = results[best_name]['model']
print(f"\n{'=' * 60}")
print(f"  BEST MODEL: {best_name}  (ROC-AUC = {results[best_name]['roc_auc']:.4f})")
print(f"{'=' * 60}")

# Save best model + scaler
joblib.dump(best_model, os.path.join(MODEL_DIR, 'best_model.pkl'))
joblib.dump(scaler,     os.path.join(MODEL_DIR, 'scaler.pkl'))

# Save feature list for API
with open(os.path.join(MODEL_DIR, 'features.json'), 'w') as f:
    json.dump({'features': FEATURES, 'best_model': best_name}, f, indent=2)

print(f"  Model saved -> models/best_model.pkl")
print(f"  Scaler saved-> models/scaler.pkl")

# -- 8. Feature Importance (Random Forest) ------------------
if 'Random Forest' in results:
    rf = results['Random Forest']['model']
    fi = pd.Series(rf.feature_importances_, index=FEATURES).sort_values(ascending=True)
    print("\n  Random Forest Feature Importances:")
    for feat, imp in fi.items():
        bar = '#' * int(imp * 60)
        print(f"  {feat:25s}  {bar}  {imp:.4f}")

# -- 9. ROC Curve Plot ------------------------------------─
print("\n-- Plotting ROC curves --")
fig, axes = plt.subplots(1, 2, figsize=(14, 5), facecolor='#0a0b14')
fig.suptitle('Model Evaluation', fontsize=15, color='white')

for ax in axes:
    ax.set_facecolor('#131520')
    ax.tick_params(colors='#8892b0')
    for spine in ax.spines.values():
        spine.set_edgecolor('#1e2030')

# ROC curves
ax = axes[0]
ax.plot([0,1],[0,1],'--', color='#4a5568', linewidth=1, label='Random (0.5)')
for i, (name, res) in enumerate(results.items()):
    fpr, tpr = res['fpr_tpr']
    ax.plot(fpr, tpr, color=COLORS[i % 4], linewidth=2.5,
            label=f"{name} (AUC={res['roc_auc']:.3f})")
ax.set_title('ROC-AUC Curves', color='white', fontsize=11)
ax.set_xlabel('False Positive Rate', color='#8892b0')
ax.set_ylabel('True Positive Rate', color='#8892b0')
ax.legend(fontsize=9, facecolor='#1e2030', labelcolor='white')

# Metric comparison bar
ax = axes[1]
metrics = ['accuracy','precision','recall','f1','roc_auc']
x = np.arange(len(metrics))
width = 0.8 / len(results)
for i, (name, res) in enumerate(results.items()):
    vals = [res[m] for m in metrics]
    offset = (i - len(results)/2 + 0.5) * width
    bars = ax.bar(x + offset, vals, width * 0.9, label=name, color=COLORS[i % 4], alpha=0.9)

ax.set_xticks(x)
ax.set_xticklabels(['Acc','Prec','Rec','F1','AUC'], color='#8892b0')
ax.set_ylim(0, 1.15)
ax.set_title('Model Metric Comparison', color='white', fontsize=11)
ax.axhline(0.80, color='#6366f1', linestyle='--', linewidth=1, label='Target (0.80)')
ax.legend(fontsize=9, facecolor='#1e2030', labelcolor='white')

plt.tight_layout()
roc_path = os.path.join(CHART_DIR, 'model_evaluation.png')
plt.savefig(roc_path, dpi=120, bbox_inches='tight', facecolor='#0a0b14')
plt.close()
print(f"  Saved: {roc_path}")

# -- 10. Confusion Matrix ------------------------------------
fig, axes = plt.subplots(1, len(results), figsize=(5*len(results), 4), facecolor='#0a0b14')
if len(results) == 1:
    axes = [axes]
for ax, (name, res) in zip(axes, results.items()):
    ax.set_facecolor('#131520')
    Xte = X_test_sc if name == 'Logistic Regression' else X_test
    cm = confusion_matrix(y_test, res['model'].predict(Xte))
    sns_colors = plt.cm.Blues
    im = ax.imshow(cm, interpolation='nearest', cmap='Blues')
    ax.set_title(name, color='white', fontsize=10)
    ax.set_xlabel('Predicted', color='#8892b0')
    ax.set_ylabel('Actual', color='#8892b0')
    ax.set_xticks([0,1]); ax.set_yticks([0,1])
    ax.set_xticklabels(['Not OD','OD']); ax.set_yticklabels(['Not OD','OD'])
    ax.tick_params(colors='#8892b0')
    for i in range(2):
        for j in range(2):
            ax.text(j, i, str(cm[i,j]), ha='center', va='center',
                    color='white' if cm[i,j] < cm.max()/2 else 'black', fontsize=14, fontweight='bold')

plt.suptitle('Confusion Matrices', color='white', fontsize=14)
plt.tight_layout()
cm_path = os.path.join(CHART_DIR, 'confusion_matrices.png')
plt.savefig(cm_path, dpi=120, bbox_inches='tight', facecolor='#0a0b14')
plt.close()
print(f"  Saved: {cm_path}")

# -- Summary ------------------------------------------------
print()
print("=" * 60)
print("MODEL SUMMARY TABLE")
print("=" * 60)
print(f"  {'Model':<22} {'Accuracy':>9} {'Precision':>10} {'Recall':>8} {'F1':>6} {'AUC':>8} {'CV-AUC':>8}")
print(f"  {'-'*68}")
for name, res in results.items():
    flag = ' [BEST]' if name == best_name else ''
    print(f"  {name:<22} {res['accuracy']:>9.4f} {res['precision']:>10.4f} "
          f"{res['recall']:>8.4f} {res['f1']:>6.4f} {res['roc_auc']:>8.4f} {res['cv_auc']:>8.4f}{flag}")
print()
print("  Next step -> Run 04_flask_api.py")
