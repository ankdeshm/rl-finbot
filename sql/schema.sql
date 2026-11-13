-- =============================================================================
-- RL FinBot - star schema (SQL Server 2022)
-- Storage rule: amounts are SIGNED (revenue +, cost -) and stored at LEAF accounts only.
-- Subtotals (Revenue, Production, Gross profit, Operating profit, EBIT, Net income) are never
-- stored; the semantic layer always computes them from leaves.
-- Executed by scripts/load_mssql.py (split on GO). The part after the POST_LOAD marker runs
-- after the bulk load (index build is faster on loaded tables).
-- =============================================================================

-- Drop dependent objects first (security policy is schema-bound to the facts)
IF EXISTS (SELECT 1 FROM sys.security_policies WHERE name = N'OrgAccessPolicy')
    DROP SECURITY POLICY rls.OrgAccessPolicy;
GO
IF OBJECT_ID(N'rls.fn_org_access', N'IF') IS NOT NULL
    DROP FUNCTION rls.fn_org_access;
GO
DECLARE @sql NVARCHAR(MAX) = N'';
SELECT @sql += N'DROP VIEW ' + QUOTENAME(SCHEMA_NAME(schema_id)) + N'.' + QUOTENAME(name) + N';'
FROM sys.views WHERE SCHEMA_NAME(schema_id) = N'dbo' AND name LIKE N'v[_]%';
EXEC sp_executesql @sql;
GO
DROP TABLE IF EXISTS dbo.fact_employee_month;
DROP TABLE IF EXISTS dbo.dim_employee;
DROP TABLE IF EXISTS dbo.fact_pnl;
DROP TABLE IF EXISTS dbo.fact_stats;
DROP TABLE IF EXISTS dbo.user_org_access;
DROP TABLE IF EXISTS dbo.app_user;
DROP TABLE IF EXISTS dbo.dim_period;
DROP TABLE IF EXISTS dbo.dim_version;
DROP TABLE IF EXISTS dbo.dim_account;
DROP TABLE IF EXISTS dbo.dim_org;
GO

-- Organisation hierarchy L1 (group) .. L6 (business unit). SCD2-ready via valid_from/valid_to.
CREATE TABLE dbo.dim_org (
    bu_id            INT            NOT NULL,
    bu_name          NVARCHAR(50)   NOT NULL,   -- e.g. US-EPV-DEN-01
    l6_bu            NVARCHAR(50)   NOT NULL,
    l5_business      NVARCHAR(100)  NOT NULL,   -- e.g. Elevators & PV Denver
    l4_product_line  NVARCHAR(100)  NOT NULL,
    l3_country       NVARCHAR(50)   NOT NULL,
    l2_region        NVARCHAR(50)   NOT NULL,
    l1_group         NVARCHAR(50)   NOT NULL,
    business_type    NVARCHAR(30)   NOT NULL,   -- inspection / laboratory / infrastructure / certification
    city             NVARCHAR(50)   NOT NULL,
    valid_from       DATE           NOT NULL,
    valid_to         DATE           NOT NULL,   -- 9999-12-31 = current
    CONSTRAINT pk_dim_org PRIMARY KEY (bu_id)
);

-- Management P&L chart of accounts. Leaf rows carry data; header and subtotal rows exist for
-- display order and hierarchy only.
CREATE TABLE dbo.dim_account (
    account_id           INT            NOT NULL,
    line_no              INT            NOT NULL,   -- internal line key 1..21 (14-16 unused)
    l1_name              NVARCHAR(100)  NOT NULL,   -- P&L line name
    l2_code              NVARCHAR(10)   NOT NULL,   -- e.g. 7A (or the line number)
    l2_name              NVARCHAR(100)  NOT NULL,
    l3_code              NVARCHAR(10)   NOT NULL,   -- leaf code e.g. 7A2, 9.3
    l3_name              NVARCHAR(100)  NOT NULL,
    is_leaf              BIT            NOT NULL,
    is_subtotal          BIT            NOT NULL,
    natural_sign         SMALLINT       NOT NULL,   -- +1 revenue/profit, -1 cost
    display_order        INT            NOT NULL,
    favorable_direction  NVARCHAR(4)    NOT NULL,   -- 'up' revenue/profit, 'down' cost
    CONSTRAINT pk_dim_account PRIMARY KEY (account_id)
);

CREATE TABLE dbo.dim_version (
    version_id     INT           NOT NULL,
    name           NVARCHAR(20)  NOT NULL,          -- Actual, Budget, FC1, FC2, FC3
    actual_months  INT           NOT NULL,          -- months of actuals inside a forecast
    is_forecast    BIT           NOT NULL,
    CONSTRAINT pk_dim_version PRIMARY KEY (version_id)
);

CREATE TABLE dbo.dim_period (
    month_key   INT           NOT NULL,             -- YYYYMM
    year        INT           NOT NULL,
    quarter     INT           NOT NULL,
    month       INT           NOT NULL,
    month_name  NVARCHAR(10)  NOT NULL,
    close_date  DATE          NOT NULL,             -- 5th of the following month
    is_closed   BIT           NOT NULL,             -- relative to AS_OF_DATE at generation
    CONSTRAINT pk_dim_period PRIMARY KEY (month_key)
);

CREATE TABLE dbo.fact_pnl (
    month_key   INT            NOT NULL,
    bu_id       INT            NOT NULL,
    account_id  INT            NOT NULL,
    version_id  INT            NOT NULL,
    amount_usd  DECIMAL(18,2)  NOT NULL,            -- signed USD (constant budget rate): revenue +, cost -
    CONSTRAINT pk_fact_pnl PRIMARY KEY (version_id, month_key, bu_id, account_id)
);

CREATE TABLE dbo.fact_stats (
    month_key       INT            NOT NULL,
    bu_id           INT            NOT NULL,
    version_id      INT            NOT NULL,
    fte             DECIMAL(10,2)  NOT NULL,        -- total FTE (stock: average over months)
    headcount       DECIMAL(10,2)  NOT NULL,        -- total headcount (stock)
    direct_fte      DECIMAL(10,2)  NOT NULL,        -- direct / production FTE (stock)
    billable_hours  DECIMAL(12,1)  NOT NULL,        -- hours billed to clients (flow)
    available_hours DECIMAL(12,1)  NOT NULL,        -- available hours of direct staff (flow)
    overtime_hours  DECIMAL(12,1)  NOT NULL,        -- overtime hours of direct staff (flow)
    CONSTRAINT pk_fact_stats PRIMARY KEY (version_id, month_key, bu_id)
);

-- Fictional employees (codes only: no names or personal attributes). Monthly hours, FTE and
-- headcount add up exactly to fact_stats (Actual) per BU and month.
CREATE TABLE dbo.dim_employee (
    employee_id    INT            NOT NULL,
    employee_code  NVARCHAR(12)   NOT NULL,         -- e.g. E100123
    bu_id          INT            NOT NULL,
    role           NVARCHAR(40)   NOT NULL,         -- e.g. Inspector, Lab technician, Manager
    grade          NVARCHAR(4)    NOT NULL,         -- G1 (junior) .. G5 (senior)
    staff_type     NVARCHAR(10)   NOT NULL,         -- Direct (billable) / Indirect
    fte_pct        DECIMAL(4,2)   NOT NULL,         -- 1.00, 0.80, 0.50
    hire_date      DATE           NOT NULL,
    leave_date     DATE           NULL,
    leave_reason   NVARCHAR(20)   NULL,             -- Voluntary / Restructuring
    CONSTRAINT pk_dim_employee PRIMARY KEY (employee_id)
);

-- One row per employee and month on payroll (Actual months only).
CREATE TABLE dbo.fact_employee_month (
    month_key        INT            NOT NULL,
    employee_id      INT            NOT NULL,
    bu_id            INT            NOT NULL,       -- BU at that month (used by row-level security)
    fte              DECIMAL(4,2)   NOT NULL,
    available_hours  DECIMAL(8,1)   NOT NULL,       -- direct staff only (0 for indirect)
    billable_hours   DECIMAL(8,1)   NOT NULL,
    overtime_hours   DECIMAL(8,1)   NOT NULL,
    is_hire          BIT            NOT NULL,       -- first month on payroll
    is_leaver        BIT            NOT NULL,       -- last month on payroll
    CONSTRAINT pk_fact_employee_month PRIMARY KEY (employee_id, month_key)
);

CREATE TABLE dbo.app_user (
    user_id       NVARCHAR(50)   NOT NULL,
    display_name  NVARCHAR(100)  NOT NULL,
    role          NVARCHAR(50)   NOT NULL,
    CONSTRAINT pk_app_user PRIMARY KEY (user_id)
);

-- org_level is one of l1_group .. l6_bu; a user sees a BU if ANY of their rows matches it.
CREATE TABLE dbo.user_org_access (
    user_id    NVARCHAR(50)   NOT NULL,
    org_level  NVARCHAR(30)   NOT NULL,
    org_value  NVARCHAR(100)  NOT NULL,
    CONSTRAINT pk_user_org_access PRIMARY KEY (user_id, org_level, org_value)
);
GO

-- @@POST_LOAD@@
ALTER TABLE dbo.fact_pnl   ADD CONSTRAINT fk_fact_pnl_org     FOREIGN KEY (bu_id)      REFERENCES dbo.dim_org (bu_id);
ALTER TABLE dbo.fact_pnl   ADD CONSTRAINT fk_fact_pnl_account FOREIGN KEY (account_id) REFERENCES dbo.dim_account (account_id);
ALTER TABLE dbo.fact_pnl   ADD CONSTRAINT fk_fact_pnl_version FOREIGN KEY (version_id) REFERENCES dbo.dim_version (version_id);
ALTER TABLE dbo.fact_pnl   ADD CONSTRAINT fk_fact_pnl_period  FOREIGN KEY (month_key)  REFERENCES dbo.dim_period (month_key);
ALTER TABLE dbo.fact_stats ADD CONSTRAINT fk_fact_stats_org     FOREIGN KEY (bu_id)      REFERENCES dbo.dim_org (bu_id);
ALTER TABLE dbo.fact_stats ADD CONSTRAINT fk_fact_stats_version FOREIGN KEY (version_id) REFERENCES dbo.dim_version (version_id);
ALTER TABLE dbo.fact_stats ADD CONSTRAINT fk_fact_stats_period  FOREIGN KEY (month_key)  REFERENCES dbo.dim_period (month_key);
ALTER TABLE dbo.dim_employee ADD CONSTRAINT fk_dim_employee_org FOREIGN KEY (bu_id) REFERENCES dbo.dim_org (bu_id);
ALTER TABLE dbo.fact_employee_month ADD CONSTRAINT fk_fem_employee FOREIGN KEY (employee_id) REFERENCES dbo.dim_employee (employee_id);
ALTER TABLE dbo.fact_employee_month ADD CONSTRAINT fk_fem_org      FOREIGN KEY (bu_id)       REFERENCES dbo.dim_org (bu_id);
ALTER TABLE dbo.fact_employee_month ADD CONSTRAINT fk_fem_period   FOREIGN KEY (month_key)   REFERENCES dbo.dim_period (month_key);
GO
-- Columnstore index for fast aggregations over ~1M fact rows
CREATE NONCLUSTERED COLUMNSTORE INDEX ncci_fact_pnl
    ON dbo.fact_pnl (version_id, month_key, bu_id, account_id, amount_usd);
GO
CREATE NONCLUSTERED COLUMNSTORE INDEX ncci_fact_employee_month
    ON dbo.fact_employee_month (month_key, bu_id, employee_id, fte, available_hours, billable_hours,
                                overtime_hours, is_hire, is_leaver);
GO
