import psycopg2
pg = psycopg2.connect("postgresql://postgres:rTvmePYZaOOwyYSFOHvhvltYtnhqEvai@kodama.proxy.rlwy.net:57611/railway")
cur = pg.cursor()
tables = ['auth_user','employees_employee','employees_attendance','employees_manualentryphoto','employees_userprofile','employees_monthlysalary']
for t in tables:
    try:
        cur.execute(f'SELECT COUNT(*) FROM "{t}"')
        c = cur.fetchone()[0]
        print(f'{t}: {c}')
    except Exception as e:
        print(f'{t}: ERROR - {e}')
cur.close()
pg.close()
