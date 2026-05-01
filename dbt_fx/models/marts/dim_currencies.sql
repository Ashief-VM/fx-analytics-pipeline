-- dim_currencies.sql  |  Layer: Mart  |  Materialised: table
-- DIMENSION TABLE. One row per currency code with descriptive attributes.
WITH currency_codes AS (
    SELECT DISTINCT target_currency AS currency_code FROM {{ ref('stg_fx_rates') }}
    UNION
    SELECT DISTINCT base_currency AS currency_code FROM {{ ref('stg_fx_rates') }}
),
meta AS (
    SELECT * FROM {{ ref('currency_meta') }}
),
final AS (
    SELECT
        c.currency_code,
        COALESCE(m.currency_name,    c.currency_code) AS currency_name,
        COALESCE(m.region,           'Unknown')        AS region,
        COALESCE(m.currency_symbol,  c.currency_code)  AS currency_symbol,
        COALESCE(CAST(m.is_major AS BOOLEAN), false)   AS is_major_currency
    FROM currency_codes c
    LEFT JOIN meta m ON c.currency_code = m.currency_code
)
SELECT * FROM final
