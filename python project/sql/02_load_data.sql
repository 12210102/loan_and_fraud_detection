-- =============================================================
-- BANKGUARD ANALYTICS — LOAD CLEANED DATA INTO MySQL
-- Run AFTER 01_create_schema.sql and Python cleaning step
-- =============================================================
-- Usage:
--   mysql -u root -p bankguard < sql/02_load_data.sql
-- OR use the Python loader script below this file
-- =============================================================

USE bankguard;

-- ── Set safe mode OFF for bulk loading ─────────────────────
SET FOREIGN_KEY_CHECKS = 0;
SET unique_checks      = 0;
SET autocommit         = 0;

-- ── Reference Tables ───────────────────────────────────────

LOAD DATA LOCAL INFILE '../uploaded to kaggle/customer_types.csv'
INTO TABLE customer_types
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(CustomerTypeID, TypeName);

LOAD DATA LOCAL INFILE '../uploaded to kaggle/account_types.csv'
INTO TABLE account_types
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(AccountTypeID, TypeName);

LOAD DATA LOCAL INFILE '../uploaded to kaggle/account_statuses.csv'
INTO TABLE account_statuses
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(AccountStatusID, StatusName);

LOAD DATA LOCAL INFILE '../uploaded to kaggle/loan_statuses.csv'
INTO TABLE loan_statuses
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(LoanStatusID, StatusName);

LOAD DATA LOCAL INFILE '../uploaded to kaggle/transaction_types.csv'
INTO TABLE transaction_types
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(TransactionTypeID, TypeName);

LOAD DATA LOCAL INFILE '../uploaded to kaggle/addresses.csv'
INTO TABLE addresses
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(AddressID, Street, City, Country);

LOAD DATA LOCAL INFILE '../uploaded to kaggle/branches.csv'
INTO TABLE branches
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(BranchID, BranchName, AddressID);

-- ── Core Tables (from cleaned CSVs) ────────────────────────

LOAD DATA LOCAL INFILE '../cleaned/customers_clean.csv'
INTO TABLE customers
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(CustomerID, FirstName, LastName, DateOfBirth, AddressID, CustomerTypeID);

LOAD DATA LOCAL INFILE '../cleaned/accounts_clean.csv'
INTO TABLE accounts
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(AccountID, CustomerID, AccountTypeID, AccountStatusID,
 Balance, OpeningDate, Balance_INR, TxnFrequency_90d, AvgTxnAmount_INR);

LOAD DATA LOCAL INFILE '../cleaned/loans_clean.csv'
INTO TABLE loans
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(LoanID, AccountID, LoanStatusID, PrincipalAmount, InterestRate,
 StartDate, EstimatedEndDate, PrincipalAmount_INR, LoanToBalanceRatio, IsOverdue);

LOAD DATA LOCAL INFILE '../cleaned/transactions_clean.csv'
INTO TABLE transactions
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(TransactionID, AccountOriginID, AccountDestinationID, TransactionTypeID,
 Amount, TransactionDate, BranchID, Description, Amount_INR);

-- ── Restore settings ───────────────────────────────────────
COMMIT;
SET FOREIGN_KEY_CHECKS = 1;
SET unique_checks      = 1;
SET autocommit         = 1;

-- ── Verification counts ────────────────────────────────────
SELECT 'Load complete — Row Counts:' AS Info;
SELECT 'customers'    AS TableName, COUNT(*) AS RowCount FROM customers
UNION ALL
SELECT 'accounts',     COUNT(*) FROM accounts
UNION ALL
SELECT 'loans',        COUNT(*) FROM loans
UNION ALL
SELECT 'transactions', COUNT(*) FROM transactions
UNION ALL
SELECT 'branches',     COUNT(*) FROM branches
UNION ALL
SELECT 'addresses',    COUNT(*) FROM addresses;
