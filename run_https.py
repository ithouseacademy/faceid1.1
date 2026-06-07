import ssl
import sys
import os
from wsgiref.simple_server import make_server

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "employee_face_recognition.settings")
from django.core.wsgi import get_wsgi_application
app = get_wsgi_application()

cert_file = "cert.pem"
key_file = "key.pem"

if not os.path.exists(cert_file) or not os.path.exists(key_file):
    print("cert.pem yoki key.pem topilmadi. Avval ularni yarating:")
    print("  python -c \"from cryptography import x509; ...\"")
    sys.exit(1)

httpd = make_server("127.0.0.1", 8000, app)
httpd.socket = ssl.wrap_socket(httpd.socket, certfile=cert_file, keyfile=key_file, server_side=True)
print("HTTPS server ishlayapti: https://127.0.0.1:8000/")
httpd.serve_forever()
