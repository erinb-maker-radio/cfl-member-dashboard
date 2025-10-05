"""
Dashboard Server
================
Runs a local web server to host the CFL Member Dashboard

Usage:
    python run_dashboard.py
"""

import http.server
import socketserver
import webbrowser
import os
from pathlib import Path

PORT = 8000
DIRECTORY = Path(__file__).parent

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DIRECTORY), **kwargs)

def main():
    os.chdir(DIRECTORY)

    with socketserver.TCPServer(("", PORT), MyHTTPRequestHandler) as httpd:
        url = f"http://localhost:{PORT}/dashboard.html"
        print(f"🚀 Dashboard server running!")
        print(f"📊 Open your browser to: {url}")
        print(f"Press Ctrl+C to stop the server\n")

        # Try to open browser automatically
        try:
            webbrowser.open(url)
        except:
            pass

        httpd.serve_forever()

if __name__ == "__main__":
    main()
