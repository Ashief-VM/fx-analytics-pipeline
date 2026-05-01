-- fct_exchange_rates.sql  |  Layer: Mart  |  Materialised: table
-- FACT TABLE. Grain: one row per rate_date + base + target currency.
-- Power BI connects to this for all trend and rate analysis.
WITH enriched AS (
    SELECT * FROM {{ ref('int_fx_enriched') }}
),
final AS (
    SELECT
        rate_key,
        rate_date, rate_month, rate_year, year_num, month_num,
        base_currency, target_currency,
        base_currency || '/' || target_currency AS currency_pair,
        exchange_rate, prev_day_rate,
        rolling_7d_avg, rolling_30d_avg,
        rolling_30d_max, rolling_30d_min,
        -- Daily change
        ROUND(exchange_rate - prev_day_rate, 6) AS daily_change,
        CASE
            WHEN prev_day_rate IS NOT NULL AND prev_day_rate > 0
            THEN ROUND(((exchange_rate - prev_day_rate) / prev_day_rate) * 100, 4)
            ELSE NULL
        END AS daily_change_pct,
        -- Volatility range
        ROUND(rolling_30d_max - rolling_30d_min, 6) AS volatility_30d_range,
        -- Position vs 30-day average
        CASE
            WHEN exchange_rate > rolling_30d_avg THEN 'above_average'
            WHEN exchange_rate < rolling_30d_avg THEN 'below_average'
            ELSE 'at_average'
        END AS vs_30d_avg_label,
        -- Trend direction
        CASE
            WHEN prev_day_rate IS NULL       THEN 'no_data'
            WHEN exchange_rate > prev_day_rate THEN 'strengthening'
            WHEN exchange_rate < prev_day_rate THEN 'weakening'
            ELSE 'unchanged'
        END AS daily_trend,
        loaded_at
    FROM enriched
)
SELECT * FROM final
