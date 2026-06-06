import psycopg2
PG_URL = "postgresql://postgres:rTvmePYZaOOwyYSFOHvhvltYtnhqEvai@kodama.proxy.rlwy.net:57611/railway"
pg = psycopg2.connect(PG_URL)
cur = pg.cursor()

# Allow NULL for fields that may have empty values
alterations = [
    "ALTER TABLE auth_user ALTER COLUMN first_name DROP NOT NULL",
    "ALTER TABLE auth_user ALTER COLUMN last_name DROP NOT NULL",
    "ALTER TABLE employees_employee ALTER COLUMN email DROP NOT NULL",
    "ALTER TABLE employees_employee ALTER COLUMN phone DROP NOT NULL",
    "ALTER TABLE employees_attendance ALTER COLUMN notes DROP NOT NULL",
    "ALTER TABLE employees_manualentryphoto ALTER COLUMN ip_address DROP NOT NULL",
    "ALTER TABLE employees_manualentryphoto ALTER COLUMN user_agent DROP NOT NULL",
]

for a in alterations:
    try:
        cur.execute(a)
        print(f"OK: {a}", flush=True)
    except Exception as e:
        print(f"SKIP: {a} -> {e}", flush=True)
pg.commit()
cur.close()
pg.close()
print("Done fixing schema.", flush=True)
