import subprocess
import os
import psycopg2
from dotenv import load_dotenv


class InfraestructuraLoader:
    def __init__(self):
        self.script_dir = os.path.dirname(os.path.realpath(__file__))
        self.pbf_file = os.path.join(self.script_dir, "chile-latest.osm.pbf")

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

    def run_osm2pgsql(self):
        print("-> [Paso 1/2] Ejecutando osm2pgsql para importar la infraestructura vial...")
        print("   (Este proceso puede tardar varios minutos)...")

        env = os.environ.copy()
        env['PGPASSWORD'] = self.db_config['password']

        command = [
            "osm2pgsql", "-d", self.db_config['dbname'], "-U", self.db_config['user'],
            "-H", self.db_config['host'], "--create", "--slim", "-C", "2048", "--hstore",
            "--style", "/usr/share/osm2pgsql/default.style", self.pbf_file
        ]

        try:
            subprocess.run(command, check=True, text=True, capture_output=True, env=env)
            print("   -> ¡osm2pgsql completado exitosamente!")
            return True
        except FileNotFoundError:
            print("   -> ERROR: El comando 'osm2pgsql' no fue encontrado.")
            return False
        except subprocess.CalledProcessError as e:
            print("   -> ERROR durante la ejecución de osm2pgsql:");
            print(e.stderr)
            return False

    def create_pgrouting_topology(self):
        print("-> [Paso 2/2] Creando la topología para pgRouting...")
        sql = """
              ALTER TABLE planet_osm_line \
                  ADD COLUMN IF NOT EXISTS "source" INTEGER;
              ALTER TABLE planet_osm_line \
                  ADD COLUMN IF NOT EXISTS "target" INTEGER;
              ALTER TABLE planet_osm_line \
                  ADD COLUMN IF NOT EXISTS "cost" DOUBLE PRECISION;
              ALTER TABLE planet_osm_line \
                  ADD COLUMN IF NOT EXISTS "reverse_cost" DOUBLE PRECISION;
              UPDATE planet_osm_line \
              SET cost = ST_Length(ST_Transform(way, 4326)::geography);
              UPDATE planet_osm_line \
              SET reverse_cost = cost;
              UPDATE planet_osm_line \
              SET reverse_cost = -1 \
              WHERE oneway = 'yes';
              SELECT pgr_createTopology('planet_osm_line', 0.00001, 'way', 'osm_id');
              CREATE INDEX IF NOT EXISTS source_idx ON planet_osm_line("source");
              CREATE INDEX IF NOT EXISTS target_idx ON planet_osm_line("target");
              CREATE INDEX IF NOT EXISTS way_idx ON planet_osm_line USING GIST (way); \
              """
        try:
            with psycopg2.connect(**self.db_config) as conn:
                conn.autocommit = True
                with conn.cursor() as cur:
                    cur.execute(sql)
            print("   -> ¡Topología de ruteo creada exitosamente!")
            return True
        except psycopg2.Error as e:
            print(f"   -> ERROR de base de datos al crear la topología: {e}")
            return False

    def ejecutar(self):
        if not os.path.exists(self.pbf_file):
            print(f"ERROR: El archivo '{self.pbf_file}' no existe. Ejecuta 'extract_infraestructura.py' primero.")
            return
        if self.run_osm2pgsql():
            self.create_pgrouting_topology()


if __name__ == "__main__":
    loader = InfraestructuraLoader()
    loader.ejecutar()