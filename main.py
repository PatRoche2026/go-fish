"""
Go Fish — Web-Based Card Game
Serves an interactive Go Fish game in the browser.
Built for MIT Sloan 15.573 (GenAI for Managers)
"""

from http.server import HTTPServer, SimpleHTTPRequestHandler
import os

PORT = int(os.environ.get("PORT", 3000))

class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/" or self.path == "":
            self.path = "/index.html"
        return super().do_GET()

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    server = HTTPServer(("0.0.0.0", PORT), Handler)
    print(f"Go Fish running at http://localhost:{PORT}")
    server.serve_forever()
