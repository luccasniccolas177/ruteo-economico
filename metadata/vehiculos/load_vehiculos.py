# Archivo: metadata/vehiculos/load_vehiculos.py
import json
import os
import psycopg2
from dotenv import load_dotenv

def load_data_to_db(json_file_path):
    """
    Lee datos de un archivo JSON y los carga en las tablas normalizadas
    marcas, modelos y versiones de la base de datos PostgreSQL.
    """
    load_dotenv()

    db_config = {
        "dbname": os.getenv("DB_NAME"),
        "user": os.getenv("DB_USER"),
        "password": os.getenv("DB_PASSWORD"),
        "host": os.getenv("DB_HOST", "localhost"),
        "port": os.getenv("DB_PORT", "5432")
    }

    if not all(db_config.values()):
        print("Error: Faltan variables de entorno para la base de datos en el archivo .env.")
        return

    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: No se encontró el archivo de entrada {json_file_path}")
        return

    conn = None
    try:
        with psycopg2.connect(**db_config) as conn:
            with conn.cursor() as cur:
                print("Conexión a la base de datos establecida exitosamente.")
                print("Limpiando tablas antiguas...")
                cur.execute("TRUNCATE TABLE versiones, modelos, marcas RESTART IDENTITY CASCADE;")

                for vehiculo in data:
                    modelo_base = vehiculo.get('modelo_base', '').strip()
                    if not modelo_base:
                        continue

                    # ====================================================================
                    # ========= INICIO DE LA LÓGICA CORREGIDA PARA MARCA Y MODELO ========
                    # ====================================================================

                    parts = modelo_base.split(' ')

                    # Si el string no tiene al menos 3 partes (año, marca, modelo), es inválido.
                    if len(parts) < 3:
                        print(f"  -> Adv: Registro omitido por formato de 'modelo_base' inesperado: '{modelo_base}'")
                        continue

                    # Manejo de casos especiales como "Great Wall"
                    if parts[1].lower() == "great" and parts[2].lower() == "wall":
                        marca_nombre = "Great Wall"
                        modelo_nombre = ' '.join(parts[3:])
                    else:
                        # Caso estándar: El año es la primera parte, la marca es la segunda.
                        marca_nombre = parts[1]
                        modelo_nombre = ' '.join(parts[2:])

                    # ====================================================================
                    # ========= FIN DE LA LÓGICA CORREGIDA ===============================
                    # ====================================================================

                    # --- A. Insertar la MARCA y obtener su ID ---
                    cur.execute(
                        """
                        WITH ins AS (
                            INSERT INTO marcas (nombre) VALUES (%s)
                            ON CONFLICT (nombre) DO NOTHING
                            RETURNING id
                        )
                        SELECT id FROM ins
                        UNION ALL
                        SELECT id FROM marcas WHERE nombre = %s;
                        """,
                        (marca_nombre, marca_nombre)
                    )
                    marca_id = cur.fetchone()[0]

                    # --- B. Insertar el MODELO y obtener su ID ---
                    cur.execute(
                        """
                        WITH ins AS (
                            INSERT INTO modelos (marca_id, nombre) VALUES (%s, %s)
                            ON CONFLICT (marca_id, nombre) DO NOTHING
                            RETURNING id
                        )
                        SELECT id FROM ins
                        UNION ALL
                        SELECT id FROM modelos WHERE marca_id = %s AND nombre = %s;
                        """,
                        (marca_id, modelo_nombre, marca_id, modelo_nombre)
                    )
                    modelo_id = cur.fetchone()[0]

                    # --- C. Insertar la VERSIÓN con sus especificaciones ---
                    specs = vehiculo.get('especificaciones_clave', {})
                    cur.execute(
                        """
                        INSERT INTO versiones (
                            modelo_id, nombre, consumo_mixto_kml, consumo_urbano_kml,
                            consumo_extraurbano_kml, capacidad_estanque_litros, motor_litros,
                            transmision, traccion
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (modelo_id, nombre) DO NOTHING;
                        """,
                        (
                            modelo_id, vehiculo.get('version'),
                            specs.get('consumo_mixto_kml'), specs.get('consumo_urbano_kml'),
                            specs.get('consumo_extraurbano_kml'), specs.get('capacidad_estanque_litros'),
                            specs.get('motor_litros'), specs.get('transmision'), specs.get('traccion')
                        )
                    )

                print(f"¡Carga completada! Se procesaron {len(data)} registros de vehículos.")

    except psycopg2.Error as e:
        print(f"Error de base de datos: {e}")
    except Exception as e:
        print(f"Ocurrió un error inesperado: {e}")
    finally:
        if conn:
            conn.close()
            print("Conexión a la base de datos cerrada.")

if __name__ == "__main__":
    SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
    json_input_file = os.path.join(SCRIPT_DIR, 'metadata_vehiculos.json')
    load_data_to_db(json_input_file)