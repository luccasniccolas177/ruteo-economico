import requests
import csv
import json
import os
from datetime import datetime, timezone


class IncendiosConafETL:
    """
    Automatiza la extracción de datos de incendios forestales desde el CSV
    público de CONAF en GitHub y los transforma a un archivo GeoJSON estandarizado,
    ordenado por fecha.
    """

    CSV_URL = "https://raw.githubusercontent.com/deigeprif/public/refs/heads/main/reporte/incendios.csv"

    def __init__(self):
        self.output_dir = os.path.dirname(os.path.realpath(__file__))
        self.headers = {'User-Agent': 'ProyectoRuteoEconomico-ETL/1.0'}

    def extraer_y_transformar(self):
        """
        Extrae los datos del CSV, los procesa y los transforma a GeoJSON.
        """
        print("-> 1. Extrayendo y transformando datos de incendios desde el CSV de CONAF...")
        features = []
        try:
            with requests.get(self.CSV_URL, headers=self.headers, stream=True, timeout=30) as r:
                r.raise_for_status()
                lines = (line.decode('utf-8') for line in r.iter_lines())
                csv_reader = csv.DictReader(lines)

                for row in csv_reader:
                    try:
                        if not row.get('lat') or not row.get('lon'):
                            continue

                        fecha_str = row['f_inicio']
                        fecha_obj = None
                        try:
                            fecha_obj = datetime.strptime(fecha_str, '%b %d, %Y, %H:%M')
                        except ValueError:
                            try:
                                fecha_obj = datetime.strptime(fecha_str, '%Y-%m-%d %H:%M')
                            except ValueError:
                                continue

                        fecha_iso = fecha_obj.replace(tzinfo=timezone.utc).isoformat()

                        feature = {
                            "type": "Feature",
                            "properties": {
                                "tipo_amenaza": "incendio_forestal",
                                "fuente": "CONAF (GitHub)",
                                "titulo": row.get('nombre'),
                                "estado": row.get('estado'),
                                "comuna": row.get('comuna'),
                                "region": row.get('region'),
                                "fecha_inicio_utc": fecha_iso,
                                "superficie_ha": float(row['sup_total'].replace(',', '.')) if row.get(
                                    'sup_total') else 0,
                                "nivel_alerta": self._calcular_nivel_alerta(row.get('estado'))
                            },
                            "geometry": {
                                "type": "Point",
                                "coordinates": [
                                    float(row['lon']),
                                    float(row['lat'])
                                ]
                            }
                        }
                        features.append(feature)

                    except (ValueError, KeyError, TypeError):
                        continue

            print(f"   -> Transformación completada: {len(features)} incendios procesados.")

            # --- ORDENAMIENTO POR FECHA ---
            # Ordenamos la lista de 'features' basándonos en la fecha de inicio.
            print("   -> Ordenando incendios por fecha...")
            features.sort(key=lambda item: item['properties']['fecha_inicio_utc'])
            # --- FIN DE LA MODIFICACIÓN ---

            return features

        except requests.exceptions.RequestException as e:
            print(f"   -> ERROR de red o HTTP al consultar el CSV: {e}")
            return None

    def _calcular_nivel_alerta(self, estado):
        if not estado: return 'indefinido'
        estado_lower = estado.lower()
        if 'en combate' in estado_lower:
            return 'rojo'
        elif 'controlado' in estado_lower:
            return 'amarillo'
        elif 'extinguido' in estado_lower:
            return 'verde'
        else:
            return 'gris'

    def guardar_json(self, features):
        if features is None:
            print("-> No se generaron datos para guardar.")
            return

        feature_collection = {
            "type": "FeatureCollection",
            "metadata": {
                "generado": datetime.now().isoformat(),
                "fuente_datos": self.CSV_URL,
                "descripcion": "Incendios forestales de la temporada actual reportados por CONAF."
            },
            "features": features
        }

        output_path = os.path.join(self.output_dir, "amenaza_incendios.geojson")
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(feature_collection, f, indent=2, ensure_ascii=False)
            print(f"-> 2. Archivo 'amenaza_incendios.geojson' guardado exitosamente.")
        except IOError as e:
            print(f"   -> ERROR al guardar el archivo: {e}")

    def ejecutar(self):
        print("\n--- Iniciando Proceso ETL para Amenaza de Incendios (Fuente: CONAF CSV) ---")
        datos_transformados = self.extraer_y_transformar()
        self.guardar_json(datos_transformados)
        print("--- Proceso Finalizado ---\n")


if __name__ == "__main__":
    etl_incendios = IncendiosConafETL()
    etl_incendios.ejecutar()