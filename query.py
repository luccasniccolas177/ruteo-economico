import psycopg2, json

conn = psycopg2.connect("dbname=chile_routing_economico user=postgres password=Monita315@")
cur = conn.cursor()

# 🔧 Desactiva JIT temporalmente para esta sesión
cur.execute("SET jit = off;")

# Ahora ejecuta tu query completa
with open("query_valparaiso.sql") as f:
    sql = f.read()
cur.execute(sql)

data = cur.fetchone()[0]
with open("ruta_valparaiso.json", "w") as f:
    json.dump(data, f, indent=2)

print("✅ Ruta exportada a ruta_valparaiso.json")
