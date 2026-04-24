# Power BI Dashboard — Setup Guide

## BankGuard Analytics | Loan & Fraud Detection

This guide walks you through building **4 Power BI dashboards** connected to the `bankguard` MySQL database.

---

## Prerequisites

| Tool | Version |
|---|---|
| Power BI Desktop | Latest (free) |
| MySQL Server | 8.0+ |
| MySQL ODBC Connector | 8.0+ |
| MySQL Workbench | Optional |

**Download Power BI Desktop:** https://powerbi.microsoft.com/downloads/

---

## Step 1 — Connect Power BI to MySQL

1. Open **Power BI Desktop**
2. Click **Home → Get Data → More...**
3. Search for **MySQL database** → Connect
4. Enter:
   - Server: `localhost`
   - Database: `bankguard`
5. Click **OK** → enter your MySQL username/password
6. In **Navigator**, select all tables:
   - `customers`, `accounts`, `loans`, `transactions`
   - `branches`, `addresses`
   - `account_types`, `account_statuses`, `loan_statuses`
   - `transaction_types`, `customer_types`

---

## Step 2 — Set Up Relationships (Data Model)

Go to **Model View** and create these relationships:

```
customers      → accounts       (CustomerID,  1:N)
accounts       → loans          (AccountID,   1:N)
accounts       → transactions   (AccountID,   1:N)  [via AccountOriginID]
branches       → transactions   (BranchID,    1:N)
account_types  → accounts       (AccountTypeID, 1:N)
account_statuses → accounts     (AccountStatusID, 1:N)
loan_statuses  → loans          (LoanStatusID, 1:N)
transaction_types → transactions (TransactionTypeID, 1:N)
customer_types → customers      (CustomerTypeID, 1:N)
addresses      → customers      (AddressID,   1:N)
addresses      → branches       (AddressID,   1:N)
```

---

## Step 3 — Create These DAX Measures

In the **Data** pane, add a new table called `_Measures` and add:

```dax
-- Total Portfolio Balance (₹ Crore)
Total Balance Cr =
DIVIDE(SUM(accounts[Balance_INR]), 10000000, 0)

-- Total Loan Outstanding (₹ Crore)
Total Loans Cr =
DIVIDE(SUM(loans[PrincipalAmount_INR]), 10000000, 0)

-- Overdue Loan Rate
Overdue Rate % =
DIVIDE(
    CALCULATE(COUNT(loans[LoanID]), loans[IsOverdue] = 1),
    COUNT(loans[LoanID]),
    0
) * 100

-- Average Interest Rate
Avg Interest Rate =
AVERAGE(loans[InterestRate]) * 100

-- Total Transaction Volume (₹ Crore)
Total Txn Volume Cr =
DIVIDE(SUM(transactions[Amount_INR]), 10000000, 0)

-- Late Night Transaction %
Late Night Txn % =
DIVIDE(
    CALCULATE(COUNT(transactions[TransactionID]),
              transactions[TxnHour] <= 5),
    COUNT(transactions[TransactionID]),
    0
) * 100

-- Month-over-Month Volume Change
MoM Volume Change % =
VAR CurrentMonth = CALCULATE(SUM(transactions[Amount_INR]),
                              DATESMTD(transactions[TransactionDate]))
VAR PrevMonth = CALCULATE(SUM(transactions[Amount_INR]),
                           DATEADD(DATESMTD(transactions[TransactionDate]), -1, MONTH))
RETURN DIVIDE(CurrentMonth - PrevMonth, PrevMonth, 0) * 100
```

---

## Step 4 — Build the 4 Dashboards

---

### Dashboard 1: Executive Summary

**Visuals to create:**

| Visual | Fields | Purpose |
|---|---|---|
| Card | `[Total Balance Cr]` | AUM in ₹ Crore |
| Card | `COUNT(customers[CustomerID])` | Total customers |
| Card | `COUNT(accounts[AccountID])` | Total accounts |
| Card | `[Overdue Rate %]` | Default rate |
| Card | `COUNT(transactions[TransactionID])` | Total transactions |
| Donut Chart | `customer_types[TypeName]`, count | Customer segments |
| Donut Chart | `account_statuses[StatusName]`, count | Account status |
| Line Chart | `TransactionDate` (Month), `Amount_INR` | Monthly trend |
| Stacked Bar | `account_types[TypeName]`, `Balance_INR` | Balance by type |

**Filters/Slicers:**
- Date range slicer on `transactions[TransactionDate]`
- `account_types[TypeName]` dropdown
- `customer_types[TypeName]` dropdown

---

### Dashboard 2: Loan Risk Dashboard

**Visuals to create:**

| Visual | Fields | Purpose |
|---|---|---|
| Donut Chart | `loan_statuses[StatusName]`, count | Loan status split |
| Clustered Bar | Interest rate band formula, count | Rate distribution |
| Clustered Bar | `account_types[TypeName]`, `[Overdue Rate %]` | Risk by type |
| Table | LoanID, Customer, Principal, Rate, Status, DaysOverdue | Overdue detail |
| Gauge | `[Overdue Rate %]`, max=30 | Default rate gauge |
| Card | `[Avg Interest Rate]` | Avg rate |
| Card | `[Total Loans Cr]` | Portfolio size |
| Scatter | `InterestRate`, `LoanToBalanceRatio`, colour=`IsOverdue` | Risk scatter |

**Conditional Formatting:**
- Table rows: Red background when `IsOverdue = 1`
- Gauge: Red zone > 15%

---

### Dashboard 3: Fraud Monitoring Dashboard

**Visuals to create:**

| Visual | Fields | Purpose |
|---|---|---|
| KPI Card | `[Late Night Txn %]` | Suspicious timing |
| Bar Chart | `TxnHour`, count | Transactions by hour |
| Map | `addresses[City]`, transaction count | Geographic heatmap |
| Table | fraud_alerts (if populated) | Alert log |
| Donut | Risk level distribution from `ml_predictions` | ML risk split |
| Line | Monthly `[Late Night Txn %]` | Trend over time |
| Clustered Bar | `transaction_types[TypeName]`, amount | Type risk comparison |

**Alerts:**
- Set **Data Alert** on Late Night Txn % card → notify if > 10%

---

### Dashboard 4: Branch Performance Dashboard

**Visuals to create:**

| Visual | Fields | Purpose |
|---|---|---|
| Bar Chart | `branches[BranchName]`, Volume_Crore | Top branches |
| Map | `addresses[City]`, transaction volume | Geographic distribution |
| Table | Branch, City, TxnCount, Volume, AvgAmount, Rank | Full scorecard |
| KPI | Branch volume vs prior period | MoM comparison |
| Clustered Bar | BranchName, count by TransactionType | Type breakdown |

---

## Step 5 — Refresh & Publish

### Auto-Refresh Setup:
1. **File → Publish → Publish to Power BI Service**
2. In Power BI Service → **Datasets → Settings**
3. Set **Scheduled Refresh** → Daily at 6:00 AM
4. Configure MySQL ODBC gateway

### Direct Query Mode (optional, for real-time):
- In **Power Query Editor**: change connection to **DirectQuery**
- This queries MySQL live without caching

---

## Step 6 — Mobile Layout

1. Go to **View → Mobile Layout**
2. Resize KPI cards to top row
3. Stack charts vertically
4. Publish mobile-optimised report

---

## Color Theme (matches dashboard)

Import this JSON theme in Power BI (View → Themes → Browse):

```json
{
  "name": "BankGuard Dark",
  "background": "#0a0b14",
  "foreground": "#e8eaf6",
  "tableAccent": "#6366f1",
  "dataColors": [
    "#6366f1", "#10b981", "#f59e0b",
    "#ef4444", "#8b5cf6", "#3b82f6",
    "#06b6d4", "#f43f5e"
  ],
  "visualStyles": {
    "*": {
      "*": {
        "background": [{ "color": "#131520" }],
        "border": [{ "color": "#1e2030" }]
      }
    }
  }
}
```

Save this as `bankguard_theme.json` and import it.

---

## Quick Connection String

Use this in **Power BI Advanced Options** or Python:

```
mysql+mysqlconnector://root:<password>@localhost:3306/bankguard
```

Or for ODBC:
```
Driver={MySQL ODBC 8.0 ANSI Driver};Server=localhost;Database=bankguard;User=root;Password=<password>;
```

---

## Report Pages Summary

| Page | SQL Query Used | Key Metric |
|---|---|---|
| Executive Summary | Q1, Q2, Q3 | Total AUM, Customer Count |
| Transaction Analytics | Q4, Q5, Q6, Q7 | Monthly Volume, Branch Rank |
| Loan Risk | Q8, Q9, Q10, Q11 | Overdue Rate, Interest Bands |
| Account Intelligence | Q12, Q13 | Balance Distribution |
| Branch Performance | Q14 | Volume Rank, Late Night % |
| Data Quality | Q15 | Null/Duplicate counts |
