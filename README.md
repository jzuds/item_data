# 🧙‍♂️ OSRS Item Data

A project for collecting item data from the **Old School RuneScape Grand Exchange** using containerized data pipelines and scheduled workflows.

The goal of this project is to enable **insightful analysis** of item price trends and market behavior on the OSRS Grand Exchange.

## 🎯 Objectives

- **Track historical price changes** for specific high-value or high-volume items.
- **Detect market anomalies** or unusual price/volume fluctuations.

---

## 🧰 Requirements

- [🐳 Docker](https://www.docker.com/) — Used for containerizing the project

---

## 📟 Interfaces

- [📅 Airflow UI](http://localhost:8080/home)  
  *Login: `admin:admin`*
- [📈 Dashboard (Dash)](http://localhost:8050)

---

## 🛠️ Setup & Useful Commands

**Build and run the data collector:**
**Initialize the project (currently empty, add setup commands here):**
```bash
make init-project
```
***Start the full stack:***
```
make up
```
***Stop the full stack:***
```
make down
```

## 🔁 Backfilling Data
**Backfill frequency breakdown:**
- 1 request = 5 minute interval
- 1 day = 288 requests
> Regardless of rate limits, we ask you to add delays between your requests to help evenly distribute the server load. Keep in mind this is a free project with very real hosting costs.

Use the provided `Makefile` to backfill the last 12 hours:
```bash
make backfill
```

or to backfill an entire day (YYYYMMDD)
```bash
make backfill DATE=20250601
```

🗓️ Fetch a range of 5-minute intervals:
```bash
docker-compose exec airflow-scheduler airflow dags backfill ingestion_raw_ge_history \
  -s 2025-01-15T00:00:00 \
  -e 2025-01-20T00:00:00 \
  --reset-dagruns
```

⏱️ Fetch a single 5-minute interval:
```bash
docker-compose exec airflow-scheduler airflow dags backfill ingestion_raw_ge_history \
  -s 2025-06-01T00:00:00 \
  --reset-dagruns
```

## 🔁 OSRS Database Backup and Restore
This script backs up the `raw.raw_ge_history` table from your PostgreSQL database running inside a Docker Compose service. 
It dumps the table, copies it to the host, compresses the dump, and cleans up temporary files inside the container.

### Prerequisites

- Docker and Docker Compose installed
- Access to the Docker Compose project directory
- `zstd` or `gzip` installed on the host for compression
- The backup script (`run_backup.sh`) with executable permissions

### 🛡️ Backup
```bash
$ chmod +x item_db/run_backup.sh
$ ./item_db/run_backup.sh
[1/4] Dumping table 'raw.raw_ge_history' from service 'osrs-database'...
[2/4] Copying dump file to host...
Successfully copied 632MB to /mnt/d/projects/data-collection/item_data/item_db/raw_ge_history_2025-06-06_16-05-23.dump
[3/4] Compressing the dump file...
./item_db/raw_ge_history_2025-06-06_16-05-23.dump :100.00%   (632232495 => 632245189 bytes, ./item_db/raw_ge_history_2025-06-06_16-05-23.dump.zst)
[✓] Compressed with zstd → ./item_db/raw_ge_history_2025-06-06_16-05-23.dump.zst
[4/4] Removing temp file from container...
[✓] Backup completed successfully.
```
### ⬇️ Restore
```bash
unzstd raw_ge_history_YYYY-MM-DD_HH-MM-SS.dump.zst
```
or
```bash
gunzip raw_ge_history_YYYY-MM-DD_HH-MM-SS.dump.gz
```
```bash
docker-compose exec -T osrs-database \
  pg_restore -U item_data_user -d item_data_db -n raw -t raw.raw_ge_history /tmp/raw_ge_history.dump
```

## 🐞 Debugging
**Fixing Docker socket permission issue:**
If you see an error like:
```ini
docker_url='unix://var/run/docker.sock' permission denied
```
```bash
getent group docker
# Output example: docker:x:1001:zuds
```

Then, update the group in the `docker-compose.yml`, see service=airflow-scheduler :
```yaml
group_add:
- 1001
```

**Backfill not started with scheduler conflict**

When running a backfill and you see an error like:
```ini
[2025-06-08T13:07:32.748+0000] {backfill_job_runner.py:927} ERROR - Backfill cannot be created for DagRun scheduled__2025-06-08T13:00:00+00:00 in 2025-06-08T13:00:00, as there's already scheduled in a RUNNING state.
[2025-06-08T13:07:32.749+0000] {backfill_job_runner.py:934} ERROR - Changing DagRun into BACKFILL would cause scheduler to lose track of executing tasks. Not changing DagRun type into BACKFILL, and trying insert another DagRun into database would cause database constraint violation for dag_id + execution_date combination. Please adjust backfill dates or wait for this DagRun to finish.
```

Then, go to the airflow ui and **toggle the dag off**, or monitor the dag to not be in a `RUNNING` state