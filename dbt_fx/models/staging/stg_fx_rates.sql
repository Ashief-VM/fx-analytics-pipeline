WITH source AS (
    SELECT * FROM {{ source('raw', 'raw_fx_rates') }}
),
cleaned AS (
    SELECT
        CAST(rate_date AS DATE)                    AS rate_date,
        UPPER(TRIM(base_currency))                 AS base_currency,
        UPPER(TRIM(target_currency))               AS target_currency,
        CAST(exchange_rate AS DOUBLE)              AS exchange_rate,
        CAST(loaded_at AS TIMESTAMP)               AS loaded_at,
        CAST(rate_date AS VARCHAR)
            || '_' || UPPER(TRIM(base_currency))
            || '_' || UPPER(TRIM(target_currency)) AS rate_key
    FROM source
    WHERE exchange_rate > 0
      AND rate_date IS NOT NULL
)
SELECT * FROM cleaned