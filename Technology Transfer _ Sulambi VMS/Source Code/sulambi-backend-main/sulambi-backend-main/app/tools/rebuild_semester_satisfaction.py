import json
import math
import os
from datetime import datetime
from dotenv import load_dotenv

from ..database.connection import cursorInstance, quote_identifier, convert_placeholders

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
is_postgresql = DATABASE_URL and DATABASE_URL.startswith('postgresql://')


def ensure_table(conn, cursor):
  if is_postgresql:
    # PostgreSQL syntax
    cursor.execute(
      """
      CREATE TABLE IF NOT EXISTS "semester_satisfaction" (
        id SERIAL PRIMARY KEY,
        year INTEGER NOT NULL,
        semester INTEGER NOT NULL CHECK (semester IN (1,2)),
        overall REAL NOT NULL,
        volunteers REAL NOT NULL,
        beneficiaries REAL NOT NULL,
        "totalEvaluations" INTEGER NOT NULL DEFAULT 0,
        "eventIds" TEXT NOT NULL DEFAULT '[]',
        "topIssues" TEXT NOT NULL DEFAULT '[]',
        "updatedAt" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(year, semester)
      );
      """
    )
  else:
    # SQLite syntax
    cursor.execute(
      """
      CREATE TABLE IF NOT EXISTS semester_satisfaction (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        year INTEGER NOT NULL,
        semester INTEGER NOT NULL CHECK (semester IN (1,2)),
        overall REAL NOT NULL,
        volunteers REAL NOT NULL,
        beneficiaries REAL NOT NULL,
        totalEvaluations INTEGER NOT NULL DEFAULT 0,
        eventIds TEXT NOT NULL DEFAULT '[]',
        topIssues TEXT NOT NULL DEFAULT '[]',
        updatedAt TEXT NOT NULL,
        UNIQUE(year, semester)
      );
      """
    )
  conn.commit()


def upsert_row(cursor, year, sem, overall, vol, ben, total, event_ids, top_issues):
  if is_postgresql:
    # PostgreSQL syntax
    table_name = quote_identifier('semester_satisfaction')
    query = f"""
    INSERT INTO {table_name}
    (year, semester, overall, volunteers, beneficiaries, "totalEvaluations", "eventIds", "topIssues", "updatedAt")
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
    ON CONFLICT(year, semester) DO UPDATE SET
      overall=EXCLUDED.overall,
      volunteers=EXCLUDED.volunteers,
      beneficiaries=EXCLUDED.beneficiaries,
      "totalEvaluations"=EXCLUDED."totalEvaluations",
      "eventIds"=EXCLUDED."eventIds",
      "topIssues"=EXCLUDED."topIssues",
      "updatedAt"=CURRENT_TIMESTAMP;
    """
    cursor.execute(
      query,
      (year, sem, overall, vol, ben, total, json.dumps(event_ids), json.dumps(top_issues)),
    )
  else:
    # SQLite syntax
    query = """
    INSERT INTO semester_satisfaction
    (year, semester, overall, volunteers, beneficiaries, totalEvaluations, eventIds, topIssues, updatedAt)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
    ON CONFLICT(year, semester) DO UPDATE SET
      overall=excluded.overall,
      volunteers=excluded.volunteers,
      beneficiaries=excluded.beneficiaries,
      totalEvaluations=excluded.totalEvaluations,
      eventIds=excluded.eventIds,
      topIssues=excluded.topIssues,
      updatedAt=datetime('now');
    """
    cursor.execute(
      query,
      (year, sem, overall, vol, ben, total, json.dumps(event_ids), json.dumps(top_issues)),
    )


def rebuild(year_filter: str | None = None):
  conn, cursor = cursorInstance()
  ensure_table(conn, cursor)

  # Pull evaluations joined to events to get dates
  internal_events_table = quote_identifier('internalEvents')
  external_events_table = quote_identifier('externalEvents')
  evaluation_table = quote_identifier('evaluation')
  requirements_table = quote_identifier('requirements')
  
  query = f"""
    SELECT e.id, e.criteria, e.finalized, e.q13, e.q14, e.comment,
           r."eventId", r.type,
           CASE 
             WHEN r.type = 'internal' THEN ei."durationStart"
             ELSE ee."durationStart"
           END as eventDate
    FROM {evaluation_table} e
    INNER JOIN {requirements_table} r ON e."requirementId" = r.id
    LEFT JOIN {internal_events_table} ei ON r."eventId" = ei.id AND r.type = 'internal'
    LEFT JOIN {external_events_table} ee ON r."eventId" = ee.id AND r.type = 'external'
    WHERE e.finalized = 1 AND e.criteria IS NOT NULL AND e.criteria != ''
  """
  cursor.execute(query)
  rows = cursor.fetchall()

  by_sem = {}
  issues: dict[str, int] = {}
  event_ids_by_sem: dict[str, set[int]] = {}

  for row in rows:
    eval_id, criteria_str, finalized, q13, q14, comment, event_id, event_type, event_date = row
    if not finalized:
      continue

    # Parse criteria
    try:
      criteria = criteria_str
      if isinstance(criteria, str):
        try:
          criteria = eval(criteria) if criteria.startswith("{") else json.loads(criteria)
        except Exception:
          criteria = {}
    except Exception:
      criteria = {}

    # Determine semester
    if event_date:
      dt = datetime.fromtimestamp(event_date / 1000)
    else:
      dt = datetime.now()
    sem_key = f"{dt.year}-{math.ceil(dt.month / 6)}"
    if year_filter and not sem_key.startswith(year_filter):
      continue

    by_sem.setdefault(sem_key, {"overall": [], "vol": [], "ben": []})
    event_ids_by_sem.setdefault(sem_key, set()).add(int(event_id) if event_id else -1)

    # Extract score
    score = 4.0
    if isinstance(criteria, dict):
      if "overall" in criteria:
        score = float(criteria["overall"])
      elif "satisfaction" in criteria:
        score = float(criteria["satisfaction"])
      elif "rating" in criteria:
        score = float(criteria["rating"])

    # For now, put into overall and vol (you can separate if respondent type is available)
    by_sem[sem_key]["overall"].append(score)
    by_sem[sem_key]["vol"].append(score)

    # Simple issue extraction
    txt = (comment or "").lower()
    for kw in ["communication", "schedule", "materials", "support", "venue", "time"]:
      if kw in txt:
        issues[kw] = issues.get(kw, 0) + 1

  # Write back
  for sem_key, data in by_sem.items():
    yr, sem = sem_key.split("-")
    overall = round(sum(data["overall"]) / max(1, len(data["overall"])), 1)
    vol = round(sum(data["vol"]) / max(1, len(data["vol"])), 1)
    ben = round(sum(data["ben"]) / max(1, len(data["ben"])) if data["ben"] else overall, 1)
    total = len(data["overall"])
    ev_ids = list(event_ids_by_sem.get(sem_key, []))

    top_issues = sorted(issues.items(), key=lambda x: x[1], reverse=True)[:5]
    top_issues_fmt = [{"issue": k.title(), "frequency": v, "category": "volunteers"} for k, v in top_issues]

    upsert_row(cursor, int(yr), int(sem), overall, vol, ben, total, ev_ids, top_issues_fmt)

  conn.commit()
  conn.close()


if __name__ == "__main__":
  # Rebuild all years by default
  rebuild(None)
  print("✓ semester_satisfaction rebuilt")














