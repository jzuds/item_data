#!/bin/bash

# Wait for DB to be ready
echo "Waiting for airflow-postgres..."
while ! nc -z airflow-postgres 5432; do
  sleep 1
done
echo "Postgres is up!"

# Initialize DB
airflow db init

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

# Start the webserver
exec airflow webserver
