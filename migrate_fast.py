import sqlite3, psycopg2, sys, io, json, csv
from decimal import Decimal

PG_URL = "postgresql://postgres:rTvmePYZaOOwyYSFOHvhvltYtnhqEvai@kodama.proxy.rlwy.net:57611/railway"

print("Connecting...", flush=True)
sqlite = sqlite3.connect("db.sqlite3")
sqlite.row_factory = sqlite3.Row
pg = psycopg2.connect(PG_URL)
cur = pg.cursor()
cur.execute("SET session_replication_role = 'replica'")

def copy_via_csv(table, cols):
    rows = sqlite.execute(f'SELECT {",".join(cols)} FROM {table}').fetchall()
    print(f'  {table}: {len(rows)} rows', flush=True)
    if not rows:
        return
    buf = io.StringIO()
    writer = csv.writer(buf)
    for row in rows:
        vals = list(row)
        for i, v in enumerate(vals):
            col = cols[i]
            if isinstance(v, int) and col in ('is_superuser','is_staff','is_active','is_paid'):
                vals[i] = 't' if v else 'f'
            elif isinstance(v, Decimal):
                vals[i] = float(v)
            elif isinstance(v, str) and col in ('work_days','work_schedule'):
                vals[i] = json.dumps(json.loads(v))
            elif v is None:
                vals[i] = '\\N'
            elif isinstance(v, str) and v == '':
                vals[i] = ''
            elif isinstance(v, str):
                vals[i] = v
        writer.writerow(vals)
    buf.seek(0)
    qcols = ",".join(f'"{c}"' for c in cols)
    try:
        cur.copy_expert(f'COPY "{table}" ({qcols}) FROM STDIN WITH CSV', buf)
        pg.commit()
    except Exception as e:
        print(f'    ERROR: {e}', flush=True)
        pg.rollback()

# Truncate all
for t in ['employees_monthlysalary','employees_attendance','employees_manualentryphoto','employees_userprofile','employees_employee','auth_user']:
    try:
        cur.execute(f'TRUNCATE TABLE "{t}" CASCADE')
    except:
        pass
pg.commit()

copy_via_csv('auth_user', ['id','password','last_login','is_superuser','username','first_name','last_name','email','is_staff','is_active','date_joined'])
copy_via_csv('employees_employee', ['id','first_name','last_name','position','department','phone','email','photo','work_days','work_schedule','monthly_salary','late_penalty_per_minute','allowed_late_minutes','daily_work_hours','is_active','created_at'])
copy_via_csv('employees_userprofile', ['id','user_id','user_type','phone','department','employee_id','created_at','updated_at'])
copy_via_csv('employees_attendance', ['id','employee_id','date','time','type','status','late_minutes','penalty_amount','notes','created_at'])
copy_via_csv('employees_manualentryphoto', ['id','employee_id','photo','captured_at','ip_address','user_agent','attendance_type'])
copy_via_csv('employees_monthlysalary', ['id','employee_id','year','month','basic_salary','total_penalty','total_bonus','net_salary','work_days','present_days','late_days','absent_days','day_off_days','total_late_minutes','notes','is_paid','paid_date','created_at','updated_at'])

# Reset sequences
for seq, tbl in [
    ('auth_user_id_seq','auth_user'),
    ('employees_employee_id_seq','employees_employee'),
    ('employees_attendance_id_seq','employees_attendance'),
    ('employees_manualentryphoto_id_seq','employees_manualentryphoto'),
    ('employees_userprofile_id_seq','employees_userprofile'),
    ('employees_monthlysalary_id_seq','employees_monthlysalary'),
]:
    try:
        cur.execute(f"SELECT setval('{seq}', (SELECT MAX(id) FROM {tbl}))")
    except Exception as e:
        print(f'  seq {seq}: {e}', flush=True)
pg.commit()

cur.execute("SET session_replication_role = 'origin'")
pg.commit()
cur.close()
pg.close()
sqlite.close()
print("\nDone! All data migrated via COPY.", flush=True)
