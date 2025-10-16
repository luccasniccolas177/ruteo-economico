import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime
from urllib.parse import urljoin
import time


class SismosWebScraperETL:
    """
    Automatiza la extracción de datos de sismos mediante web scraping
    desde sismologia.cl y los transforma a un archivo GeoJSON estandarizado.
    """

    BASE_URL = "https://www.sismologia.cl/"
    MIN_MAGNITUDE = 3.5  # Filtro para sismos relevantes

    def __init__(self):
        self.output_dir = os.path.dirname(os.path.realpath(__file__))
        self.headers = {'User-Agent': 'ProyectoRuteoEconomico-Scraper/1.0'}

    def _scrape_main_page(self):
        """Extrae la lista inicial de sismos desde la tabla principal."""
        print("-> 1. Extrayendo tabla de sismos desde la página principal...")
        try:
            response = requests.get(self.BASE_URL, headers=self.headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')
            table = soup.find('table', class_='sismologia')
            if not table:
                print("   -> ERROR: No se encontró la tabla de sismos en la página principal.")
                return []

            sismos = []

            # --- CORRECCIÓN APLICADA AQUÍ ---
            # Buscamos todos los 'tr' directamente en la tabla y saltamos el primero (header)
            rows = table.find_all('tr')[1:]

            for row in rows:
                cols = row.find_all('td')
                if len(cols) == 3:
                    magnitud = float(cols[2].text.strip())

                    if magnitud < self.MIN_MAGNITUDE:
                        continue

                    link_tag = cols[0].find('a')
                    full_text = cols[0].get_text(separator='\n', strip=True).split('\n')

                    sismo_info = {
                        'fecha_local': full_text[0],
                        'referencia_geografica': full_text[1],
                        'profundidad_km_str': cols[1].text.strip(),
                        'magnitud': magnitud,
                        'detalle_url': urljoin(self.BASE_URL, link_tag['href']) if link_tag else None
                    }
                    sismos.append(sismo_info)

            print(f"   -> Se encontraron {len(sismos)} sismos con magnitud >= {self.MIN_MAGNITUDE}.")
            return sismos

        except requests.RequestException as e:
            print(f"   -> ERROR de red al consultar la página principal: {e}")
            return []

    def _scrape_detail_page(self, url):
        """Extrae las coordenadas de la página de detalle de un sismo."""
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            table = soup.find('table', class_='sismologia informe')
            if not table: return None

            coords = {}
            rows = table.find_all('tr')
            for row in rows:
                cols = row.find_all('td')
                if len(cols) == 2:
                    key = cols[0].text.strip().lower()
                    value = cols[1].text.strip()
                    if 'latitud' in key:
                        coords['latitud'] = float(value)
                    elif 'longitud' in key:
                        coords['longitud'] = float(value)
            return coords
        except (requests.RequestException, ValueError) as e:
            print(f"   -> Advertencia: No se pudo procesar la página de detalle {url}. Error: {e}")
            return None

    def ejecutar(self):
        """Orquesta el proceso completo de Extracción y Transformación."""
        print("\n--- Iniciando Proceso ETL (Web Scraping) para Amenaza de Sismos ---")
        sismos_base = self._scrape_main_page()
        if not sismos_base:
            print("--- Proceso Finalizado: No se extrajeron datos. ---")
            return

        print("-> 2. Enriqueciendo datos con coordenadas de páginas de detalle...")
        features = []
        for i, sismo in enumerate(sismos_base):
            if not sismo['detalle_url']: continue

            print(f"   -> Procesando sismo {i + 1}/{len(sismos_base)}...", end='\r')
            coords = self._scrape_detail_page(sismo['detalle_url'])

            if coords and 'latitud' in coords and 'longitud' in coords:
                feature = {
                    "type": "Feature",
                    "properties": {
                        "tipo_amenaza": "sismo",
                        "fuente": "CSN",
                        "fecha_local": sismo['fecha_local'],
                        "magnitud": sismo['magnitud'],
                        "profundidad_km": float(sismo['profundidad_km_str'].replace('km', '').strip()),
                        "referencia_geografica": sismo['referencia_geografica'],
                        "url_detalle": sismo['detalle_url'],
                        "nivel_alerta": "amarillo" if sismo['magnitud'] >= 5.0 else "verde"
                    },
                    "geometry": {
                        "type": "Point",
                        "coordinates": [coords['longitud'], coords['latitud']]
                    }
                }
                features.append(feature)

            time.sleep(0.5)

        print("\n   -> Transformación completada.")

        feature_collection = {
            "type": "FeatureCollection",
            "metadata": {"generado": datetime.now().isoformat()},
            "features": features
        }

        output_path = os.path.join(self.output_dir, "amenaza_sismos.geojson")
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(feature_collection, f, indent=2, ensure_ascii=False)
            print(f"-> 3. Archivo 'amenaza_sismos.geojson' guardado con {len(features)} sismos.")
        except IOError as e:
            print(f"   -> ERROR al guardar el archivo: {e}")

        print("--- Proceso Finalizado ---\n")


if __name__ == "__main__":
    etl = SismosWebScraperETL()
    etl.ejecutar()