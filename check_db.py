import sqlite3
s = sqlite3.connect("db.sqlite3")
c = s.cursor()
tables = ['auth_user','employees_employee','employees_attendance',
          'employees_manualentryphoto','employees_userprofile','employees_monthlysalary']
for t in tables:
    try:
        c.execute(f"SELECT COUNT(*) FROM {t}")
        print(f"{t}: {c.fetchone()[0]}")
    except Exception as e:
        print(f"{t}: ERROR - {e}")
s.close()
