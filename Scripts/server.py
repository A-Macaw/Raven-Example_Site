import http.server
import ssl
import os
import subprocess
import threading
import urllib.parse
from datetime import datetime

# Configuration
# Detect project root folder ("Raven")
base_dir = os.path.dirname(os.path.abspath(__file__))
current = base_dir
root_dir = None

while current != os.path.dirname(current):
    if os.path.basename(current) == "Raven":
        root_dir = current
        break
    current = os.path.dirname(current)

if root_dir is None:
    raise FileNotFoundError("Could not find Raven root directory")

# Serve HTML from the correct location (clone-safe)
SERVE_DIR = os.path.join(root_dir, "Articles-html")
HOST = "0.0.0.0"
HTTP_PORT = 80
HTTPS_PORT = 443
CERT_FILE = "server.pem"

os.chdir(SERVE_DIR)

# Function to check if certificate is expired
def cert_expired(cert_path):
    try:
        # Get expiry date from the cert
        result = subprocess.run(
            ["openssl", "x509", "-enddate", "-noout", "-in", cert_path],
            capture_output=True, text=True, check=True
        )
        # Output is like: "notAfter=Dec  3 14:25:05 2025 GMT"
        not_after_str = result.stdout.strip().split('=')[1]
        expiry_date = datetime.strptime(not_after_str, "%b %d %H:%M:%S %Y %Z")
        return datetime.utcnow() > expiry_date
    except Exception as e:
        print(f"Error checking certificate: {e}")
        return True  # Treat errors as expired

# Generate self-signed cert if missing or expired
if not os.path.exists(CERT_FILE) or cert_expired(CERT_FILE):
    print("Generating new self-signed certificate...")
    subprocess.run([
        "openssl", "req", "-new", "-x509",
        "-keyout", CERT_FILE, "-out", CERT_FILE,
        "-days", "365", "-nodes", "-subj", "/CN=localhost"
    ], check=True)

# HTTPS handler
class SecureHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path in ("/main", "/main.html"):
            self.send_response(301)
            self.send_header("Location", "/")
            self.end_headers()
            return

        if self.path == "/" and os.path.exists("main.html"):
            self.path = "/main.html"

        if self.path.endswith(".text"):
            decoded_path = urllib.parse.unquote(self.path.lstrip("/").rsplit(".text", 1)[0])
            md_path = os.path.join(os.path.dirname(SERVE_DIR), "Articles-md", decoded_path + ".md")
            if os.path.exists(md_path):
                self.send_response(200)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.end_headers()
                with open(md_path, "r", encoding="utf-8") as f:
                    self.wfile.write(f.read().encode("utf-8"))
                return
            else:
                self.send_error(404, "Markdown not found")
                return

        raw_path = self.path.lstrip("/")
        fs_path = urllib.parse.unquote(raw_path)
        if not os.path.exists(fs_path):
            if not fs_path.endswith(".html") and os.path.exists(fs_path + ".html"):
                self.path = "/" + fs_path + ".html"
                fs_path = urllib.parse.unquote(self.path.lstrip("/"))

        if not os.path.exists(fs_path):
            if os.path.exists("404.html"):
                self.path = "/404.html"
            else:
                self.send_error(404, "File not found")
                return

        return super().do_GET()

# HTTP → HTTPS redirect
class RedirectToHTTPSHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        host = self.headers.get("Host", "localhost").split(":")[0]
        new_url = f"https://{host}{self.path}" if HTTPS_PORT == 443 else f"https://{host}:{HTTPS_PORT}{self.path}"
        self.send_response(301)
        self.send_header("Location", new_url)
        self.end_headers()

    def log_message(self, format, *args):
        return

# Run HTTPS server
def run_https():
    httpsd = http.server.HTTPServer((HOST, HTTPS_PORT), SecureHandler)
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(certfile=CERT_FILE)
    httpsd.socket = context.wrap_socket(httpsd.socket, server_side=True)
    httpsd.serve_forever()

# Run HTTP redirect
def run_http_redirect():
    httpd = http.server.HTTPServer((HOST, HTTP_PORT), RedirectToHTTPSHandler)
    httpd.serve_forever()

if __name__ == "__main__":
    threading.Thread(target=run_http_redirect, daemon=True).start()
    try:
        run_https()
    except KeyboardInterrupt:
        print("\nReceived Keyboard Interrupt")
