import geopandas as gpd
import matplotlib.pyplot as plt

# Cargar los GeoJSON
ruta = gpd.read_file("ruta.geojson")
peajes = gpd.read_file("peajes.geojson")

# Graficar
base = ruta.plot(color='blue', linewidth=2, figsize=(10, 8))
peajes.plot(ax=base, color='red', markersize=50)

plt.title("Ruta y Peajes detectados")
plt.xlabel("Longitud")
plt.ylabel("Latitud")
plt.show()
