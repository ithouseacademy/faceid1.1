import psycopg2
pg = psycopg2.connect("postgresql://postgres:rTvmePYZaOOwyYSFOHvhvltYtnhqEvai@kodama.proxy.rlwy.net:57611/railway")
cur = pg.cursor()
tables = ['auth_user','employees_employee','employees_attendance','employees_manualentryphoto','employees_userprofile','employees_monthlysalary']
for t in tables:
    print(f"\n--- {t} ---")
    cur.execute(f"""
        SELECT column_name, is_nullable, data_type 
        FROM information_schema.columns 
        WHERE table_name = '{t}'
        ORDER BY ordinal_position
    """)
    for row in cur.fetchall():
        print(f"  {row[0]:30s} nullable={row[1]:5s} type={row[2]}")
cur.close()
pg.close()
