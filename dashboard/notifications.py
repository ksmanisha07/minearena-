import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator


_SEVERITY_ORDER = {
    "Urgent": 0,
    "Review": 1,
    "Watch": 2,
    "Sensor issue": 3,
}


@contextmanager
def _connection() -> Iterator[sqlite3.Connection]:
    configured_path = os.environ.get("MINEARENA_NOTIFICATION_DB")
    database_path = Path(configured_path) if configured_path else Path(__file__).with_name(
        "notifications.sqlite3"
    )
    database_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database_path, timeout=10)
    connection.row_factory = sqlite3.Row
    try:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS doctor_notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_key TEXT NOT NULL UNIQUE,
                patient_id TEXT NOT NULL,
                patient_name TEXT NOT NULL,
                severity TEXT NOT NULL,
                message TEXT NOT NULL,
                recommended_action TEXT NOT NULL,
                rule_id TEXT NOT NULL,
                created_at TEXT NOT NULL,
                read_at TEXT
            )
            """
        )
        yield connection
        connection.commit()
    finally:
        connection.close()


def create_notification(
    patient_id: str,
    patient_name: str,
    severity: str,
    message: str,
    recommended_action: str,
    rule_id: str,
    reading_time: str,
) -> bool:
    if severity not in _SEVERITY_ORDER:
        raise ValueError(f"Unsupported notification severity: {severity}")

    event_key = "\x1f".join((patient_id, severity, rule_id, reading_time))
    with _connection() as connection:
        cursor = connection.execute(
            """
            INSERT OR IGNORE INTO doctor_notifications (
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
        return cursor.rowcount == 1


def seed_demo_notifications() -> int:
    examples = [
        (
            "urgent",
            "P-001",
            "Ramesh",
            "Urgent",
            "Synthetic example · partial NEWS2-style score 9",
            "Immediate clinical review",
            "NEWS2_PARTIAL_SCORE",
        ),
        (
            "review",
            "P-002",
            "Sunita",
            "Review",
            "Synthetic example · partial NEWS2-style score 6",
            "Nurse review within 15 minutes",
            "NEWS2_PARTIAL_SCORE",
        ),
        (
            "watch",
            "P-003",
            "Arjun",
            "Watch",
            "Synthetic example · heart rate trending above baseline",
            "Re-check in 30 minutes",
            "SPO2_TREND_BELOW_BASELINE",
        ),
        (
            "sensor",
            "P-001",
            "Ramesh",
            "Sensor issue",
            "Synthetic example · probable probe removal",
            "Ask patient to refit the sensor and verify the reading",
            "PROBE_REMOVAL_SIGNATURE",
        ),
    ]
    created = 0
    for event_id, patient_id, patient_name, severity, message, action, rule_id in examples:
        created += create_notification(
            patient_id=patient_id,
            patient_name=patient_name,
            severity=severity,
            message=message,
            recommended_action=action,
            rule_id=rule_id,
            reading_time=f"demo-seed-v1:{event_id}",
        )
    return created


def list_notifications(limit: int = 100) -> list[dict[str, object]]:
    if limit < 1:
        raise ValueError("Notification limit must be positive")

    with _connection() as connection:
        rows = connection.execute(
            """
            SELECT id, patient_id, patient_name, severity, message,
                   recommended_action, rule_id, created_at, read_at
            FROM doctor_notifications
            ORDER BY
                CASE severity
                    WHEN 'Urgent' THEN 0
                    WHEN 'Review' THEN 1
                    WHEN 'Watch' THEN 2
                    ELSE 3
                END,
                id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [dict(row) for row in rows]


def unread_count() -> int:
    with _connection() as connection:
        row = connection.execute(
            "SELECT COUNT(*) AS count FROM doctor_notifications WHERE read_at IS NULL"
        ).fetchone()
        return int(row["count"])


def mark_notification_read(notification_id: int) -> None:
    with _connection() as connection:
        connection.execute(
            """
            UPDATE doctor_notifications
            SET read_at = ?
            WHERE id = ? AND read_at IS NULL
            """,
            (datetime.now(timezone.utc).isoformat(timespec="seconds"), notification_id),
        )


def mark_all_notifications_read() -> None:
    with _connection() as connection:
        connection.execute(
            """
            UPDATE doctor_notifications
            SET read_at = ?
            WHERE read_at IS NULL
            """,
            (datetime.now(timezone.utc).isoformat(timespec="seconds"),),
        )
