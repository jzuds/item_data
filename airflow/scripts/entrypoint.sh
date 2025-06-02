#!/bin/bash
set -x

# Wait for DB to be ready
echo "Waiting for airflow-postgres..."
while ! nc -z airflow-postgres 5432; do
  sleep 1
done
echo "Postgres is up!"

CHECK_FILE="/opt/airflow/airflow_db_initialized.flag"

if [ ! -f "$CHECK_FILE" ]; then
  echo "Airflow DB not initialized. Initializing now..."
  
  airflow db migrate
  airflow connections create-default-connections
  
  if [ $? -eq 0 ]; then
    touch "$CHECK_FILE"
    echo "Initialization complete. Created check file."
  else
    echo "Airflow DB initialization failed."
    exit 1
  fi
else
  echo "Airflow DB already initialized (check file exists)."
fi

# Create admin user if it doesn't exist
airflow users list | grep -q admin
if [ $? -ne 0 ]; then
  echo "Creating admin user..."
  airflow users create \
    --username admin \
    --password admin \
    --firstname Admin \
    --lastname User \
    --role Admin \
    --email admin@example.com
else
  echo "Admin user already exists"
fi

echo "Starting Airflow webserver..."
exec airflow webserver

