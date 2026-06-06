import sqlite3
import psycopg2
import json
from datetime import date, time, datetime
from decimal import Decimal

PG_URL = "postgresql://postgres:rTvmePYZaOOwyYSFOHvhvltYtnhqEvai@kodama.proxy.rlwy.net:57611/railway"

sqlite = sqlite3.connect("db.sqlite3")
sqlite.row_factory = sqlite3.Row
pg = psycopg2.connect(PG_URL)
pg.autocommit = False
cur = pg.cursor()

# Truncate all tables first (order matters for FK)
tables = [
    'employees_monthlysalary',
    'employees_attendance',
    'employees_manualentryphoto',
    'employees_userprofile',
    'employees_employee',
    'django_session',
    'auth_user',
    'auth_group_permissions',
    'auth_user_groups',
    'auth_user_user_permissions',
    'admin_logentry',
    'django_admin_log',
    'authtoken_token',
]
for t in tables:
    try:
        cur.execute(f'TRUNCATE TABLE "{t}" CASCADE')
    except:
        pass
pg.commit()

def copy_table(table, cols, cur):
    rows = sqlite.execute(f'SELECT {",".join(cols)} FROM {table}').fetchall()
    if not rows:
        print(f'  {table}: 0 rows')
        return
    placeholders = ",".join(["%s"] * len(cols))
    quoted_cols = ",".join(f'"{c}"' for c in cols)
    for row in rows:
        values = list(row)
        for i, v in enumerate(values):
            if isinstance(v, str) and v.startswith('\\\\x'):
                values[i] = bytes.fromhex(v[4:])
        try:
            cur.execute(f'INSERT INTO "{table}" ({quoted_cols}) VALUES ({placeholders})', values)
        except Exception as e:
            print(f'  Error in {table} pk={row[0] if cols else "?"}: {e}')
    pg.commit()
    print(f'  {table}: {len(rows)} rows')

# auth_user
print('Copying auth_user...')
cols = ['id', 'password', 'last_login', 'is_superuser', 'username', 'first_name', 'last_name', 'email', 'is_staff', 'is_active', 'date_joined']
copy_table('auth_user', cols, cur)

# employees_employee
print('Copying employees_employee...')
cols = ['id', 'first_name', 'last_name', 'position', 'department', 'phone', 'email', 'photo', 'work_days', 'work_schedule', 'monthly_salary', 'late_penalty_per_minute', 'allowed_late_minutes', 'daily_work_hours', 'is_active', 'created_at']
copy_table('employees_employee', cols, cur)

# employees_attendance
print('Copying employees_attendance...')
cols = ['id', 'employee_id', 'date', 'time', 'type', 'status', 'late_minutes', 'penalty_amount', 'notes', 'created_at']
copy_table('employees_attendance', cols, cur)

# employees_manualentryphoto
print('Copying employees_manualentryphoto...')
cols = ['id', 'employee_id', 'photo', 'captured_at', 'ip_address', 'user_agent', 'attendance_type']
copy_table('employees_manualentryphoto', cols, cur)

# employees_userprofile
print('Copying employees_userprofile...')
cols = ['id', 'user_id', 'user_type', 'phone', 'department', 'employee_id', 'created_at', 'updated_at']
copy_table('employees_userprofile', cols, cur)

# employees_monthlysalary
print('Copying employees_monthlysalary...')
cols = ['id', 'employee_id', 'year', 'month', 'basic_salary', 'total_penalty', 'total_bonus', 'net_salary', 'work_days', 'present_days', 'late_days', 'absent_days', 'day_off_days', 'total_late_minutes', 'notes', 'is_paid', 'paid_date', 'created_at', 'updated_at']
copy_table('employees_monthlysalary', cols, cur)

# django_session
print('Copying django_session...')
cols = ['session_key', 'session_data', 'expire_date']
copy_table('django_session', cols, cur)

# admin_logentry
print('Copying admin_logentry...')
cols = ['id', 'action_time', 'user_id', 'content_type_id', 'object_id', 'object_repr', 'action_flag', 'change_message']
copy_table('admin_logentry', cols, cur)

# Reset sequences
try:
    cur.execute("SELECT setval('auth_user_id_seq', (SELECT MAX(id) FROM auth_user))")
    cur.execute("SELECT setval('employees_employee_id_seq', (SELECT MAX(id) FROM employees_employee))")
    cur.execute("SELECT setval('employees_attendance_id_seq', (SELECT MAX(id) FROM employees_attendance))")
    cur.execute("SELECT setval('employees_manualentryphoto_id_seq', (SELECT MAX(id) FROM employees_manualentryphoto))")
    cur.execute("SELECT setval('employees_userprofile_id_seq', (SELECT MAX(id) FROM employees_userprofile))")
    cur.execute("SELECT setval('employees_monthlysalary_id_seq', (SELECT MAX(id) FROM employees_monthlysalary))")
    cur.execute("SELECT setval('django_admin_log_id_seq', (SELECT MAX(id) FROM admin_logentry))")
    pg.commit()
    print('Sequences reset.')
except Exception as e:
    print(f'Sequence reset warning: {e}')
    pg.rollback()

cur.close()
pg.close()
sqlite.close()
print('Done!')
