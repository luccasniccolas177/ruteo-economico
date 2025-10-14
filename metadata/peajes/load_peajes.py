import json
import os
import psycopg2
from dotenv import load_dotenv


class CargadorPeajes:
    """
    Carga los datos transformados de peajes desde el JSON limpio
    a las tablas 'peajes' y 'tarifas_peaje' en PostgreSQL.
    """

    def __init__(self):
        self.script_dir = os.path.dirname(os.path.realpath(__file__))
        load_dotenv()

        self.db_config = {
            "dbname": os.getenv("DB_NAME"),
            "user": os.getenv("DB_USER"),
            "password": os.getenv("DB_PASSWORD"),
            "host": os.getenv("DB_HOST", "localhost"),
            "port": os.getenv("DB_PORT", "5432")
        }
        if not all(self.db_config.values()):
            raise ValueError("Faltan variables de BD en el archivo .env.")

    def ejecutar_carga(self):
        print("--- Iniciando Proceso de Carga de Datos de Peajes ---")

        json_path = os.path.join(self.script_dir, 'transformed_peajes.json')
        if not os.path.exists(json_path):
            print(
                f"Error: No se encontró el archivo 'transformed_peajes.json'. Ejecuta el script de transformación primero.")
            return

        print(f"Cargando datos desde: {os.path.basename(json_path)}")

        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error al leer el archivo JSON: {e}")
            return

        try:
            with psycopg2.connect(**self.db_config) as conn:
                with conn.cursor() as cur:
                    print("Conexión a la base de datos establecida exitosamente.")

                    print("Vaciando tablas de peajes existentes...")
                    cur.execute("TRUNCATE TABLE tarifas_peaje, peajes RESTART IDENTITY CASCADE;")

                    peajes_insertados = 0
                    tarifas_insertadas = 0

                    for peaje in data:
                        # Insertar en la tabla 'peajes'
                        cur.execute(
                            """
                            INSERT INTO peajes (nombre, concesionaria, tipo, ubicacion)
                            VALUES (%s, %s, %s, ST_SetSRID(ST_MakePoint(%s, %s), 4326)) RETURNING id;
                            """,
                            (
                                peaje.get('nombre'), peaje.get('concesionaria'), peaje.get('tipo'),
                                peaje.get('longitud'), peaje.get('latitud')
                            )
                        )
                        peaje_id_db = cur.fetchone()[0]
                        peajes_insertados += 1

                        # Insertar tarifas asociadas
                        for tarifa in peaje.get('tarifas', []):
                            cur.execute(
                                """
                                INSERT INTO tarifas_peaje (peaje_id, categoria_vehiculo, tipo_tarifa, precio)
                                VALUES (%s, %s, %s, %s);
                                """,
                                (
                                    peaje_id_db,
                                    tarifa.get('categoria_vehiculo'),
                                    tarifa.get('tipo_tarifa'),
                                    tarifa.get('precio')
                                )
                            )
                            tarifas_insertadas += 1

                    print(f"\n¡Carga completada!")
                    print(f"  -> Se insertaron {peajes_insertados} peajes.")
                    print(f"  -> Se insertaron {tarifas_insertadas} tarifas.")

        except psycopg2.Error as e:
            print(f"\nError de base de datos durante la carga: {e}")
            if conn: conn.rollback()
        except Exception as e:
            print(f"\nOcurrió un error inesperado: {e}")


if __name__ == "__main__":
    cargador = CargadorPeajes()
    cargador.ejecutar_carga()