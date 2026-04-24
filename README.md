# BankGuard Analytics — Banking Loan & Fraud Detection

## 🏦 Project Overview

A complete end-to-end banking analytics project covering:
- **Data Cleaning** (Python + Pandas)
- **SQL Database** (MySQL — schema + analytical queries)
- **Machine Learning** (Logistic Regression, Decision Tree, Random Forest, XGBoost)
- **REST API** (Flask — deployed model + fraud scorer)
- **Web Dashboard** (HTML/CSS/JS + Chart.js — INR ₹)
- **Power BI Reports** (4 dashboards connected to MySQL)

---

## 📁 Project Structure (Organised for Deployment)

```
college project/
│
├── html project/            ← Web project files
│   ├── index.html           ← Main dashboard
│   ├── style.css            ← Modern premium styling
│   └── app.js               ← Interactive logic (₹ INR)
│
├── python project/          ← Python project files
│   ├── app.py               ← Flask REST API (Entry point for Render)
│   ├── 01_data_cleaning.py  ← Data preparation script
│   ├── 02_eda_analysis.py   ← Exploratory analysis script
│   ├── 03_ml_models.py      ← Model training script
│   ├── requirements.txt     ← Dependencies (includes gunicorn)
│   │
│   ├── sql/                 ← SQL schema & queries
│   ├── cleaned/             ← Cleaned datasets (INR)
│   ├── models/              ← Best performing ML models (.pkl)
│   ├── reports/             ← Visual performance charts
│   └── uploaded to kaggle/  ← Raw source data
│
└── powerbi/                 ← Power BI documentation
```

---

## ⚡ Quick Start (Local Backend)

### 1. Setup Environment
```powershell
cd 'python project'
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Run Pipeline
```powershell
python 01_data_cleaning.py
python 02_eda_analysis.py
python 03_ml_models.py
python app.py
```

---

## 🌐 Deployment Logic

### GitHub
1. Create a new repository on GitHub.
2. Initialise and push this folder:
   ```bash
   git init
   git add .
   git commit -m "Organised project with python and html folders"
   git remote add origin <your-repo-url>
   git push -u origin main
   ```

### Render (Deploying the API)
1. Link your GitHub repo to Render.com.
2. Create a **Web Service**.
3. **Build Command:** `pip install -r 'python project/requirements.txt'`
4. **Start Command:** `gunicorn --directory 'python project' app:app`

---

## 📊 Web Dashboard
Simply open `html project/index.html` in any browser. It is designed to work with the Python API for real-time predictions.

---

## 🤖 ML Model Results

| Model | Accuracy | ROC-AUC | CV-AUC |
|---|---|---|---|
| Logistic Regression | ~81% | ~0.81 | ~0.80 |
| Decision Tree | ~83% | ~0.83 | ~0.82 |
| Random Forest ⭐ | ~94% | ~0.94 | ~0.93 |
| XGBoost 🏆 | ~96% | ~0.96 | ~0.95 |
