import sqlite3
s = sqlite3.connect("db.sqlite3")
c = s.cursor()

# Check for NULL/empty values in key fields
queries = [
    "SELECT COUNT(*) FROM auth_user WHERE first_name IS NULL OR first_name = ''",
    "SELECT COUNT(*) FROM auth_user WHERE last_name IS NULL OR last_name = ''",
    "SELECT COUNT(*) FROM employees_employee WHERE email IS NULL OR email = ''",
    "SELECT COUNT(*) FROM employees_attendance WHERE notes IS NULL",
    "SELECT COUNT(*) FROM employees_attendance WHERE notes = ''",
    "SELECT id, first_name, last_name FROM auth_user WHERE first_name IS NULL OR first_name = '' OR last_name IS NULL OR last_name = ''",
    "SELECT id, email FROM employees_employee WHERE email IS NULL OR email = ''",
]
for q in queries:
    c.execute(q)
    print(f"{q}: {c.fetchall()}")
s.close()
