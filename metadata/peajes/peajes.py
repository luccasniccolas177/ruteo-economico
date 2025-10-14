import json
import pandas as pd

# 1️⃣ Cargar tus archivos
with open("precios.json", "r", encoding="utf-8") as f:
    precios_data = json.load(f)

with open("georef.json", "r", encoding="utf-8") as f:
    georef_data = json.load(f)

# 2️⃣ Convertir a DataFrames
# --- Precios ---
precios_rows = []
for autopista in precios_data["autopistas"]:
    for eje in autopista["ejes"]:
        for direccion in eje["direcciones"]:
            for portico in direccion["porticos"]:
                precios_rows.append({
                    "nombre_autopista": autopista["nombre_autopista"],
                    "portico_id": portico["portico_id"],
                    "nombre_portico": portico["nombre_portico"],
                    "referencia_tramo": portico["referencia_tramo"]
                })
df_precios = pd.DataFrame(precios_rows)

# --- Georreferencias ---
df_geo = pd.DataFrame(georef_data["peajes"])

# 3️⃣ Normalizar nombres para poder unirlos
# (puedes ajustar esta parte si los nombres difieren en mayúsculas o tildes)
df_precios["nombre_portico_norm"] = df_precios["nombre_portico"].str.lower().str.strip()
df_geo["nombre_norm"] = df_geo["nombre"].str.lower().str.strip()

# 4️⃣ Unir por nombre (o id si tienes un campo en común)
df_final = pd.merge(df_precios, df_geo,
                    left_on="nombre_portico_norm",
                    right_on="nombre_norm",
                    how="left")

# 5️⃣ Guardar el resultado
df_final.to_csv("peajes_completos.csv", index=False, encoding="utf-8-sig")

print("✅ Archivo combinado guardado como peajes_completos.csv")
print(f"Total registros combinados: {len(df_final)}")
print(f"Con coordenadas faltantes: {df_final['latitude'].isna().sum()}")
