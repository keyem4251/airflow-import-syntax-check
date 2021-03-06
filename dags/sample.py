"""
Example Airflow DAG for Google BigQuery Sensors.
"""
import os
from datetime import datetime

from airflow import models
from airflow.providers.google.cloud.operators.bigquery import (
    BigQueryCreateEmptyDatasetOperator,
    BigQueryCreateEmptyTableOperator,
    BigQueryDeleteDatasetOperator,
    BigQueryInsertJobOperator,
)
from airflow.providers.google.cloud.sensors.bigquery import (
    BigQueryTableExistenceSensor,
)

PROJECT_ID = os.environ.get("GCP_PROJECT_ID", "example-project")
DATASET_NAME = os.environ.get("GCP_BIGQUERY_DATASET_NAME", "test_sensors_dataset")

TABLE_NAME = "partitioned_table"
INSERT_DATE = datetime.now().strftime("%Y-%m-%d")

PARTITION_NAME = "{{ ds_nodash }}"

INSERT_ROWS_QUERY = f"INSERT {DATASET_NAME}.{TABLE_NAME} VALUES " "(42, '{{ ds }}')"

SCHEMA = [
    {"name": "value", "type": "INTEGER", "mode": "REQUIRED"},
    {"name": "ds", "type": "DATE", "mode": "NULLABLE"},
]

dag_id = "example_bigquery_sensors"

with models.DAG(
    dag_id,
    schedule_interval='@once',  # Override to match your needs
    start_date=datetime(2021, 1, 1),
    catchup=False,
    tags=["example"],
    user_defined_macros={"DATASET": DATASET_NAME, "TABLE": TABLE_NAME},
    default_args={"project_id": PROJECT_ID},
) as dag_with_locations:
    create_dataset = BigQueryCreateEmptyDatasetOperator(
        task_id="create-dataset", dataset_id=DATASET_NAME, project_id=PROJECT_ID
    )

    create_table = BigQueryCreateEmptyTableOperator(
        task_id="create_table",
        dataset_id=DATASET_NAME,
        table_id=TABLE_NAME,
        schema_fields=SCHEMA,
        time_partitioning={
            "type": "DAY",
            "field": "ds",
        },
    )
    # [START howto_sensor_bigquery_table]
    check_table_exists = BigQueryTableExistenceSensor(
        task_id="check_table_exists", project_id=PROJECT_ID, dataset_id=DATASET_NAME, table_id=TABLE_NAME
    )
    # [END howto_sensor_bigquery_table]

    execute_insert_query = BigQueryInsertJobOperator(
        task_id="execute_insert_query",
        configuration={
            "query": {
                "query": INSERT_ROWS_QUERY,
                "useLegacySql": False,
            }
        },
    )

    delete_dataset = BigQueryDeleteDatasetOperator(
        task_id="delete_dataset", dataset_id=DATASET_NAME, delete_contents=True
    )

    create_dataset >> create_table
    create_table >> check_table_exists
    create_table >> execute_insert_query
    check_table_exists >> delete_dataset