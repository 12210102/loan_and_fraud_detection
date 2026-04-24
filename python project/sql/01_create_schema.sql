-- =============================================================
-- BANKGUARD ANALYTICS — MySQL SCHEMA
-- Data Preparation & Schema Definition
-- Run this FIRST to create the database and all tables
-- =============================================================
-- Usage:
--   mysql -u root -p < sql/01_create_schema.sql
-- =============================================================

CREATE DATABASE IF NOT EXISTS bankguard
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE bankguard;

-- ── Reference / Lookup Tables ──────────────────────────────

CREATE TABLE IF NOT EXISTS customer_types (
    CustomerTypeID   INT           PRIMARY KEY,
    TypeName         VARCHAR(50)   NOT NULL
);

CREATE TABLE IF NOT EXISTS account_types (
    AccountTypeID    INT           PRIMARY KEY,
    TypeName         VARCHAR(50)   NOT NULL
);

CREATE TABLE IF NOT EXISTS account_statuses (
    AccountStatusID  INT           PRIMARY KEY,
    StatusName       VARCHAR(50)   NOT NULL
);

CREATE TABLE IF NOT EXISTS loan_statuses (
    LoanStatusID     INT           PRIMARY KEY,
    StatusName       VARCHAR(50)   NOT NULL
);

CREATE TABLE IF NOT EXISTS transaction_types (
    TransactionTypeID INT          PRIMARY KEY,
    TypeName          VARCHAR(50)  NOT NULL
);

-- ── Addresses ──────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS addresses (
    AddressID        INT           PRIMARY KEY,
    Street           VARCHAR(200),
    City             VARCHAR(100),
    Country          VARCHAR(100),
    INDEX idx_city   (City),
    INDEX idx_country(Country)
);

-- ── Branches ───────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS branches (
    BranchID         INT           PRIMARY KEY,
    BranchName       VARCHAR(100)  NOT NULL,
    AddressID        INT,
    FOREIGN KEY (AddressID) REFERENCES addresses(AddressID)
      ON DELETE SET NULL
);

-- ── Customers ──────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS customers (
    CustomerID       INT           PRIMARY KEY,
    FirstName        VARCHAR(100)  NOT NULL,
    LastName         VARCHAR(100)  NOT NULL,
    DateOfBirth      DATE,
    AddressID        INT,
    CustomerTypeID   INT           NOT NULL,
    -- Derived fields (from Python cleaning)
    Age              INT           GENERATED ALWAYS AS
                       (TIMESTAMPDIFF(YEAR, DateOfBirth, CURDATE())) STORED,
    FOREIGN KEY (AddressID)      REFERENCES addresses(AddressID)     ON DELETE SET NULL,
    FOREIGN KEY (CustomerTypeID) REFERENCES customer_types(CustomerTypeID),
    INDEX idx_custtype (CustomerTypeID),
    INDEX idx_address  (AddressID)
);

-- ── Accounts ───────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS accounts (
    AccountID           INT            PRIMARY KEY,
    CustomerID          INT            NOT NULL,
    AccountTypeID       INT            NOT NULL,
    AccountStatusID     INT            NOT NULL DEFAULT 1,
    Balance             DECIMAL(18,2)  NOT NULL DEFAULT 0.00   COMMENT 'USD',
    Balance_INR         DECIMAL(18,2)  NOT NULL DEFAULT 0.00   COMMENT 'INR (×84)',
    OpeningDate         DATE,
    -- Derived features (from Python cleaning)
    TxnFrequency_90d    INT            DEFAULT 0,
    AvgTxnAmount_INR    DECIMAL(18,2)  DEFAULT 0.00,
    FOREIGN KEY (CustomerID)      REFERENCES customers(CustomerID)        ON DELETE CASCADE,
    FOREIGN KEY (AccountTypeID)   REFERENCES account_types(AccountTypeID),
    FOREIGN KEY (AccountStatusID) REFERENCES account_statuses(AccountStatusID),
    INDEX idx_customer   (CustomerID),
    INDEX idx_acctype    (AccountTypeID),
    INDEX idx_accstatus  (AccountStatusID)
);

-- ── Loans ──────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS loans (
    LoanID                INT            PRIMARY KEY,
    AccountID             INT            NOT NULL,
    LoanStatusID          INT            NOT NULL DEFAULT 1,
    PrincipalAmount       DECIMAL(18,2)  NOT NULL    COMMENT 'USD',
    PrincipalAmount_INR   DECIMAL(18,2)  NOT NULL    COMMENT 'INR (×84)',
    InterestRate          DECIMAL(8,6)   NOT NULL,
    StartDate             DATE,
    EstimatedEndDate      DATE,
    -- Derived features
    LoanDurationDays      INT            GENERATED ALWAYS AS
                            (DATEDIFF(EstimatedEndDate, StartDate)) STORED,
    LoanToBalanceRatio    DECIMAL(10,4)  DEFAULT NULL,
    IsOverdue             TINYINT(1)     GENERATED ALWAYS AS
                            (LoanStatusID = 3) STORED,
    FOREIGN KEY (AccountID)    REFERENCES accounts(AccountID)    ON DELETE CASCADE,
    FOREIGN KEY (LoanStatusID) REFERENCES loan_statuses(LoanStatusID),
    INDEX idx_loan_account  (AccountID),
    INDEX idx_loan_status   (LoanStatusID),
    INDEX idx_is_overdue    (IsOverdue)
);

-- ── Transactions ───────────────────────────────────────────

CREATE TABLE IF NOT EXISTS transactions (
    TransactionID         INT            PRIMARY KEY,
    AccountOriginID       INT            NOT NULL,
    AccountDestinationID  INT,
    TransactionTypeID     INT            NOT NULL,
    Amount                DECIMAL(18,2)  NOT NULL    COMMENT 'USD',
    Amount_INR            DECIMAL(18,2)  NOT NULL    COMMENT 'INR (×84)',
    TransactionDate       DATETIME       NOT NULL,
    BranchID              INT,
    Description           VARCHAR(255),
    -- Extracted time parts for fast querying
    TxnHour               TINYINT        GENERATED ALWAYS AS (HOUR(TransactionDate))   STORED,
    TxnDayOfWeek          TINYINT        GENERATED ALWAYS AS (DAYOFWEEK(TransactionDate)) STORED,
    TxnYear               SMALLINT       GENERATED ALWAYS AS (YEAR(TransactionDate))   STORED,
    TxnMonth              TINYINT        GENERATED ALWAYS AS (MONTH(TransactionDate))  STORED,
    FOREIGN KEY (AccountOriginID)      REFERENCES accounts(AccountID),
    FOREIGN KEY (AccountDestinationID) REFERENCES accounts(AccountID),
    FOREIGN KEY (TransactionTypeID)    REFERENCES transaction_types(TransactionTypeID),
    FOREIGN KEY (BranchID)             REFERENCES branches(BranchID),
    INDEX idx_txn_origin    (AccountOriginID),
    INDEX idx_txn_dest      (AccountDestinationID),
    INDEX idx_txn_date      (TransactionDate),
    INDEX idx_txn_type      (TransactionTypeID),
    INDEX idx_txn_branch    (BranchID),
    INDEX idx_txn_year_mon  (TxnYear, TxnMonth)
);

-- ── ML Predictions log table ────────────────────────────────

CREATE TABLE IF NOT EXISTS ml_predictions (
    PredictionID         INT            PRIMARY KEY AUTO_INCREMENT,
    LoanID               INT,
    AccountID            INT,
    DefaultProbability   DECIMAL(8,6),
    RiskClass            ENUM('LOW','MODERATE','HIGH','CRITICAL'),
    ModelVersion         VARCHAR(50),
    PredictedAt          DATETIME       DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (LoanID)    REFERENCES loans(LoanID)    ON DELETE SET NULL,
    FOREIGN KEY (AccountID) REFERENCES accounts(AccountID) ON DELETE SET NULL,
    INDEX idx_pred_loan    (LoanID),
    INDEX idx_pred_risk    (RiskClass),
    INDEX idx_pred_date    (PredictedAt)
);

-- ── Fraud alerts log table ──────────────────────────────────

CREATE TABLE IF NOT EXISTS fraud_alerts (
    AlertID             INT            PRIMARY KEY AUTO_INCREMENT,
    TransactionID       INT,
    FraudScore          TINYINT        CHECK (FraudScore BETWEEN 0 AND 100),
    RiskLevel           ENUM('LOW','MODERATE','HIGH','CRITICAL'),
    FlaggedFactors      JSON,
    ReviewedBy          VARCHAR(100),
    ReviewedAt          DATETIME,
    Status              ENUM('PENDING','REVIEWED','CLEARED','BLOCKED') DEFAULT 'PENDING',
    CreatedAt           DATETIME       DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (TransactionID) REFERENCES transactions(TransactionID) ON DELETE SET NULL,
    INDEX idx_alert_txn    (TransactionID),
    INDEX idx_alert_risk   (RiskLevel),
    INDEX idx_alert_status (Status)
);

-- Confirm
SELECT 'Schema created successfully in bankguard database' AS Status;
SHOW TABLES;
