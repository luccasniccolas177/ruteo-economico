from flask import Flask, render_template, jsonify
import psycopg2
import os
import json  # Asegúrate de importar json
from dotenv import load_dotenv

# Cargar variables de entorno desde el archivo .env
load_dotenv()

app = Flask(__name__)

# Configuración de la conexión a la base de datos desde variables de entorno
db_config = {
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432")
}


def get_db_connection():
    """Crea y retorna una conexión a la base de datos."""
    conn = psycopg2.connect(**db_config)
    return conn


@app.route('/')
def index():
    """Renderiza la página principal del mapa."""
    return render_template('index.html')


@app.route('/api/ruta_ejemplo')
def get_ruta_ejemplo():
    """
    Calcula una ruta de ejemplo usando pgr_dijkstra y la devuelve como GeoJSON.
    """
    # Nodos de ejemplo (puedes cambiarlos por cualquier ID de la tabla planet_osm_line_vertices_pgr)
    # Por ejemplo, un recorrido por la Alameda en Santiago.
    nodo_inicio = 115254
    nodo_fin = 103233

    # --- CORRECCIONES AQUÍ ---
    # 1. La tabla principal ahora es 'planet_osm_line'.
    # 2. La columna de geometría es 'way', no 'the_geom'.
    # 3. La columna de ID es 'osm_id', no 'id'.
    query = """
            SELECT ST_AsGeoJSON(ST_Collect(geom)) AS route
            FROM (SELECT ways.way as geom \
                  FROM pgr_dijkstra( \
                               'SELECT osm_id AS id, source, target, cost FROM planet_osm_line WHERE highway IS NOT NULL', \
                               %s, %s, directed := false \
                       ) AS di \
                           JOIN planet_osm_line AS ways ON di.edge = ways.osm_id) AS route_geom; \
            """

    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(query, (nodo_inicio, nodo_fin))
        result = cur.fetchone()

        if result and result[0]:
            # La consulta devuelve un GeoJSON, lo convertimos a un objeto Python y lo retornamos
            return jsonify(json.loads(result[0]))
        else:
            return jsonify({"error": "No se pudo calcular la ruta."}), 404

    except psycopg2.Error as e:
        print(f"Error de base de datos: {e}")
        return jsonify({"error": "Error de conexión con la base de datos."}), 500
    finally:
        if conn:
            conn.close()


if __name__ == '__main__':
    app.run(debug=True, port=5001, host='0.0.0.0')