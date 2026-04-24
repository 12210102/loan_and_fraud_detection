"""
=============================================================
STEP 4 — FLASK REST API DEPLOYMENT
Operationalizing ML Models & REST Services
=============================================================

Endpoints:
  POST /api/predict/loan       → Loan default risk score
  POST /api/predict/fraud      → Fraud risk score
  GET  /api/health             → Health check
  GET  /api/stats              → Dataset-level statistics

Start:  python 04_flask_api.py
Test:   http://127.0.0.1:5000/api/health
"""

import os
import json
import math
import joblib
import numpy as np
import pandas as pd
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS

# ── App Setup ──────────────────────────────────────────────
app = Flask(__name__, static_folder='../html project', static_url_path='')
CORS(app)   # Allow requests from Power BI / dashboard

BASE = os.path.dirname(__file__)
MODEL_DIR = os.path.join(BASE, 'models')
CLEAN_DIR = os.path.join(BASE, 'cleaned')

# ── Load model & scaler ────────────────────────────────────
try:
    model  = joblib.load(os.path.join(MODEL_DIR, 'best_model.pkl'))
    scaler = joblib.load(os.path.join(MODEL_DIR, 'scaler.pkl'))
    with open(os.path.join(MODEL_DIR, 'features.json')) as f:
        meta = json.load(f)
    FEATURES   = meta['features']
    BEST_MODEL = meta['best_model']
    MODEL_READY = True
    print(f"[OK] Model loaded: {BEST_MODEL}")
except Exception as e:
    MODEL_READY = False
    model = scaler = None
    FEATURES = []
    BEST_MODEL = 'None'
    print(f"[ERROR] Model not found — run 03_ml_models.py first. ({e})")

# ── Helper: Rule-based fraud scorer ────────────────────────
def rule_based_fraud_score(amount_inr: float, hour: int,
                           tx_type: str, freq_24h: int,
                           loan_status: str) -> dict:
    """Heuristic fraud risk score matching the dashboard simulator."""
    score = 0
    factors = []

    # Amount thresholds (INR)
    if amount_inr > 4_200_000:
        score += 30; factors.append('Very High Amount (>₹42L)')
    elif amount_inr > 1_700_000:
        score += 20; factors.append('High Amount (>₹17L)')
    elif amount_inr > 420_000:
        score += 10; factors.append('Moderate Amount (>₹4.2L)')

    # Late-night transaction
    if 0 <= hour <= 5:
        score += 25; factors.append('Late Night Transaction')
    elif hour >= 22:
        score += 15; factors.append('Late Evening Transaction')

    # Transaction type
    if tx_type.lower() == 'withdrawal':
        score += 15; factors.append('Withdrawal Type')
    elif tx_type.lower() == 'transfer':
        score += 10; factors.append('Transfer Type')

    # Frequency
    if freq_24h > 20:
        score += 25; factors.append('High Frequency (>20/day)')
    elif freq_24h > 10:
        score += 15; factors.append('Elevated Frequency')
    elif freq_24h > 5:
        score += 5;  factors.append('Normal-High Frequency')

    # Loan status
    if loan_status.lower() == 'overdue':
        score += 20; factors.append('Overdue Loan')
    elif loan_status.lower() == 'none':
        score += 5;  factors.append('No Loan History')

    score = min(score, 100)

    if score < 25:    risk_level, verdict = 'LOW',      'Transaction appears normal'
    elif score < 50:  risk_level, verdict = 'MODERATE', 'Flagged for manual review'
    elif score < 75:  risk_level, verdict = 'HIGH',     'High risk — manual review required'
    else:             risk_level, verdict = 'CRITICAL', 'Block transaction immediately'

    return {
        'fraud_score': score,
        'risk_level':  risk_level,
        'verdict':     verdict,
        'factors':     factors,
    }

# ── Statistics cache ───────────────────────────────────────
_stats_cache = None

def get_stats():
    global _stats_cache
    if _stats_cache is not None:
        return _stats_cache
    try:
        accounts = pd.read_csv(os.path.join(CLEAN_DIR, 'accounts_clean.csv'))
        loans    = pd.read_csv(os.path.join(CLEAN_DIR, 'loans_clean.csv'))
        txns     = pd.read_csv(os.path.join(CLEAN_DIR, 'transactions_clean.csv'))
        _stats_cache = {
            'total_accounts':      int(len(accounts)),
            'total_balance_inr':   round(float(accounts['Balance_INR'].sum()), 2),
            'total_loans':         int(len(loans)),
            'overdue_loans':       int(loans['IsOverdue'].sum()),
            'overdue_rate_pct':    round(float(loans['IsOverdue'].mean()) * 100, 2),
            'total_principal_inr': round(float(loans['PrincipalAmount_INR'].sum()), 2),
            'avg_interest_rate':   round(float(loans['InterestRate'].mean()) * 100, 2),
            'total_transactions':  int(len(txns)),
            'total_volume_inr':    round(float(txns['Amount_INR'].sum()), 2),
            'avg_txn_amount_inr':  round(float(txns['Amount_INR'].mean()), 2),
        }
    except Exception as e:
        _stats_cache = {'error': str(e)}
    return _stats_cache

# ══════════════════════════════════════════════════════════
# ROUTES
# ══════════════════════════════════════════════════════════

@app.route('/', methods=['GET'])
def index():
    """Serve the main web dashboard dashboard directly."""
    return app.send_static_file('index.html')

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({
        'status':       'ok',
        'model_loaded': MODEL_READY,
        'best_model':   BEST_MODEL,
        'timestamp':    datetime.now().isoformat(),
        'version':      '1.0.0',
    })


@app.route('/api/stats', methods=['GET'])
def stats():
    """Return high-level portfolio statistics."""
    return jsonify(get_stats())


@app.route('/api/predict/loan', methods=['POST'])
def predict_loan():
    """
    Predict loan default risk using the trained ML model.

    Request body (JSON):
    {
        "principal_amount_inr": 840000,
        "interest_rate":        0.09,
        "loan_to_balance_ratio":0.75,
        "txn_frequency_90d":    12,
        "avg_txn_amount_inr":   50000,
        "account_type_id":      2,
        "loan_duration_days":   1460
    }

    Response:
    {
        "default_probability": 0.23,
        "risk_class":          "LOW",
        "model_used":          "Random Forest",
        "features_received":   {...}
    }
    """
    if not MODEL_READY:
        return jsonify({'error': 'Model not loaded. Run 03_ml_models.py first.'}), 503

    data = request.get_json(silent=True)
    if not data:
        return jsonify({'error': 'Invalid JSON body'}), 400

    # Map request keys to feature names
    key_map = {
        'PrincipalAmount_INR':  data.get('principal_amount_inr', 840000),
        'InterestRate':         data.get('interest_rate', 0.09),
        'LoanToBalanceRatio':   data.get('loan_to_balance_ratio', 0.5),
        'TxnFrequency_90d':     data.get('txn_frequency_90d', 5),
        'AvgTxnAmount_INR':     data.get('avg_txn_amount_inr', 50000),
        'AccountTypeID':        data.get('account_type_id', 1),
        'LoanDurationDays':     data.get('loan_duration_days', 365),
    }

    # Validate feature order
    try:
        row = np.array([[key_map[f] for f in FEATURES]], dtype=float)
    except Exception as e:
        return jsonify({'error': f'Feature mapping error: {e}'}), 400

    prob = float(model.predict_proba(row)[0][1])

    if prob < 0.25:    risk_class = 'LOW'
    elif prob < 0.50:  risk_class = 'MODERATE'
    elif prob < 0.75:  risk_class = 'HIGH'
    else:              risk_class = 'CRITICAL'

    return jsonify({
        'default_probability': round(prob, 4),
        'default_percentage':  round(prob * 100, 2),
        'risk_class':          risk_class,
        'model_used':          BEST_MODEL,
        'features_received':   key_map,
        'timestamp':           datetime.now().isoformat(),
    })


@app.route('/api/predict/fraud', methods=['POST'])
def predict_fraud():
    """
    Compute fraud risk score using rule-based + heuristic model.

    Request body (JSON):
    {
        "amount_inr":    500000,
        "hour":          2,
        "tx_type":       "withdrawal",
        "freq_24h":      15,
        "loan_status":   "overdue"
    }
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'error': 'Invalid JSON body'}), 400

    result = rule_based_fraud_score(
        amount_inr  = float(data.get('amount_inr', 0)),
        hour        = int(data.get('hour', 12)),
        tx_type     = str(data.get('tx_type', 'deposit')),
        freq_24h    = int(data.get('freq_24h', 0)),
        loan_status = str(data.get('loan_status', 'active')),
    )
    result['timestamp'] = datetime.now().isoformat()
    return jsonify(result)


@app.route('/api/accounts/summary', methods=['GET'])
def accounts_summary():
    """Return account-type and status breakdown."""
    try:
        accounts = pd.read_csv(os.path.join(CLEAN_DIR, 'accounts_clean.csv'))
        by_type   = accounts.groupby('AccountTypeID').agg(
            count=('AccountID', 'count'),
            total_balance=('Balance_INR', 'sum'),
            avg_balance=('Balance_INR', 'mean')
        ).reset_index().to_dict(orient='records')
        by_status = accounts.groupby('AccountStatusID').agg(
            count=('AccountID','count')
        ).reset_index().to_dict(orient='records')
        return jsonify({'by_type': by_type, 'by_status': by_status})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/transactions/monthly', methods=['GET'])
def transactions_monthly():
    """Return monthly transaction volumes for the last 12 months."""
    try:
        txns = pd.read_csv(os.path.join(CLEAN_DIR, 'transactions_clean.csv'),
                           parse_dates=['TransactionDate'])
        txns['YearMonth'] = txns['TransactionDate'].dt.to_period('M').astype(str)
        monthly = txns.groupby(['YearMonth', 'TransactionTypeID']).agg(
            count=('TransactionID', 'count'),
            volume_inr=('Amount_INR', 'sum')
        ).reset_index()
        last_12 = sorted(txns['YearMonth'].unique())[-12:]
        monthly = monthly[monthly['YearMonth'].isin(last_12)]
        return jsonify(monthly.to_dict(orient='records'))
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ── 404 Handler ────────────────────────────────────────────
@app.errorhandler(404)
def not_found(e):
    return jsonify({
        'error': 'Endpoint not found',
        'available_endpoints': [
            'GET  /api/health',
            'GET  /api/stats',
            'GET  /api/accounts/summary',
            'GET  /api/transactions/monthly',
            'POST /api/predict/loan',
            'POST /api/predict/fraud',
        ]
    }), 404


# ── Run ────────────────────────────────────────────────────
if __name__ == '__main__':
    print()
    print("=" * 60)
    print("BANKGUARD Flask API — Starting")
    print("=" * 60)
    print(f"  Model loaded : {MODEL_READY} ({BEST_MODEL})")
    print(f"  Endpoints:")
    print(f"    GET  http://127.0.0.1:5000/api/health")
    print(f"    GET  http://127.0.0.1:5000/api/stats")
    print(f"    POST http://127.0.0.1:5000/api/predict/loan")
    print(f"    POST http://127.0.0.1:5000/api/predict/fraud")
    print(f"    GET  http://127.0.0.1:5000/api/accounts/summary")
    print(f"    GET  http://127.0.0.1:5000/api/transactions/monthly")
    print("=" * 60)
    app.run(debug=True, host='0.0.0.0', port=5000)
