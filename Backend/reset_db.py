"""
reset_db.py — Safe test-data reset for MARG-DRISHTI events.db.

What this script does:
  1. Connects to the existing events.db (does NOT delete or recreate the file).
  2. Captures the full schema (CREATE TABLE statements) BEFORE making any changes.
  3. Deletes all rows from every data table using DELETE FROM (not DROP TABLE),
     so the schema is completely preserved.
  4. Resets SQLite AUTOINCREMENT sequences (sqlite_sequence rows).
  5. Runs VACUUM to reclaim space.
  6. Verifies all tables still exist with 0 rows.
  7. Removes all files inside evidence/ WITHOUT deleting the directory itself.
  8. Prints a detailed report.

No application source code is changed.
"""

import sqlite3
import os
import glob

DB_PATH    = os.path.join(os.path.dirname(__file__), "events.db")
EVIDENCE_DIR = os.path.join(os.path.dirname(__file__), "evidence")

# ── 1. Capture current schema ────────────────────────────────────────────────
print("=" * 60)
print("MARG-DRISHTI  —  Safe DB Reset")
print("=" * 60)

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

cur.execute("SELECT name, sql FROM sqlite_master WHERE type='table' ORDER BY name")
schema_rows = cur.fetchall()
tables = [r["name"] for r in schema_rows]

print(f"\nDatabase : {DB_PATH}")
print(f"Tables found: {tables}\n")

# ── 2. Row counts BEFORE reset ───────────────────────────────────────────────
print("Row counts BEFORE reset:")
for t in tables:
    cur.execute(f"SELECT COUNT(*) FROM [{t}]")
    print(f"  {t:25s}: {cur.fetchone()[0]:>6} rows")

# ── 3. Delete all data rows (schema-preserving DELETE, not DROP) ─────────────
print("\nDeleting all data rows...")
# Delete in dependency order so FK constraints (even if not enforced) are respected
delete_order = ["evidence", "clusters", "hotspots", "events"]
for t in delete_order:
    if t in tables:
        cur.execute(f"DELETE FROM [{t}]")
        print(f"  DELETE FROM {t}")

# Also clear any tables not in our fixed list (future-proof)
for t in tables:
    if t not in delete_order:
        cur.execute(f"DELETE FROM [{t}]")
        print(f"  DELETE FROM {t} (extra table)")

# ── 4. Reset AUTOINCREMENT sequences ────────────────────────────────────────
cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sqlite_sequence'")
if cur.fetchone():
    cur.execute("DELETE FROM sqlite_sequence")
    print("\nReset sqlite_sequence (AUTOINCREMENT counters).")

conn.commit()

# ── 5. VACUUM to reclaim space ───────────────────────────────────────────────
conn.execute("VACUUM")
print("VACUUM complete.")

# ── 6. Verify schema and row counts AFTER reset ──────────────────────────────
cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables_after = [r[0] for r in cur.fetchall()]

print(f"\nRow counts AFTER reset:")
all_empty = True
for t in tables_after:
    cur.execute(f"SELECT COUNT(*) FROM [{t}]")
    n = cur.fetchone()[0]
    print(f"  {t:25s}: {n:>6} rows")
    if n != 0:
        all_empty = False

conn.close()

schema_ok = sorted(tables) == sorted(tables_after)
print(f"\nSchema preserved : {'YES ✓' if schema_ok else 'NO — MISMATCH'}")
print(f"All tables empty : {'YES ✓' if all_empty else 'NO — ROWS REMAIN'}")

# ── 7. Clear evidence video files (keep directory) ───────────────────────────
print(f"\nClearing evidence files from: {EVIDENCE_DIR}")
if not os.path.isdir(EVIDENCE_DIR):
    print("  evidence/ directory does not exist — nothing to clear.")
else:
    files = glob.glob(os.path.join(EVIDENCE_DIR, "*"))
    if not files:
        print("  evidence/ is already empty.")
    else:
        removed = 0
        for f in files:
            if os.path.isfile(f):
                os.remove(f)
                print(f"  Removed: {os.path.basename(f)}")
                removed += 1
        print(f"  {removed} file(s) removed. Directory kept.")

# ── 8. Final summary ──────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("RESET COMPLETE")
print(f"  events.db schema : PRESERVED (tables: {tables_after})")
print(f"  All rows deleted : YES")
print(f"  AUTOINCREMENT    : RESET")
print(f"  evidence/ files  : CLEARED (directory kept)")
print("=" * 60)
print("\nYou can now start the server and run fresh scenario tests.")
print("Command: uvicorn main:app --host 0.0.0.0 --port 8000")
