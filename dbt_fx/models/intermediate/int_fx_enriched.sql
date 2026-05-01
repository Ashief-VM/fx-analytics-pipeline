-- int_fx_enriched.sql  |  Layer: Intermediate  |  Materialised: ephemeral
-- Purpose: Add rolling averages and daily change using window functions.
-- Ephemeral = compiled as a subquery, no physical table created.
WITH rates AS (
    SELECT * FROM {{ ref('stg_fx_rates') }}
),
enriched AS (
    SELECT
        rate_key, rate_date, base_currency, target_currency,
        exchange_rate, loaded_at,
        -- Previous trading day rate
        LAG(exchange_rate, 1) OVER (
            PARTITION BY base_currency, target_currency ORDER BY rate_date
        ) AS prev_day_rate,
        -- 7-day rolling average
        AVG(exchange_rate) OVER (
            PARTITION BY base_currency, target_currency ORDER BY rate_date
            ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
        ) AS rolling_7d_avg,
        -- 30-day rolling average
        AVG(exchange_rate) OVER (
            PARTITION BY base_currency, target_currency ORDER BY rate_date
            ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
        ) AS rolling_30d_avg,
        -- 30-day max and min for volatility
        MAX(exchange_rate) OVER (
            PARTITION BY base_currency, target_currency ORDER BY rate_date
            ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
        ) AS rolling_30d_max,
        MIN(exchange_rate) OVER (
            PARTITION BY base_currency, target_currency ORDER BY rate_date
            ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
        ) AS rolling_30d_min,
        DATE_TRUNC('month', rate_date) AS rate_month,
        DATE_TRUNC('year',  rate_date) AS rate_year,
        EXTRACT('year'  FROM rate_date) AS year_num,
        EXTRACT('month' FROM rate_date) AS month_num
    FROM rates
)
SELECT * FROM enriched
