import json
import os
import glob
import psycopg2
from dotenv import load_dotenv


class CargadorCombustible:
    """
    Carga los datos transformados de combustibles desde un archivo JSON
    a las tablas 'estaciones_servicio' y 'precios_combustibles' en PostgreSQL.
    """

    def __init__(self):
        self.script_dir = os.path.dirname(os.path.realpath(__file__))
        load_dotenv()

        # Cargar configuración de la base de datos desde .env
        self.db_config = {
            "dbname": os.getenv("DB_NAME"),
            "user": os.getenv("DB_USER"),
            "password": os.getenv("DB_PASSWORD"),
            "host": os.getenv("DB_HOST", "localhost"),
            "port": os.getenv("DB_PORT", "5432")
        }
        if not all(self.db_config.values()):
            raise ValueError("Faltan variables de BD en el archivo .env. Asegúrate de tener DB_NAME, DB_USER, etc.")

    def encontrar_ultimo_json_transformado(self):
        """
        Encuentra el archivo transformed_combustibles_*.json más reciente.
        """
        try:
            lista_de_archivos = glob.glob(os.path.join(self.script_dir, 'transformed_combustibles_*.json'))
            if not lista_de_archivos:
                return None
            return max(lista_de_archivos, key=os.path.getctime)
        except Exception as e:
            print(f"Error al buscar el archivo JSON transformado: {e}")
            return None

    def ejecutar_carga(self):
        """
        Orquesta el proceso completo de carga a la base de datos.
        """
        print("--- Iniciando Proceso de Carga de Datos de Combustibles ---")

        json_path = self.encontrar_ultimo_json_transformado()
        if not json_path:
            print(f"Error: No se encontró ningún archivo 'transformed_combustibles_*.json' en '{self.script_dir}'.")
            return

        print(f"Cargando datos desde: {os.path.basename(json_path)}")

        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error al leer el archivo JSON: {e}")
            return

        conn = None
        try:
            # Establecer conexión
            with psycopg2.connect(**self.db_config) as conn:
                with conn.cursor() as cur:
                    print("Conexión a la base de datos establecida exitosamente.")

                    # Limpiar tablas antes de la inserción
                    print("Vaciando tablas de combustibles existentes...")
                    cur.execute("TRUNCATE TABLE precios_combustibles, estaciones_servicio RESTART IDENTITY CASCADE;")

                    estaciones_insertadas = 0
                    precios_insertados = 0

                    # Iterar sobre las estaciones del JSON
                    for estacion in data.get('estaciones', []):
                        # Insertar en la tabla 'estaciones_servicio'
                        cur.execute(
                            """
                            INSERT INTO estaciones_servicio (id_estacion_cne, nombre, marca, direccion,
                                                             comuna, region, horario, ubicacion)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, ST_SetSRID(ST_MakePoint(%s, %s), 4326)) RETURNING id;
                            """,
                            (
                                estacion.get('id_estacion_cne'), estacion.get('nombre'), estacion.get('marca'),
                                estacion.get('direccion'), estacion.get('comuna'), estacion.get('region'),
                                estacion.get('horario'), estacion.get('longitud'), estacion.get('latitud')
                            )
                        )
                        # Recuperar el ID de la estación recién insertada
                        estacion_id_db = cur.fetchone()[0]
                        estaciones_insertadas += 1

                        # Iterar sobre los precios de esa estación
                        for precio_info in estacion.get('precios', []):
                            cur.execute(
                                """
                                INSERT INTO precios_combustibles (estacion_id, tipo_combustible, precio,
                                                                  fecha_actualizacion)
                                VALUES (%s, %s, %s, %s);
                                """,
                                (
                                    estacion_id_db,
                                    precio_info.get('tipo_combustible'),
                                    precio_info.get('precio'),
                                    precio_info.get('fecha_actualizacion')
                                )
                            )
                            precios_insertados += 1

                    print(f"\n¡Carga completada!")
                    print(f"  -> Se insertaron {estaciones_insertadas} estaciones.")
                    print(f"  -> Se insertaron {precios_insertados} precios.")

        except psycopg2.Error as e:
            print(f"\nError de base de datos durante la carga: {e}")
            if conn:
                conn.rollback()  # Revertir cambios si hay un error
        except Exception as e:
            print(f"\nOcurrió un error inesperado: {e}")
        finally:
            if conn:
                conn.close()
                print("Conexión a la base de datos cerrada.")


if __name__ == "__main__":
    cargador = CargadorCombustible()
    cargador.ejecutar_carga()