import http.server
import socketserver
import re
import psycopg2
import json

## Database connection data
DATABASE = {
    'user':     'postgres',
    'password': 'postgres',
    'host':     'localhost',
    'port':     '5434',
    'database': 'postgres',
    'options': '-c search_path=ygis,public'
    }

PORT = 8081

class HelloWorldRequestHandler(http.server.BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b'Hello World!!!')

    def log_message(self, format, *args):
        print(f'{self.client_address[0]} - {format % args}')

with socketserver.TCPServer(("", PORT), HelloWorldRequestHandler) as httpd:
    print(f'Serving on port {PORT}')
    httpd.serve_forever()        