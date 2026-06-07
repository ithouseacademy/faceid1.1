@echo off
cd /d "%~dp0"
python manage.py runserver_plus --cert-file cert.pem --key-file key.pem 127.0.0.1:8000
pause
