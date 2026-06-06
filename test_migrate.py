import sqlite3, psycopg2, sys
from decimal import Decimal

PG_URL = "postgresql://postgres:rTvmePYZaOOwyYSFOHvhvltYtnhqEvai@kodama.proxy.rlwy.net:57611/railway"

print("Connecting to SQLite...", flush=True)
sqlite = sqlite3.connect("db.sqlite3")
sqlite.row_factory = sqlite3.Row

print("Connecting to PostgreSQL...", flush=True)
pg = psycopg2.connect(PG_URL)
cur = pg.cursor()

print("Copying auth_user...", flush=True)
rows = sqlite.execute("SELECT id,password,last_login,is_superuser,username,first_name,last_name,email,is_staff,is_active,date_joined FROM auth_user").fetchall()
print(f"  Found {len(rows)} users", flush=True)
for row in rows:
    vals = list(row)
    cur.execute("""INSERT INTO auth_user (id,password,last_login,is_superuser,username,first_name,last_name,email,is_staff,is_active,date_joined) 
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""", vals)
pg.commit()
print(f"  Copied {len(rows)} users", flush=True)

print("Checking result...", flush=True)
cur.execute("SELECT COUNT(*) FROM auth_user")
print(f"  PG now has {cur.fetchone()[0]} users", flush=True)

cur.close()
pg.close()
sqlite.close()
print("Test done!", flush=True)
