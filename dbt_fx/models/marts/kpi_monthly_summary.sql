{{ config(materialized='table') }}

WITH fct AS (
    SELECT * FROM {{ ref('fct_exchange_rates') }}
)
SELECT
    rate_month,
    year_num,
    month_num,
    currency_pair,
    base_currency,
    target_currency,
    ROUND(AVG(exchange_rate), 6)                      AS avg_rate,
    ROUND(MIN(exchange_rate), 6)                      AS min_rate,
    ROUND(MAX(exchange_rate), 6)                      AS max_rate,
    ROUND(MAX(exchange_rate) - MIN(exchange_rate), 6) AS monthly_range,
    COUNT(DISTINCT rate_date)                         AS trading_days,
    ROUND(AVG(daily_change_pct), 4)                   AS avg_daily_change_pct
FROM fct
GROUP BY
    rate_month, year_num, month_num,
    currency_pair, base_currency, target_currency
ORDER BY rate_month, currency_pair