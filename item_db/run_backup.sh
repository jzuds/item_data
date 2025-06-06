#!/bin/bash

# === Configuration ===
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")

SERVICE_NAME="osrs-database"
DB_NAME="item_data_db"
DB_USER="item_data_user"
TABLE_NAME="raw.raw_ge_history"
TMP_DUMP_PATH="/tmp/raw_ge_history.dump"
LOCAL_DUMP_PATH="./item_db/raw_ge_history_${TIMESTAMP}.dump"

# === Step 1: Run pg_dump inside the container ===
echo "[1/4] Dumping table '$TABLE_NAME' from service '$SERVICE_NAME'..."
docker-compose exec -T "$SERVICE_NAME" \
  pg_dump -U "$DB_USER" -d "$DB_NAME" -n raw -t "$TABLE_NAME" -F c -f "$TMP_DUMP_PATH"

# === Step 2: Copy dump to host ===
echo "[2/4] Copying dump file to host..."
CONTAINER_ID=$(docker-compose ps -q "$SERVICE_NAME")
docker cp "$CONTAINER_ID:$TMP_DUMP_PATH" "$LOCAL_DUMP_PATH"

# === Step 3: Compress with zstd or gzip ===
echo "[3/4] Compressing the dump file..."
if command -v zstd &> /dev/null; then
  zstd -19 --rm "$LOCAL_DUMP_PATH"
  echo "[✓] Compressed with zstd → $LOCAL_DUMP_PATH.zst"
elif command -v gzip &> /dev/null; then
  gzip -9 "$LOCAL_DUMP_PATH"
  echo "[✓] Compressed with gzip → $LOCAL_DUMP_PATH.gz"
else
  echo "[!] No compression tool found (zstd or gzip). File remains uncompressed."
fi

# === Step 4: Clean up container dump ===
echo "[4/4] Removing temp file from container..."
docker-compose exec -T "$SERVICE_NAME" rm -f "$TMP_DUMP_PATH"

echo "[✓] Backup completed successfully."
