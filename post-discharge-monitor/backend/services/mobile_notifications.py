import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator


def _database_path() -> Path:
    configured_path = os.environ.get("MINEARENA_MOBILE_DB")
    if configured_path:
        return Path(configured_path)
    return Path(__file__).parents[1] / "data" / "mobile_alerts.sqlite3"


@contextmanager
def _connection() -> Iterator[sqlite3.Connection]:
    path = _database_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, timeout=10)
    connection.row_factory = sqlite3.Row
    try:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS mobile_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_key TEXT NOT NULL UNIQUE,
                patient_id TEXT NOT NULL,
                patient_name TEXT NOT NULL,
                severity TEXT NOT NULL,
                message TEXT NOT NULL,
                recommended_action TEXT NOT NULL,
                rule_id TEXT NOT NULL,
                created_at TEXT NOT NULL,
                acknowledged_at TEXT,
                push_sent_at TEXT
            );
            CREATE TABLE IF NOT EXISTS doctor_push_subscriptions (
                endpoint TEXT PRIMARY KEY,
                subscription_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            """
        )
        yield connection
        connection.commit()
    finally:
        connection.close()


def create_alert(
    *,
    patient_id: str,
    patient_name: str,
    severity: str,
    message: str,
    recommended_action: str,
    rule_id: str,
    reading_time: str,
) -> tuple[int, bool, bool]:
    event_key = "\x1f".join((patient_id, severity, rule_id, reading_time))
    with _connection() as connection:
        cursor = connection.execute(
            """
            INSERT OR IGNORE INTO mobile_alerts (
                event_key, patient_id, patient_name, severity, message,
                recommended_action, rule_id, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event_key,
                patient_id,
                patient_name,
                severity,
                message,
                recommended_action,
                rule_id,
                datetime.now(timezone.utc).isoformat(timespec="seconds"),
            ),
        )
        row = connection.execute(
            "SELECT id, push_sent_at FROM mobile_alerts WHERE event_key = ?", (event_key,)
        ).fetchone()
        return int(row["id"]), cursor.rowcount == 1, row["push_sent_at"] is not None


def list_alerts() -> list[dict[str, object]]:
    with _connection() as connection:
        rows = connection.execute(
            """
            SELECT id, patient_id, patient_name, severity, message,
                   recommended_action, rule_id, created_at, acknowledged_at
            FROM mobile_alerts
            ORDER BY
                CASE severity
                    WHEN 'Urgent' THEN 0
                    WHEN 'Review' THEN 1
                    WHEN 'Watch' THEN 2
                    ELSE 3
                END,
                id DESC
            """
        ).fetchall()
        return [dict(row) for row in rows]


def acknowledge_alert(alert_id: int) -> bool:
    with _connection() as connection:
        cursor = connection.execute(
            """
            UPDATE mobile_alerts
            SET acknowledged_at = ?
            WHERE id = ? AND acknowledged_at IS NULL
            """,
            (datetime.now(timezone.utc).isoformat(timespec="seconds"), alert_id),
        )
        return cursor.rowcount == 1


def mark_alert_push_sent(alert_id: int) -> None:
    with _connection() as connection:
        connection.execute(
            "UPDATE mobile_alerts SET push_sent_at = ? WHERE id = ?",
            (datetime.now(timezone.utc).isoformat(timespec="seconds"), alert_id),
        )


def pending_push_alert_ids() -> list[int]:
    with _connection() as connection:
        rows = connection.execute(
            """
            SELECT id FROM mobile_alerts
            WHERE push_sent_at IS NULL AND acknowledged_at IS NULL
            ORDER BY id
            """
        ).fetchall()
        return [int(row["id"]) for row in rows]


def save_subscription(subscription: dict[str, object]) -> None:
    serialized = json.dumps(subscription, separators=(",", ":"), sort_keys=True)
    with _connection() as connection:
        connection.execute(
            """
            INSERT INTO doctor_push_subscriptions (endpoint, subscription_json, created_at)
            VALUES (?, ?, ?)
            ON CONFLICT(endpoint) DO UPDATE SET subscription_json = excluded.subscription_json
            """,
            (
                str(subscription["endpoint"]),
                serialized,
                datetime.now(timezone.utc).isoformat(timespec="seconds"),
            ),
        )


def list_subscriptions() -> list[dict[str, object]]:
    with _connection() as connection:
        rows = connection.execute(
            "SELECT subscription_json FROM doctor_push_subscriptions"
        ).fetchall()
        return [json.loads(row["subscription_json"]) for row in rows]


def remove_subscription(endpoint: str) -> None:
    with _connection() as connection:
        connection.execute(
            "DELETE FROM doctor_push_subscriptions WHERE endpoint = ?", (endpoint,)
        )
