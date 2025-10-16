import requests
import os
from datetime import datetime


class ExtractorInfraestructura:
    """
    Descarga el archivo de datos de OpenStreetMap para Chile desde Geofabrik.
    """

    # URL directa al archivo .osm.pbf de Chile
    PBF_URL = "https://download.geofabrik.de/south-america/chile-latest.osm.pbf"

    def __init__(self):
        self.output_dir = os.path.dirname(os.path.realpath(__file__))
        self.output_filename = "chile-latest.osm.pbf"
        self.filepath = os.path.join(self.output_dir, self.output_filename)
        self.headers = {'User-Agent': 'ProyectoRuteoEconomico-ETL/1.0'}

    def descargar(self):
        """
        Descarga el archivo PBF, mostrando el progreso.
        """
        print(f"-> Iniciando descarga de infraestructura desde Geofabrik...")
        print(f"   URL: {self.PBF_URL}")
        try:
            with requests.get(self.PBF_URL, headers=self.headers, stream=True, timeout=30) as r:
                r.raise_for_status()
                total_size = int(r.headers.get('content-length', 0))

                with open(self.filepath, 'wb') as f:
                    downloaded_size = 0
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        # Imprimir progreso
                        done = int(50 * downloaded_size / total_size)
                        print(
                            f"\r   [{'=' * done}{' ' * (50 - done)}] {downloaded_size / 1024 / 1024:.2f} MB / {total_size / 1024 / 1024:.2f} MB",
                            end='')

            print(f"\n\n-> Descarga completada. Archivo guardado en: {self.filepath}")
            return self.filepath

        except requests.RequestException as e:
            print(f"\n-> ERROR: No se pudo descargar el archivo. {e}")
            return None


if __name__ == "__main__":
    extractor = ExtractorInfraestructura()
    extractor.descargar()