-- =============================================================
-- BANKGUARD ANALYTICS — ANALYTICAL SQL QUERIES
-- These 15 queries power the Power BI dashboards
-- =============================================================
-- Usage: Run in MySQL Workbench or connect via Power BI
-- Database: bankguard
-- =============================================================

USE bankguard;

-- ─────────────────────────────────────────────────────────────
-- EXECUTIVE DASHBOARD QUERIES
-- ─────────────────────────────────────────────────────────────

-- Q1: KPI Summary Card
SELECT
    COUNT(DISTINCT c.CustomerID)                    AS TotalCustomers,
    COUNT(DISTINCT a.AccountID)                     AS TotalAccounts,
    ROUND(SUM(a.Balance_INR), 2)                    AS TotalPortfolio_INR,
    ROUND(SUM(l.PrincipalAmount_INR), 2)            AS TotalLoans_INR,
    COUNT(DISTINCT l.LoanID)                        AS TotalLoans,
    SUM(CASE WHEN l.IsOverdue = 1 THEN 1 ELSE 0 END) AS OverdueLoans,
    ROUND(AVG(l.InterestRate) * 100, 2)             AS AvgInterestRate_Pct,
    (SELECT COUNT(*) FROM transactions)             AS TotalTransactions
FROM customers c
LEFT JOIN accounts a ON c.CustomerID = a.CustomerID
LEFT JOIN loans   l ON a.AccountID   = l.AccountID;


-- Q2: Customer Type Distribution
SELECT
    ct.TypeName                     AS CustomerType,
    COUNT(c.CustomerID)             AS CustomerCount,
    ROUND(COUNT(c.CustomerID)*100.0
        / (SELECT COUNT(*) FROM customers), 2) AS Percentage
FROM customers c
JOIN customer_types ct ON c.CustomerTypeID = ct.CustomerTypeID
GROUP BY ct.TypeName
ORDER BY CustomerCount DESC;


-- Q3: Account Status Summary
SELECT
    ast.StatusName                  AS AccountStatus,
    COUNT(a.AccountID)              AS AccountCount,
    ROUND(SUM(a.Balance_INR), 2)    AS TotalBalance_INR,
    ROUND(AVG(a.Balance_INR), 2)    AS AvgBalance_INR
FROM accounts a
JOIN account_statuses ast ON a.AccountStatusID = ast.AccountStatusID
GROUP BY ast.StatusName
ORDER BY AccountCount DESC;


-- ─────────────────────────────────────────────────────────────
-- TRANSACTION ANALYTICS QUERIES
-- ─────────────────────────────────────────────────────────────

-- Q4: Monthly Transaction Volume (last 12 months)
SELECT
    DATE_FORMAT(TransactionDate, '%Y-%m')   AS YearMonth,
    tt.TypeName                             AS TransactionType,
    COUNT(t.TransactionID)                  AS TxnCount,
    ROUND(SUM(t.Amount_INR), 2)             AS Volume_INR
FROM transactions t
JOIN transaction_types tt ON t.TransactionTypeID = tt.TransactionTypeID
WHERE TransactionDate >= DATE_SUB(NOW(), INTERVAL 12 MONTH)
GROUP BY YearMonth, tt.TypeName
ORDER BY YearMonth, tt.TypeName;


-- Q5: Transaction Volume by Hour (fraud pattern analysis)
SELECT
    TxnHour                                 AS HourOfDay,
    COUNT(TransactionID)                    AS TxnCount,
    ROUND(SUM(Amount_INR), 2)               AS Volume_INR,
    ROUND(AVG(Amount_INR), 2)               AS AvgAmount_INR,
    CASE
        WHEN TxnHour BETWEEN 0 AND 5   THEN 'Late Night (High Risk)'
        WHEN TxnHour BETWEEN 6 AND 11  THEN 'Morning'
        WHEN TxnHour BETWEEN 12 AND 17 THEN 'Afternoon'
        WHEN TxnHour BETWEEN 18 AND 21 THEN 'Evening'
        ELSE 'Late Evening'
    END                                     AS TimeSegment
FROM transactions
GROUP BY TxnHour
ORDER BY TxnHour;


-- Q6: Top 10 Branches by Transaction Volume
SELECT
    b.BranchID,
    b.BranchName,
    a.City,
    COUNT(t.TransactionID)                  AS TxnCount,
    ROUND(SUM(t.Amount_INR), 2)             AS Volume_INR,
    ROUND(AVG(t.Amount_INR), 2)             AS AvgAmount_INR
FROM transactions t
JOIN branches b  ON t.BranchID   = b.BranchID
JOIN addresses a ON b.AddressID  = a.AddressID
GROUP BY b.BranchID, b.BranchName, a.City
ORDER BY Volume_INR DESC
LIMIT 10;


-- Q7: Transaction Type Annual Comparison
SELECT
    TxnYear                                 AS Year,
    tt.TypeName                             AS TransactionType,
    COUNT(t.TransactionID)                  AS TxnCount,
    ROUND(SUM(t.Amount_INR)/1e7, 2)         AS Volume_Crore
FROM transactions t
JOIN transaction_types tt ON t.TransactionTypeID = tt.TransactionTypeID
GROUP BY TxnYear, tt.TypeName
ORDER BY TxnYear, tt.TypeName;


-- ─────────────────────────────────────────────────────────────
-- LOAN RISK DASHBOARD QUERIES
-- ─────────────────────────────────────────────────────────────

-- Q8: Loan Portfolio Health
SELECT
    ls.StatusName                               AS LoanStatus,
    COUNT(l.LoanID)                             AS LoanCount,
    ROUND(SUM(l.PrincipalAmount_INR), 2)        AS TotalPrincipal_INR,
    ROUND(AVG(l.PrincipalAmount_INR), 2)        AS AvgPrincipal_INR,
    ROUND(AVG(l.InterestRate) * 100, 2)         AS AvgInterestRate_Pct,
    ROUND(AVG(l.LoanDurationDays), 0)           AS AvgDurationDays,
    ROUND(COUNT(l.LoanID)*100.0
        / (SELECT COUNT(*) FROM loans), 2)      AS Percentage
FROM loans l
JOIN loan_statuses ls ON l.LoanStatusID = ls.LoanStatusID
GROUP BY ls.StatusName
ORDER BY LoanCount DESC;


-- Q9: Loan Risk by Account Type (for Power BI heatmap)
SELECT
    at.TypeName                             AS AccountType,
    ls.StatusName                           AS LoanStatus,
    COUNT(l.LoanID)                         AS LoanCount,
    ROUND(AVG(l.InterestRate)*100, 2)       AS AvgInterestRate,
    ROUND(AVG(l.LoanToBalanceRatio), 4)     AS AvgLoanToBalanceRatio,
    ROUND(SUM(l.PrincipalAmount_INR)/1e5,2) AS TotalPrincipal_Lakh
FROM loans l
JOIN accounts a     ON l.AccountID     = a.AccountID
JOIN account_types at ON a.AccountTypeID = at.AccountTypeID
JOIN loan_statuses ls ON l.LoanStatusID  = ls.LoanStatusID
GROUP BY at.TypeName, ls.StatusName
ORDER BY at.TypeName, ls.StatusName;


-- Q10: Interest Rate Band Distribution
SELECT
    CASE
        WHEN InterestRate*100 < 4  THEN '2-4%'
        WHEN InterestRate*100 < 6  THEN '4-6%'
        WHEN InterestRate*100 < 8  THEN '6-8%'
        WHEN InterestRate*100 < 10 THEN '8-10%'
        WHEN InterestRate*100 < 12 THEN '10-12%'
        WHEN InterestRate*100 < 14 THEN '12-14%'
        ELSE '14%+'
    END                                     AS InterestRateBand,
    COUNT(*)                                AS LoanCount,
    ROUND(AVG(IsOverdue)*100, 2)            AS DefaultRate_Pct
FROM loans
GROUP BY InterestRateBand
ORDER BY MIN(InterestRate);


-- Q11: High-Risk Loans (overdue) — for Fraud Monitoring Table
SELECT
    l.LoanID,
    c.FirstName, c.LastName,
    at.TypeName                             AS AccountType,
    ROUND(l.PrincipalAmount_INR/1e5, 2)    AS Principal_Lakh,
    ROUND(l.InterestRate*100, 2)            AS InterestRate_Pct,
    l.StartDate,
    l.EstimatedEndDate,
    DATEDIFF(CURDATE(), l.EstimatedEndDate) AS DaysOverdue,
    ROUND(l.LoanToBalanceRatio, 4)          AS LoanToBalanceRatio
FROM loans l
JOIN accounts a ON l.AccountID     = a.AccountID
JOIN customers c ON a.CustomerID   = c.CustomerID
JOIN account_types at ON a.AccountTypeID = at.AccountTypeID
WHERE l.IsOverdue = 1
ORDER BY DaysOverdue DESC;


-- ─────────────────────────────────────────────────────────────
-- ACCOUNT INTELLIGENCE QUERIES
-- ─────────────────────────────────────────────────────────────

-- Q12: Account Type vs Status Matrix (Power BI stacked bar)
SELECT
    at.TypeName                             AS AccountType,
    ast.StatusName                          AS AccountStatus,
    COUNT(a.AccountID)                      AS AccountCount,
    ROUND(SUM(a.Balance_INR), 2)            AS TotalBalance_INR,
    ROUND(AVG(a.Balance_INR), 2)            AS AvgBalance_INR
FROM accounts a
JOIN account_types    at  ON a.AccountTypeID    = at.AccountTypeID
JOIN account_statuses ast ON a.AccountStatusID  = ast.AccountStatusID
GROUP BY at.TypeName, ast.StatusName
ORDER BY at.TypeName, ast.StatusName;


-- Q13: Balance Distribution Buckets
SELECT
    CASE
        WHEN Balance_INR < 400000    THEN 'Under ₹4L'
        WHEN Balance_INR < 1700000   THEN '₹4L - ₹17L'
        WHEN Balance_INR < 4200000   THEN '₹17L - ₹42L'
        WHEN Balance_INR < 8400000   THEN '₹42L - ₹84L'
        ELSE 'Above ₹84L'
    END                                     AS BalanceBucket,
    COUNT(*)                                AS AccountCount,
    ROUND(AVG(Balance_INR), 2)              AS AvgBalance_INR
FROM accounts
GROUP BY BalanceBucket
ORDER BY MIN(Balance_INR);


-- ─────────────────────────────────────────────────────────────
-- BRANCH PERFORMANCE QUERY
-- ─────────────────────────────────────────────────────────────

-- Q14: Full Branch Performance Scorecard
SELECT
    b.BranchID,
    b.BranchName,
    adr.City,
    adr.Country,
    COUNT(t.TransactionID)                  AS TotalTransactions,
    ROUND(SUM(t.Amount_INR)/1e7, 4)         AS Volume_Crore,
    ROUND(AVG(t.Amount_INR), 2)             AS AvgTxnAmount_INR,
    COUNT(DISTINCT t.AccountOriginID)       AS UniqueAccounts,
    ROUND(SUM(CASE WHEN t.TxnHour BETWEEN 0 AND 5 THEN 1 ELSE 0 END)*100.0
        / COUNT(*), 2)                      AS LateNightTxnPct,
    RANK() OVER (ORDER BY SUM(t.Amount_INR) DESC) AS VolumeRank
FROM transactions t
JOIN branches  b   ON t.BranchID  = b.BranchID
JOIN addresses adr ON b.AddressID = adr.AddressID
GROUP BY b.BranchID, b.BranchName, adr.City, adr.Country
ORDER BY Volume_Crore DESC;


-- ─────────────────────────────────────────────────────────────
-- DATA QUALITY AUDIT
-- ─────────────────────────────────────────────────────────────

-- Q15: Data Quality Summary
SELECT 'customers'    AS TableName,
    COUNT(*)          AS TotalRows,
    SUM(CASE WHEN FirstName IS NULL OR LastName IS NULL OR DateOfBirth IS NULL THEN 1 ELSE 0 END) AS NullCount,
    COUNT(*) - COUNT(DISTINCT CustomerID) AS DuplicateIDs
FROM customers
UNION ALL
SELECT 'accounts',
    COUNT(*), SUM(CASE WHEN Balance IS NULL OR OpeningDate IS NULL THEN 1 ELSE 0 END),
    COUNT(*) - COUNT(DISTINCT AccountID)
FROM accounts
UNION ALL
SELECT 'loans',
    COUNT(*), SUM(CASE WHEN PrincipalAmount IS NULL OR InterestRate IS NULL THEN 1 ELSE 0 END),
    COUNT(*) - COUNT(DISTINCT LoanID)
FROM loans
UNION ALL
SELECT 'transactions',
    COUNT(*), SUM(CASE WHEN Amount IS NULL OR TransactionDate IS NULL THEN 1 ELSE 0 END),
    COUNT(*) - COUNT(DISTINCT TransactionID)
FROM transactions;
