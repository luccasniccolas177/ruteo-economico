import json
import os
import psycopg2
from dotenv import load_dotenv


class CargadorPeajes:
    """
    Carga la metadata de peajes desde un archivo JSON enriquecido
    a las tablas 'peajes' y 'tarifas_peaje' en PostgreSQL.
    También vincula cada peaje a su nodo más cercano en la red vial (nearest_node_id).
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

    def ejecutar_carga(self):
        print("🚧 Iniciando carga de peajes...")

        json_path = os.path.join(self.script_dir, "peajes_enriquecidos.json")
        if not os.path.exists(json_path):
            print(f"❌ No se encontró el archivo: {json_path}")
            return

        with open(json_path, "r", encoding="utf-8") as f:
            peajes_data = json.load(f)

        conn = None
        try:
            with psycopg2.connect(**self.db_config) as conn:
                with conn.cursor() as cur:
                    print("✅ Conexión establecida con la base de datos.")
                    cur.execute("TRUNCATE TABLE tarifas_peaje, peajes RESTART IDENTITY CASCADE;")

                    sql_peaje = """
                        INSERT INTO peajes (objectid, globalid, nombre, tipo, concesionaria, tramo,
                                            latitud, longitud, geom)
                        VALUES (%s, %s, %s, %s, %s, %s,
                                %s, %s, ST_SetSRID(ST_MakePoint(%s, %s), 4326))
                        RETURNING id;
                    """

                    sql_tarifa = """
                        INSERT INTO tarifas_peaje (peaje_id, categoria_vehiculo, tipo_tarifa, precio)
                        VALUES (%s, %s, %s, %s);
                    """

                    peajes_count, tarifas_count = 0, 0
                    for p in peajes_data:
                        cur.execute(sql_peaje, (
                            p.get("OBJECTID"),
                            p.get("globalid", "").strip("{}"),
                            p.get("nombre"),
                            p.get("tipo"),
                            p.get("concesionaria"),
                            p.get("tramo"),
                            p.get("latitud"),
                            p.get("longitud"),
                            p.get("longitud"),
                            p.get("latitud")
                        ))
                        peaje_id = cur.fetchone()[0]
                        peajes_count += 1

                        for tarifa in p.get("tarifas", []):
                            cur.execute(sql_tarifa, (
                                peaje_id,
                                tarifa.get("categoria_vehiculo"),
                                tarifa.get("tipo_tarifa"),
                                tarifa.get("precio")
                            ))
                            tarifas_count += 1

                    print(f"✅ Insertados {peajes_count} peajes y {tarifas_count} tarifas.")

                    # --- Asociar peajes al grafo vial ---
                    print("🔄 Calculando nearest_node_id para cada peaje...")
                    cur.execute("""
                        UPDATE peajes AS p
                        SET nearest_node_id = nn.node
                        FROM (
                            SELECT p2.id,
                                   (
                                       SELECT source
                                       FROM chile_2po_4pgr
                                       ORDER BY geom_way <-> p2.geom
                                       LIMIT 1
                                   ) AS node
                            FROM peajes AS p2
                        ) AS nn
                        WHERE nn.id = p.id;
                    """)
                    conn.commit()
                    print("✅ Nodos cercanos actualizados correctamente.")

        except Exception as e:
            print(f"❌ Error durante la carga: {e}")
            if conn:
                conn.rollback()
        finally:
            if conn:
                conn.close()
                print("🔌 Conexión cerrada.")


if __name__ == "__main__":
    CargadorPeajes().ejecutar_carga()
