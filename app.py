import psycopg2
from flask import Flask, jsonify
from flask_cors import CORS  # Importante para permitir la conexión desde el frontend

# --- Configuración de la Aplicación ---
app = Flask(__name__)
# Habilita CORS para que tu index.html pueda hacerle peticiones
CORS(app)

# --- ¡MODIFICA ESTO! ---
# Coloca aquí las credenciales de tu base de datos
DATABASE_CONFIG = {
    'dbname': 'chile_routing_economico',
    'user': 'postgres',  # Tu usuario de PostgreSQL
    'password': 'Monita315@',  # Tu contraseña
    'host': 'localhost',  # O la IP de tu servidor de BD
    'port': '5432'  # Puerto por defecto de Postgres
}


# --- Funciones de Base de Datos ---

def get_db_connection():
    """Crea una conexión a la base de datos."""
    try:
        conn = psycopg2.connect(**DATABASE_CONFIG)
        return conn
    except Exception as e:
        print(f"Error al conectar a la base de datos: {e}")
        return None


def fetch_geojson(query):
    """Ejecuta una consulta que devuelve un único resultado GeoJSON."""
    conn = get_db_connection()
    if conn is None:
        return None, "Error de conexión a la BD"

    try:
        with conn.cursor() as cur:
            cur.execute(query)
            # json_agg y json_build_object devuelven una sola fila
            result = cur.fetchone()
            return result[0] if result else None
    except Exception as e:
        print(f"Error en la consulta: {e}")
        return None, str(e)
    finally:
        conn.close()


# --- Definición de las API (Endpoints) ---

@app.route("/")
def index():
    """Página de inicio simple para saber que el backend funciona."""
    return "El servidor de la API de GeoJSON está funcionando."


@app.route("/api/peajes")
def get_peajes():
    """
    Endpoint para obtener todos los peajes como una FeatureCollection de GeoJSON.
    """
    # Esta consulta es idéntica a la que usamos en psql
    # Construye el GeoJSON directamente en la base de datos (¡muy eficiente!)
    query = """
            SELECT json_build_object(
                           'type', 'FeatureCollection',
                           'features', json_agg(
                                   json_build_object(
                                           'type', 'Feature',
                                           'geometry', ST_AsGeoJSON(geom)::json,
                                           'properties', json_build_object(
                                                   'nombre', nombre,
                                                   'tipo', tipo,
                                                   'concesionaria', concesionaria
                                                         )
                                   )
                                       )
                   )
            FROM peajes; \
            """

    geojson_data, error = fetch_geojson(query)

    if geojson_data:
        return jsonify(geojson_data)
    else:
        return jsonify({"error": error or "No se encontraron datos"}), 500


@app.route("/api/bencineras")
def get_bencineras():
    """
    Endpoint para obtener todas las bencineras como una FeatureCollection de GeoJSON.
    """
    query = """
            SELECT json_build_object(
                           'type', 'FeatureCollection',
                           'features', json_agg(
                                   json_build_object(
                                           'type', 'Feature',
                                           'geometry', ST_AsGeoJSON(geom)::json,
                                           'properties', json_build_object(
                                                   'nombre', nombre,
                                                   'marca', marca,
                                                   'direccion', direccion,
                                                   'precio_gasolina_93', precio_gasolina_93,
                                                   'precio_gasolina_95', precio_gasolina_95,
                                                   'precio_gasolina_97', precio_gasolina_97,
                                                   'precio_diesel', precio_diesel
                                                         )
                                   )
                                       )
                   )
            FROM bencineras; \
            """

    geojson_data, error = fetch_geojson(query)

    if geojson_data:
        return jsonify(geojson_data)
    else:
        return jsonify({"error": error or "No se encontraron datos"}), 500


# --- Ejecutar la Aplicación ---
if __name__ == '__main__':
    # Ejecuta la app en modo de desarrollo (debug=True)
    # Se hosteará en http://127.0.0.1:5000
    app.run(debug=True, port=5000)