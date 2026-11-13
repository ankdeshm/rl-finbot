# Reconciliation report (mssql backend)

## Row counts per table

| Table | Rows |
|---|---:|
| dim_org | 109 |
| dim_account | 57 |
| dim_version | 5 |
| dim_period | 60 |
| app_user | 3 |
| user_org_access | 3 |
| fact_pnl | 1,201,834 |
| fact_stats | 32,482 |

## fact_pnl rows and totals per version

| Version | Rows | Months | Sum of signed amounts (USD) |
|---|---:|---:|---:|
| Actual | 233,914 | 58 | 549,031,703.08 |
| Budget | 241,980 | 60 | 601,041,628.60 |
| FC1 | 241,980 | 60 | 574,995,886.99 |
| FC2 | 241,980 | 60 | 570,624,038.75 |
| FC3 | 241,980 | 60 | 568,682,516.76 |

## Integrity checks

| Check | Found | Expected | Status |
|---|---:|---:|---|
| Fact rows on non-leaf (subtotal/header) accounts | 0 | 0 | OK |
| Actual rows for months not yet closed | 0 | 0 | OK |
| Forecast actual-months differing from Actual (month totals) | 0 | 0 | OK |

SQL Server vs DuckDB (rows and totals per version): identical

## Subtotal reconciliation: 50 random BU x month x version samples

Each sample checks Revenue, Production, Gross profit, MAOP, Management OP and Net income three ways: semantic layer vs raw SQL leaf sums (tolerance USD 0.005) and vs generator control totals (tolerance USD 0.15).

| BU | Month | Version | Production (USD) | MAOP (USD) | Status |
|---|---|---|---:|---:|---|
| CA-MMI-TOR-03 | 202507 | Budget | 1,265,060.17 | 147,760.98 | OK |
| UY-CER-MVD-01 | 202604 | FC2 | 152,923.34 | 51,980.49 | OK |
| PE-IND-AQP-01 | 202412 | FC1 | 606,310.90 | 33,948.42 | OK |
| CA-ENV-VAN-02 | 202603 | Budget | 1,091,160.81 | 228,116.14 | OK |
| UY-BNI-MVD-01 | 202408 | Budget | 248,080.89 | 41,094.00 | OK |
| CA-CER-TOR-02 | 202607 | FC3 | 304,272.38 | 61,981.70 | OK |
| BR-BNI-CWB-01 | 202504 | FC2 | 602,652.69 | 141,125.32 | OK |
| CO-ENV-BAQ-01 | 202407 | FC3 | 660,466.90 | 49,191.41 | OK |
| US-CER-NYC-01 | 202204 | Budget | 428,181.55 | 126,298.11 | OK |
| BR-MMI-BHZ-01 | 202401 | FC3 | 810,633.42 | -13,466.61 | OK |
| CA-ENV-VAN-02 | 202408 | FC2 | 633,693.01 | -53,896.43 | OK |
| PY-BNI-ASU-02 | 202502 | FC3 | 180,289.18 | 12,168.90 | OK |
| ... 38 more samples | | | | | |

**Mismatches: 0** (subtotal checks: 300), integrity check failures: 0
