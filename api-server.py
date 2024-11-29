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

## Table for the MVT Tiles 
# TABLE = {
#     'table':       'ruas',
#     'srid':        '4326',
#     'geomColumn':  'geometry',
#     'attrColumns': 'osmid, nr_faixas, tipo_via, nome'
#     }

PORT = 8081

class DatabaseRequestHandler(http.server.BaseHTTPRequestHandler):

    DATABASE_CONNECTION = None
    # Functions pathToTile, tileToEnvelope, tileToEnvelope, envelopeToBoundsSQL, envelopeToSQL, sqlToPbf
    # from https://github.com/pramsey/minimal-mvt
    def pathToTile(self, path):
        m = re.search(r'^\/(\d+)\/(\d+)\/(\d+)\.(\w+)', path)
        if (m):
            return {'zoom':   int(m.group(1)), 
                    'x':      int(m.group(2)), 
                    'y':      int(m.group(3)), 
                    'format': m.group(4)}
        else:
            return None

    # Do we have all keys we need? 
    # Do the tile x/y coordinates make sense at this zoom level?
    def tileIsValid(self, tile):
        if not ('x' in tile and 'y' in tile and 'zoom' in tile):
            return False
        if 'format' not in tile or tile['format'] not in ['pbf', 'mvt']:
            return False
        size = 2 ** tile['zoom'];
        if tile['x'] >= size or tile['y'] >= size:
            return False
        if tile['x'] < 0 or tile['y'] < 0:
            return False
        return True

    # Calculate envelope in "Spherical Mercator" (https://epsg.io/3857)
    def tileToEnvelope(self, tile):
        # Width of world in EPSG:3857
        worldMercMax = 20037508.3427892
        worldMercMin = -1 * worldMercMax
        worldMercSize = worldMercMax - worldMercMin
        # Width in tiles
        worldTileSize = 2 ** tile['zoom']
        # Tile width in EPSG:3857
        tileMercSize = worldMercSize / worldTileSize
        # Calculate geographic bounds from tile coordinates
        # XYZ tile coordinates are in "image space" so origin is
        # top-left, not bottom right
        env = dict()
        env['xmin'] = worldMercMin + tileMercSize * tile['x']
        env['xmax'] = worldMercMin + tileMercSize * (tile['x'] + 1)
        env['ymin'] = worldMercMax - tileMercSize * (tile['y'] + 1)
        env['ymax'] = worldMercMax - tileMercSize * (tile['y'])
        return env

    # Generate SQL to materialize a query envelope in EPSG:3857.
    # Densify the edges a little so the envelope can be
    # safely converted to other coordinate systems.
    def envelopeToBoundsSQL(self, env):
        DENSIFY_FACTOR = 4
        env['segSize'] = (env['xmax'] - env['xmin'])/DENSIFY_FACTOR
        sql_tmpl = 'ST_Segmentize(ST_MakeEnvelope({xmin}, {ymin}, {xmax}, {ymax}, 3857),{segSize})'
        return sql_tmpl.format(**env)

    # Generate a SQL query to pull a tile worth of MVT data
    # from the table of interest.
    # WITH bounds AS (SELECT ST_Segmentize(ST_MakeEnvelope(-5497351.074269865, -3334488.921912521, -5496739.578043582, -3333877.42568624, 3857),152.87405657069758) AS geom, ST_Segmentize(ST_MakeEnvelope(-5497351.074269865, -3334488.921912521, -5496739.578043582, -3333877.42568624, 3857),152.87405657069758)::box2d AS b2d), mvtgeom AS (SELECT ST_AsMVTGeom(ST_Transform(t.geometry, 3857), bounds.b2d) AS geom, osmid, nr_faixas, tipo_via, nome FROM ruas t, bounds WHERE ST_Intersects(t.geometry, ST_Transform(bounds.geom, 4326))) SELECT ST_AsMVT(mvtgeom.*) FROM mvtgeom        
    def envelopeToSQL(self, env, table):
        tbl = table.copy()
        tbl['env'] = self.envelopeToBoundsSQL(env)
        # Materialize the bounds
        # Select the relevant geometry and clip to MVT bounds
        # Convert to MVT format
        sql_tmpl = """WITH bounds AS (SELECT {env} AS geom, {env}::box2d AS b2d), mvtgeom AS (SELECT ST_AsMVTGeom(ST_Transform(t.{geomColumn}, 3857), bounds.b2d) AS geom, {attrColumns} FROM {table} t, bounds WHERE ST_Intersects(t.{geomColumn}, ST_Transform(bounds.geom, {srid}))) SELECT ST_AsMVT(mvtgeom.*) FROM mvtgeom"""
        return sql_tmpl.format(**tbl)

    # Run tile query SQL and return error on failure conditions
    def sqlToPbf(self, sql):
        # Make and hold connection to database
        if not self.DATABASE_CONNECTION: ## Não esta reconhecendo essa variável?! Mesmo se trocar para DATABASE.
            try:
                self.DATABASE_CONNECTION = psycopg2.connect(**DATABASE)
            except (Exception, psycopg2.Error) as error:
                self.send_error(500, "FUck! cannot connect: %s" % (str(DATABASE)))
                return None

        # Query for MVT
        with self.DATABASE_CONNECTION.cursor() as cur:
            cur.execute(sql)
            if not cur:
                self.send_error(404, "sql query failed: %s" % (sql))
                return None
            return cur.fetchone()[0]
        
        return None

    def do_GET(self):
        parsed_url = urlparse(self.path)

        if parsed_url.path.startswith('/vector-tiles'):
            path = self.path

            if parsed_url.path.startswith('/vector-tiles/ruas'):
                path = self.path[len('/vector-tiles/ruas'):]
                TABLE = {'table': 'ruas', 'srid': '4326', 'geomColumn':  'geometry', 'attrColumns': 'osmid, nr_faixas, tipo_via, nome'}
                pbf = self.handle_tiles_request(path, TABLE)

            elif parsed_url.path.startswith('/vector-tiles/escolas'):
                path = self.path[len('/vector-tiles/escolas'):]
                TABLE = {'table': 'escolas', 'srid': '4326', 'geomColumn':  'geometry', 'attrColumns': 'osmid, nome'}
                pbf = self.handle_tiles_request(path, TABLE)

            self.send_response(200)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-type", "application/vnd.mapbox-vector-tile")
            self.end_headers()
            self.wfile.write(pbf)

        elif parsed_url.path == '/data/ruas':
            query_params = parse_qs(parsed_url.query)
            lat = query_params.get('lat', [None])[0]
            lon = query_params.get('lon', [None])[0]
            self.handle_ruas_request(lat, lon)
        
        else:
            self.send_error(404, "Ops! Invalid endpoint: %s" % (self.path))
    
    def handle_tiles_request(self, path, table):
        tile = self.pathToTile(path)

        if not (tile and self.tileIsValid(tile)):
            self.send_error(400, "Invalid tile path: %s" % (self.path))
            return

        env = self.tileToEnvelope(tile)
        sql = self.envelopeToSQL(env, table)
        pbf = self.sqlToPbf(sql)

        return pbf

    def handle_ruas_request(self, lat, lon):
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

    def fetch_ruas_data(self, lat, lon, radius=0.00005):
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