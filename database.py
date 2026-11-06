import sqlite3
import json

DB_NAME = "reports.db"

conn = sqlite3.connect(
    DB_NAME,
    check_same_thread= False
)

cursor = conn.cursor()

try:
    cursor.execute("""
    ALTER TABLE reports ADD COLUMN pdf_path TEXT
    """)

    conn.commit()
except sqlite3.OperationalError:
    pass

cursor.execute("""
CREATE TABLE IF NOT EXISTS reports(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_name TEXT,
    report_text TEXT,
    analysis_json TEXT,
    pdf_path TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")

conn.commit()

def save_report(report_name, report_text, analysis_json, pdf_path=None):
    cursor.execute(
        """
        INSERT INTO reports(
        report_name,
        report_text,
        analysis_json,
        pdf_path
        )
        VALUES (?, ?, ?, ?)
        """,
        (
            report_name,
            report_text,
            json.dumps(analysis_json),
            pdf_path
        )
    )
    conn.commit()

def get_reports():
    cursor.execute("""
    SELECT id, report_name, report_text, analysis_json, pdf_path, created_at
    FROM reports
    ORDER BY id DESC
    """)

    return cursor.fetchall()

def load_report(report_id):
    cursor.execute("""
    SELECT report_text, analysis_json, pdf_path
    FROM reports
    WHERE id = ?
    """,
    (report_id,)
    )
    return cursor.fetchone()
