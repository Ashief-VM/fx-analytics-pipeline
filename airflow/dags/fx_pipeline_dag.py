#fx_pipeline_dag.py
#Schedule: Weekdays 08:00 UTC  (cron: '0 8 * * 1-5')
#Tasks: extract_load_fx -> dbt_seed -> dbt_run -> dbt_test -> notify

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash   import BashOperator
from airflow.utils.dates      import days_ago
from datetime import timedelta
import subprocess, sys, logging
 
log = logging.getLogger(__name__)
 
default_args = {
    'owner'            : 'ashief',
    'depends_on_past'  : False,
    'retries'          : 2,
    'retry_delay'      : timedelta(minutes=5),
    'email_on_failure' : False,
}
 
with DAG(
    dag_id            = 'fx_daily_pipeline',
    description       = 'Daily FX ELT: Frankfurter API -> DuckDB -> dbt',
    default_args      = default_args,
    schedule_interval = '0 8 * * 1-5',
    start_date        = days_ago(1),
    catchup           = False,
    max_active_runs   = 1,
    tags              = ['fx', 'elt', 'dbt', 'daily'],
) as dag:
 
    # Task 1: Extract and Load
    def run_extract(**context):
        exec_date = context['ds']  # YYYY-MM-DD execution date
        log.info(f'Extracting FX rates for {exec_date}')
        result = subprocess.run(
            [sys.executable, '/opt/airflow/ingestion/extract_daily.py', exec_date],
            capture_output=True, text=True
        )
        log.info(result.stdout)
        if result.returncode != 0:
            raise Exception(f'Extract failed:\n{result.stderr}')
 
    extract_load = PythonOperator(
        task_id='extract_load_fx',
        python_callable=run_extract,
        provide_context=True,
    )
 
    # Task 2: dbt seed
    dbt_seed = BashOperator(
        task_id='dbt_seed',
        bash_command='cd /opt/airflow/dbt_fx && dbt seed --profiles-dir . --target prod',
    )
 
    # Task 3: dbt run
    dbt_run = BashOperator(
        task_id='dbt_run',
        bash_command='cd /opt/airflow/dbt_fx && dbt run --profiles-dir . --target prod',
    )
 
    # Task 4: dbt test
    dbt_test = BashOperator(
        task_id='dbt_test',
        bash_command='cd /opt/airflow/dbt_fx && dbt test --profiles-dir . --target prod',
    )
 
    # Task 5: Notify
    notify = BashOperator(
        task_id='notify_success',
        bash_command='echo "Pipeline complete for {{ ds }}"',
    )
 
    # Chain: each task runs only after the previous one succeed
    extract_load >> dbt_seed >> dbt_run >> dbt_test >> notify
