import json

# Archivo de entrada (tu JSON original)
with open("ruta_valparaiso.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# Extrae secciones si existen
ruta = data.get("ruta", [])
peajes = data.get("peajes", [])

# Exporta la ruta (líneas)
if ruta:
    ruta_geojson = {
        "type": "FeatureCollection",
        "features": ruta
    }
    with open("ruta.geojson", "w", encoding="utf-8") as f:
        json.dump(ruta_geojson, f, indent=2, ensure_ascii=False)
    print("✅ Archivo 'ruta.geojson' creado correctamente.")

# Exporta los peajes (puntos)
if peajes:
    peajes_geojson = {
        "type": "FeatureCollection",
        "features": peajes
    }
    with open("peajes.geojson", "w", encoding="utf-8") as f:
        json.dump(peajes_geojson, f, indent=2, ensure_ascii=False)
    print("✅ Archivo 'peajes.geojson' creado correctamente.")

print("\n👉 Ahora abre los archivos 'ruta.geojson' y 'peajes.geojson' en QGIS.")
