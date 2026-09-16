
import json
import logging
import sqlite3
import uuid
from datetime import datetime

from app.config import settings

logger = logging.getLogger(__name__)

DB_PATH = settings.db_path




CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS reports (
    id                  TEXT PRIMARY KEY,
    topic               TEXT NOT NULL,
    report_md           TEXT NOT NULL,
    sources_json        TEXT NOT NULL,
    sub_questions_json  TEXT NOT NULL,
    url_count           INTEGER DEFAULT 0,
    created_at          TEXT NOT NULL
)
"""



def init_db() -> None:
    """
    Create the reports table if it doesn't already exist.

    This is called once at server startup (inside the FastAPI lifespan function).
    'IF NOT EXISTS' means it is safe to call on every restart — it won't
    wipe existing data.
    """
    # sqlite3.connect() creates the file if it doesn't exist yet
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute(CREATE_TABLE_SQL)
        conn.commit()
        logger.info(f"Database ready: {DB_PATH}")
    finally:
        # Always close the connection, even if an error occurred
        conn.close()


def save_report(
    topic: str,
    report_md: str,
    sources: list,
    sub_questions: list,
) -> str:
    """
    Save a completed research report to the database.

    Returns the report's ID (an 8-character string like "a1b2c3d4").
    The frontend uses this ID to build the PDF download URL:
      GET /history/a1b2c3d4/pdf

    Why uuid4()[:8]?
      uuid4() generates a random 32-character ID like "550e8400-e29b-41d4-a716..."
      We take only the first 8 characters — short enough to read, long enough
      to avoid accidental collisions in a personal project.

    Why json.dumps(sources)?
      SQLite doesn't have a list/array column type.
      We serialize Python lists to JSON strings and store as TEXT.
      When we read them back, json.loads() converts back to Python lists.
    """
    # Generate a short unique ID for this report
    report_id = str(uuid.uuid4())[:8]

    # Record when this report was saved (UTC time, ISO format)
    created_at = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")

    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute(
            """
            INSERT INTO reports
              (id, topic, report_md, sources_json, sub_questions_json, url_count, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                report_id,
                topic,
                report_md,
                json.dumps(sources),         # list → JSON string
                json.dumps(sub_questions),   # list → JSON string
                len(sources),                # count of URLs found
                created_at,
            ),
        )
        conn.commit()
        logger.info(f"Report saved: id={report_id} topic={topic!r}")
    finally:
        conn.close()

    return report_id


def list_reports() -> list:
    """
    Return a summary list of all past reports, newest first.

    We deliberately do NOT return report_md here — the full report text
    can be large. The history list only needs: id, topic, url_count, created_at.
    The frontend uses these to render the history cards.

    Returns a list of dicts, e.g.:
      [
        {"id": "a1b2c3d4", "topic": "AI in healthcare", "url_count": 12, "created_at": "2025-04-14T16:30:00"},
        ...
      ]
    """
    conn = sqlite3.connect(DB_PATH)
    try:
        # ORDER BY created_at DESC = newest reports first
        rows = conn.execute(
            "SELECT id, topic, url_count, created_at FROM reports ORDER BY created_at DESC"
        ).fetchall()
    finally:
        conn.close()

    # Convert each tuple row into a dict for easy JSON serialization
    return [
        {
            "id": row[0],
            "topic": row[1],
            "url_count": row[2],
            "created_at": row[3],
        }
        for row in rows
    ]


def get_report(report_id: str) -> dict | None:
    """
    Return the full details of one report, or None if the ID doesn't exist.

    This is called when:
      - The user clicks "View" on a history item → frontend fetches GET /history/{id}
      - The user requests a PDF → backend fetches the report to convert it

    The sources and sub_questions are stored as JSON strings; we parse them
    back to Python lists before returning.
    """
    conn = sqlite3.connect(DB_PATH)
    try:
        row = conn.execute(
            """
            SELECT id, topic, report_md, sources_json, sub_questions_json, url_count, created_at
            FROM reports
            WHERE id = ?
            """,
            (report_id,),  # Always use parameterized queries — never f-strings in SQL!
        ).fetchone()
    finally:
        conn.close()

    if row is None:
        return None  # Report not found — caller should return 404

    return {
        "id": row[0],
        "topic": row[1],
        "report_md": row[2],
        "sources": json.loads(row[3]),         
        "sub_questions": json.loads(row[4]),   
        "url_count": row[5],
        "created_at": row[6],
    }


def delete_report(report_id: str) -> bool:
    """
    Delete a report by ID.

    Returns True if a row was deleted, False if the ID was not found.
    The caller uses this to decide whether to return 200 or 404.
    """
    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.execute(
            "DELETE FROM reports WHERE id = ?",
            (report_id,),
        )
        conn.commit()
        deleted = cursor.rowcount > 0  
    finally:
        conn.close()

    if deleted:
        logger.info(f"Report deleted: id={report_id}")

    return deleted
