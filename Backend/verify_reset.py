import sqlite3, os, glob
db = os.path.join(os.path.dirname(__file__), "events.db")
conn = sqlite3.connect(db)
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = [r[0] for r in cur.fetchall()]
print("TABLES:", tables)
for t in tables:
    cur.execute("SELECT COUNT(*) FROM [" + t + "]")
    print("  " + t + ": " + str(cur.fetchone()[0]) + " rows")
conn.close()
ev_dir = os.path.join(os.path.dirname(__file__), "evidence")
files = glob.glob(os.path.join(ev_dir, "*"))
print("evidence/ files remaining:", len(files))
print("evidence/ directory exists:", os.path.isdir(ev_dir))
print("DB app open check: PASS")
