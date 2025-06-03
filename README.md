# 🧙‍♂️ OSRS Item Data

A project for collecting item data from the **Old School RuneScape Grand Exchange** using containerized data pipelines and scheduled workflows.

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

🗓️ Fetch a range of 5-minute intervals:
```bash
docker-compose exec airflow-scheduler airflow dags backfill ingestion_raw_ge_history \
  -s 2025-06-01T00:00:00 \
  -e 2025-06-02T16:00:00
```

⏱️ Fetch a single 5-minute interval:
```bash
 docker-compose exec airflow-scheduler airflow dags backfill ingestion_raw_ge_history \
  -s 2025-04-01T00:00:00
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

Then, add the group to your container configuration:
```yaml
group_add:
- 1001
```