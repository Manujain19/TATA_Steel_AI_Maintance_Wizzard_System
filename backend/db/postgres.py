from __future__ import annotations

import json
from typing import Iterable

from backend.config import settings
from backend.services.data_repository import DataRepository


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS assets (id TEXT PRIMARY KEY, payload JSONB NOT NULL);
CREATE TABLE IF NOT EXISTS sensor_data (id SERIAL PRIMARY KEY, equipment_id TEXT, payload JSONB NOT NULL);
CREATE TABLE IF NOT EXISTS sensor_history (id SERIAL PRIMARY KEY, equipment_id TEXT, payload JSONB NOT NULL);
CREATE TABLE IF NOT EXISTS failure_modes (id SERIAL PRIMARY KEY, equipment_id TEXT, payload JSONB NOT NULL);
CREATE TABLE IF NOT EXISTS failure_reports (record_id TEXT PRIMARY KEY, equipment_id TEXT, payload JSONB NOT NULL);
CREATE TABLE IF NOT EXISTS maintenance_logs (log_id TEXT PRIMARY KEY, equipment_id TEXT, payload JSONB NOT NULL);
CREATE TABLE IF NOT EXISTS spare_parts (part_id TEXT PRIMARY KEY, equipment_id TEXT, payload JSONB NOT NULL);
CREATE TABLE IF NOT EXISTS work_orders (work_order_id TEXT PRIMARY KEY, equipment_id TEXT, payload JSONB NOT NULL);
CREATE TABLE IF NOT EXISTS copilot_conversations (id SERIAL PRIMARY KEY, equipment_id TEXT, payload JSONB NOT NULL, created_at TIMESTAMPTZ DEFAULT now());
CREATE TABLE IF NOT EXISTS sector_health (sector TEXT PRIMARY KEY, payload JSONB NOT NULL);
CREATE TABLE IF NOT EXISTS asset_relationships (id SERIAL PRIMARY KEY, source_asset TEXT, target_asset TEXT, payload JSONB NOT NULL);
"""


def get_connection():
    try:
        import psycopg
    except Exception as exc:  # pragma: no cover
        raise RuntimeError("psycopg is required for PostgreSQL mode") from exc
    return psycopg.connect(settings.database_url)


def initialize_schema() -> bool:
    if not settings.enable_postgres:
        return False
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(SCHEMA_SQL)
    return True


def _upsert_rows(cursor, table: str, key_name: str, rows: Iterable[dict]) -> None:
    for row in rows:
        key = row.get(key_name) or row.get("id")
        equipment_id = row.get("equipment_id") or row.get("id")
        if table == "assets":
            cursor.execute(
                "INSERT INTO assets (id, payload) VALUES (%s, %s) ON CONFLICT (id) DO UPDATE SET payload = EXCLUDED.payload",
                (key, json.dumps(row)),
            )
        else:
            cursor.execute(
                f"INSERT INTO {table} ({key_name}, equipment_id, payload) VALUES (%s, %s, %s) "
                f"ON CONFLICT ({key_name}) DO UPDATE SET payload = EXCLUDED.payload",
                (key, equipment_id, json.dumps(row)),
            )


def seed_from_json(repo: DataRepository | None = None) -> bool:
    if not settings.enable_postgres:
        return False
    repo = repo or DataRepository()
    initialize_schema()
    with get_connection() as conn:
        with conn.cursor() as cursor:
            _upsert_rows(cursor, "assets", "id", repo.assets())
            _upsert_rows(cursor, "failure_reports", "record_id", repo.failure_reports())
            _upsert_rows(cursor, "maintenance_logs", "log_id", repo.maintenance_logs())
            _upsert_rows(cursor, "spare_parts", "part_id", repo.spare_parts())
            _upsert_rows(cursor, "work_orders", "work_order_id", repo.work_orders())
            for table, rows in [
                ("sensor_data", repo.sensors()),
                ("sensor_history", repo.sensor_history()),
                ("failure_modes", repo.failure_modes()),
            ]:
                for row in rows:
                    cursor.execute(
                        f"INSERT INTO {table} (equipment_id, payload) VALUES (%s, %s)",
                        (row.get("equipment_id"), json.dumps(row)),
                    )
    return True
