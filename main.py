import subprocess
import sys
import os

ETL_PIPELINE = [
    # --- INFRAESTRUCTURA ---
    ("infraestructura/extract_infraestructura.py", "Descargando mapa de Chile desde Geofabrik"),
    ("infraestructura/transform_load_infraestructura.py", "Procesando y cargando infraestructura a la BD"),
    # --- METADATA ---
    ("metadata/vehiculos/scraper-chileautos.py", "Extrayendo datos de vehículos (Scraping)"),
    ("metadata/vehiculos/transform_vehiculos.py", "Transformando datos de vehículos"),
    ("metadata/vehiculos/load_vehiculos.py", "Cargando vehículos a la BD"),
    ("metadata/combustible/extract_combustibles.py", "Extrayendo datos crudos de combustibles"),
    ("metadata/combustible/transform_combustibles.py", "Transformando datos de combustibles"),
    ("metadata/combustible/load_combustibles.py", "Cargando combustibles a la BD"),
    ("metadata/peajes/transform_peajes.py", "Transformando y mapeando datos de peajes"),
    ("metadata/peajes/load_peajes.py", "Cargando peajes a la BD"),
    # --- AMENAZAS ---
    ("amenazas/congestion/extract_congestion.py", "Extrayendo datos de congestión"),
    ("amenazas/congestion/transform_congestion.py", "Transformando datos de congestión"),
    ("amenazas/sismos/extract_transform_sismos.py", "Extrayendo y transformando datos de sismos"),
    ("amenazas/inundaciones/extract_transform_inundaciones.py", "Extrayendo y transformando datos de inundaciones"),
    ("amenazas/incendios/extract_transform_incendios.py", "Extrayendo y transformando datos de incendios"),
]

def run_script(script_path, description):
    print("-" * 70); print(f"▶️  EJECUTANDO: {description}"); print("-" * 70)
    if not os.path.exists(script_path):
        print(f"❌ ERROR: El script '{script_path}' no fue encontrado.")
        return False
    try:
        result = subprocess.run([sys.executable, script_path], check=True, capture_output=True, text=True)
        print("   ✅ Tarea completada con éxito.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ ERROR al ejecutar '{script_path}':\n{e.stderr}")
        return False

if __name__ == "__main__":
    print("🚀 INICIANDO PIPELINE DE EXTRACCIÓN Y CARGA DE DATOS 🚀")
    for path, desc in ETL_PIPELINE:
        if not run_script(path, desc):
            print("\n🛑 El pipeline se detuvo debido a un error.")
            sys.exit(1)
    print("\n🎉 ¡TODOS LOS PROCESOS ETL SE COMPLETARON EXITOSAMENTE! 🎉")