import json
import os
import glob
import psycopg2
from dotenv import load_dotenv


class CargadorCombustible:
    """
    Carga los datos transformados de combustibles desde un archivo JSON
    a la tabla 'bencineras' (estructura aplanada) en PostgreSQL.
    Ahora carga estaciones de TODO Chile.
    """

    def __init__(self):
        self.script_dir = os.path.dirname(os.path.realpath(__file__))
        load_dotenv()

        # Configuración BD
        self.db_config = {
            "dbname": os.getenv("DB_NAME"),
            "user": os.getenv("DB_USER"),
            "password": os.getenv("DB_PASSWORD"),
            "host": os.getenv("DB_HOST", "localhost"),
            "port": os.getenv("DB_PORT", "5432")
        }
        if not all(self.db_config.values()):
            raise ValueError("Faltan variables de BD en .env (DB_NAME, DB_USER, etc.)")

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

    def parsear_precios(self, lista_precios):
        """
        Toma la lista de precios anidada del JSON
        y la aplana en un diccionario simple.
        """
        precios = {}
        for item in lista_precios:
            if item.get('tipo_combustible') == 'gasolina_93':
                precios['gasolina_93'] = item.get('precio')
            elif item.get('tipo_combustible') == 'gasolina_95':
                precios['gasolina_95'] = item.get('precio')
            elif item.get('tipo_combustible') == 'gasolina_97':
                precios['gasolina_97'] = item.get('precio')
            elif item.get('tipo_combustible') == 'petroleo_diesel':
                precios['diesel'] = item.get('precio')
        return precios

    def ejecutar_carga(self):
        """
        Orquesta el proceso de carga a la base de datos
        de TODAS las estaciones del archivo JSON.
        """
        print("--- Iniciando Proceso de Carga de Datos de Combustibles (Nueva Estructura) ---")

        json_path = self.encontrar_ultimo_json_transformado()
        if not json_path:
            print("❌ No se encontró ningún archivo transformed_combustibles_*.json")
            return

        print(f"📄 Archivo detectado: {os.path.basename(json_path)}")

        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"❌ Error al leer el archivo JSON: {e}")
            return

        conn = None
        try:
            with psycopg2.connect(**self.db_config) as conn:
                with conn.cursor() as cur:
                    print("✅ Conexión establecida.")

                    print("🧹 Vaciando tabla 'bencineras'...")
                    cur.execute("TRUNCATE TABLE bencineras;")

                    estaciones_insertadas = 0

                    sql_insert = """
                                 INSERT INTO bencineras (id_estacion_cne, nombre, marca, direccion, comuna, region, \
                                                         precio_gasolina_93, precio_gasolina_95, precio_gasolina_97, \
                                                         precio_diesel, \
                                                         latitud, longitud, geom)
                                 VALUES (%s, %s, %s, %s, %s, %s, \
                                         %s, %s, %s, %s, \
                                         %s, %s, ST_SetSRID(ST_MakePoint(%s, %s), 4326)); \
                                 """

                    for estacion in data.get('estaciones', []):
                        region_estacion = estacion.get('region')
                        precios_aplanados = self.parsear_precios(estacion.get('precios', []))

                        datos_tupla = (
                            estacion.get('id_estacion_cne'),
                            estacion.get('nombre'),
                            estacion.get('marca'),
                            estacion.get('direccion'),
                            estacion.get('comuna'),
                            region_estacion,
                            precios_aplanados.get('gasolina_93'),
                            precios_aplanados.get('gasolina_95'),
                            precios_aplanados.get('gasolina_97'),
                            precios_aplanados.get('diesel'),
                            estacion.get('latitud'),
                            estacion.get('longitud'),
                            estacion.get('longitud'),
                            estacion.get('latitud')
                        )

                        cur.execute(sql_insert, datos_tupla)
                        estaciones_insertadas += 1

                    print(f"\n✅ ¡Carga finalizada!")
                    print(f"   → Se insertaron {estaciones_insertadas} estaciones.")

                    # 🧭 Vincular cada estación a su nodo más cercano del grafo
                    print("🔄 Calculando nearest_node_id para todas las estaciones (puede tardar un poco)...")

                    cur.execute("""
                                UPDATE bencineras AS b
                                SET nearest_node_id = nn.node
                                FROM (
                                    SELECT b2.id_estacion_cne,
                                           (
                                               SELECT source
                                               FROM chile_2po_4pgr
                                               ORDER BY geom_way <-> b2.geom
                                               LIMIT 1
                                           ) AS node
                                    FROM bencineras AS b2
                                ) AS nn
                                WHERE nn.id_estacion_cne = b.id_estacion_cne;
                                """)

                    conn.commit()  # 💾 Guardar cambios
                    print("✅ Nodos cercanos actualizados correctamente.")

        except psycopg2.Error as e:
            print(f"\n❌ Error de base de datos: {e}")
            if conn:
                conn.rollback()
        except Exception as e:
            print(f"\n❌ Error inesperado: {e}")
        finally:
            if conn:
                conn.close()
                print("🔌 Conexión cerrada.")


if __name__ == "__main__":
    cargador = CargadorCombustible()
    cargador.ejecutar_carga()
