import requests
import json
import os

# URL base del servicio ArcGIS
url = "https://rest-sit.mop.gob.cl/arcgis/rest/services/VIALIDAD/Infraestructura_Vial/MapServer/1/query"

# Parámetros: pedimos todo en una sola consulta
params = {
    "where": "1=1",          # condición: todos los registros
    "outFields": "*",        # todos los campos
    "f": "json",             # formato de salida
    "returnGeometry": "true" # incluir coordenadas
}

print("Consultando datos de peajes...")
response = requests.get(url, params=params)
data = response.json()

features = data.get("features", [])

# Extraer atributos + geometría
rows = []
for f in features:
    attrs = f.get("attributes", {})
    geom = f.get("geometry", {})
    attrs["latitude"] = geom.get("y")
    attrs["longitude"] = geom.get("x")
    rows.append(attrs)

# Guardar en JSON
output_file = os.path.join(os.path.dirname(__file__), "peajes_mop.json")
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(rows, f, indent=2, ensure_ascii=False)

print(f"✅ Datos guardados en {output_file}")
print(f"Total registros: {len(rows)}")