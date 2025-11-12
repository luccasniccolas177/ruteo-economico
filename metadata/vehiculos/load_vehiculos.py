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

    if not all(val for val in db_config.values() if val is not None):
        print("Error: Faltan variables de entorno para la base de datos en el archivo .env.")
        print("Asegúrate de tener DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT.")
        return

    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: No se encontró el archivo de entrada {json_file_path}")
        return
    except json.JSONDecodeError:
        print(f"Error: El archivo {json_file_path} no es un JSON válido.")
        return

    conn = None
    try:
        with psycopg2.connect(**db_config) as conn:
            with conn.cursor() as cur:
                print("Conexión a la base de datos establecida exitosamente.")
                print("Limpiando tablas antiguas (marcas, modelos, versiones)...")
                cur.execute("TRUNCATE TABLE versiones, modelos, marcas RESTART IDENTITY CASCADE;")

                marcas_cache = {}
                modelos_cache = {}
                versiones_insertadas = 0

                for vehiculo in data:
                    modelo_base = vehiculo.get('modelo_base', '').strip()
                    if not modelo_base:
                        continue

                    # ====================================================================
                    # ========= LÓGICA PARA MARCA Y MODELO (de tu script) ========
                    # ====================================================================

                    parts = modelo_base.split(' ')

                    if len(parts) < 3:
                        print(f"  -> Adv: Registro omitido por formato de 'modelo_base' inesperado: '{modelo_base}'")
                        continue

                    # Manejo de casos especiales como "Great Wall"
                    if parts[1].lower() == "great" and len(parts) > 2 and parts[2].lower() == "wall":
                        marca_nombre = "Great Wall"
                        modelo_nombre = ' '.join(parts[3:])
                    else:
                        # Caso estándar: El año es la primera parte, la marca es la segunda.
                        marca_nombre = parts[1]
                        modelo_nombre = ' '.join(parts[2:])

                    if not modelo_nombre:
                        print(f"  -> Adv: No se pudo determinar el nombre del modelo para: '{modelo_base}'")
                        continue

                    # ====================================================================
                    # ========= FIN DE LA LÓGICA (de tu script) ===========================
                    # ====================================================================

                    # --- A. Insertar la MARCA y obtener su ID ---
                    if marca_nombre not in marcas_cache:
                        cur.execute(
                            """
                            WITH ins AS (
                            INSERT
                            INTO marcas (nombre)
                            VALUES (%s)
                            ON CONFLICT (nombre) DO NOTHING
                                RETURNING id
                                )
                            SELECT id
                            FROM ins
                            UNION ALL
                            SELECT id
                            FROM marcas
                            WHERE nombre = %s;
                            """,
                            (marca_nombre, marca_nombre)
                        )
                        marcas_cache[marca_nombre] = cur.fetchone()[0]
                    marca_id = marcas_cache[marca_nombre]

                    # --- B. Insertar el MODELO y obtener su ID ---
                    modelo_key = (marca_id, modelo_nombre)
                    if modelo_key not in modelos_cache:
                        cur.execute(
                            """
                            WITH ins AS (
                            INSERT
                            INTO modelos (marca_id, nombre)
                            VALUES (%s, %s)
                            ON CONFLICT (marca_id, nombre) DO NOTHING
                                RETURNING id
                                )
                            SELECT id
                            FROM ins
                            UNION ALL
                            SELECT id
                            FROM modelos
                            WHERE marca_id = %s
                              AND nombre = %s;
                            """,
                            (marca_id, modelo_nombre, marca_id, modelo_nombre)
                        )
                        modelos_cache[modelo_key] = cur.fetchone()[0]
                    modelo_id = modelos_cache[modelo_key]

                    # --- C. Insertar la VERSIÓN con sus especificaciones ---
                    specs = vehiculo.get('especificaciones_clave', {})
                    cur.execute(
                        """
                        INSERT INTO versiones (modelo_id, nombre, consumo_mixto_kml, consumo_urbano_kml,
                                               consumo_extraurbano_kml, capacidad_estanque_litros, motor_litros,
                                               transmision, traccion)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT (modelo_id, nombre) DO NOTHING;
                        """,
                        (
                            modelo_id, vehiculo.get('version'),
                            specs.get('consumo_mixto_kml'), specs.get('consumo_urbano_kml'),
                            specs.get('consumo_extraurbano_kml'), specs.get('capacidad_estanque_litros'),
                            specs.get('motor_litros'), specs.get('transmision'), specs.get('traccion')
                        )
                    )
                    versiones_insertadas += 1

                print(f"¡Carga completada! Se procesaron {len(data)} registros de vehículos.")
                print(f"Total de marcas únicas: {len(marcas_cache)}")
                print(f"Total de modelos únicos: {len(modelos_cache)}")
                print(f"Total de versiones insertadas: {versiones_insertadas}")

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
    # Asegúrate de que tu archivo JSON se llame así y esté en la misma carpeta
    json_input_file = os.path.join(SCRIPT_DIR, 'metadata_vehiculos.json')

    if not os.path.exists(json_input_file):
        print(f"Error: El archivo '{json_input_file}' no se encuentra.")
    else:
        load_data_to_db(json_input_file)
