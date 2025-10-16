import googlemaps

# Tu API Key
API_KEY = "AIzaSyDGZkrGCQT3rtvAEqX-lVl8exmNt881af4"

# Crear cliente de Google Maps
gmaps = googlemaps.Client(key=API_KEY)

# Origen y destino
origen = "Santiago, Chile"
destino = "Coquimbo, Chile"

# Llamada a la Directions API
ruta = gmaps.directions(
    origin=origen,
    destination=destino,
    mode="driving",
    alternatives=False
)

# Verificar si se obtuvo una ruta
if not ruta:
    print("No se encontró ninguna ruta.")
else:
    route_info = ruta[0]
    summary = route_info.get("summary", "Sin nombre")
    warnings = route_info.get("warnings", [])

    print(f"Ruta: {summary}")
    print("Advertencias:")
    if warnings:
        for w in warnings:
            print(f" - {w}")
    else:
        print(" - No hay advertencias relevantes.")

    # Buscar si menciona peajes
    contiene_peajes = any("peaje" in w.lower() or "toll" in w.lower() for w in warnings)

    if contiene_peajes:
        print("\n⚠️ La ruta incluye peajes o TAG.")
    else:
        print("\n✅ La ruta NO incluye peajes.")
