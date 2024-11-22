import http.server
import socketserver
import re
import psycopg2
import json
from urllib.parse import urlparse, parse_qs

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

class DatabaseRequestHandler(http.server.BaseHTTPRequestHandler):

    def do_GET(self):
        parsed_url = urlparse(self.path)

        if parsed_url.path == '/data/ruas':
            query_params = parse_qs(parsed_url.query)
            lat = query_params.get('lat', [None])[0]
            lon = query_params.get('lon', [None])[0]
        
        try:
            if lat and lon:
                data = self.fetch_ruas_data(lat, lon)
                if data:
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.send_header("Access-Control-Allow-Origin", "http://localhost:5173")  # Allow all origins, or specify your frontend domain
                    self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
                    self.send_header("Access-Control-Allow-Headers", "Content-Type")
                    self.end_headers()
                    self.wfile.write(json.dumps(data).encode('UTF-8'))
        
                else:
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.send_header("Access-Control-Allow-Origin", "http://localhost:5173")
                    self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
                    self.send_header("Access-Control-Allow-Headers", "Content-Type")
                    self.end_headers()
                    self.wfile.write(json.dumps([]).encode('UTF-8'))  # Return an empty array

            else:
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Iak! Missing coordinates!"}).encode("utf-8"))
        
        except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))

    def do_OPTIONS(self):
        # Handle preflight requests
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "http://localhost:5173")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def fetch_ruas_data(self, lat, lon, radius=0.00001):
        try:
            conn = psycopg2.connect(**DATABASE)
            cursor = conn.cursor()

            cursor.execute("""SELECT osmid, nome, nr_faixas, tipo_via, comprimento, observacao FROM ygis.ruas 
                           WHERE ST_DWithin(geometry, ST_SetSRID(ST_Point(%s, %s), 4326), %s);""",
                           (lon, lat, radius))
            rows = cursor.fetchall()

            col_names = [desc[0] for desc in cursor.description]
            data = [dict(zip(col_names, row)) for row in rows]

            cursor.close()
            conn.close()

            return data
        except Exception as e:
            print('Arh! Error fetching data: ', e)
            return None
        
    def send_error_response(self, code, message):
        self.send_response(code)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        error_html = f"<html><body><h1>Error {code}: {message}</h1></body></html>"
        self.wfile.write(error_html.encode('utf-8'))

    def log_message(self, format, *args):
        print(f'{self.client_address[0]} - {format % args}')

with socketserver.TCPServer(("", PORT), DatabaseRequestHandler) as httpd:
    print(f'Serving on port {PORT}')
    httpd.serve_forever()        