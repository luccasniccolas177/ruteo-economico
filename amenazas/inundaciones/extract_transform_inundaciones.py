import requests
import json
import os
from datetime import datetime, timezone
import urllib3

# --- ADVERTENCIA DE SEGURIDAD ---
# La siguiente línea deshabilita los warnings de seguridad para conexiones SSL.
# Se usa porque el servidor del MOP puede tener un certificado que no es validado
# por las librerías estándar. No es una práctica recomendada para producción general.
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class InundacionesETL:
    """
    Automatiza la extracción y transformación de alertas hidrológicas desde el
    servicio MapServer de la DGA a un archivo GeoJSON estandarizado.
    """

    API_URL = "https://rest-sit.mop.gob.cl/arcgis/rest/services/DGA/ALERTAS/MapServer/0/query"

    def __init__(self):
        self.output_dir = os.path.dirname(os.path.realpath(__file__))
        self.headers = {'User-Agent': 'ProyectoRuteoEconomico-ETL/1.0'}

    def extraer_alertas(self):
        """
        Extrae los datos crudos de las alertas hidrológicas desde la API de la DGA.
        """
        print("-> 1. Extrayendo datos de alertas hidrológicas desde la API de la DGA...")
        params = {
            'where': '1=1',  # Traer todos los registros
            'outFields': '*',  # Traer todos los campos
            'f': 'json',  # Formato de salida
            'returnGeometry': 'true'  # Incluir las coordenadas
        }
        try:
            # Se usa verify=False debido a problemas con el certificado SSL del servidor del MOP.
            response = requests.get(self.API_URL, params=params, headers=self.headers, timeout=30, verify=False)
            response.raise_for_status()
            alertas_data = response.json()

            num_alertas = len(alertas_data.get('features', []))
            print(f"   -> Extracción exitosa: Se encontraron {num_alertas} alertas.")
            return alertas_data

        except requests.exceptions.RequestException as e:
            print(f"   -> ERROR de red o HTTP al consultar la API de la DGA: {e}")
        except json.JSONDecodeError:
            print("   -> ERROR: La respuesta de la API de la DGA no es un JSON válido.")
        return None

    def transformar_a_geojson(self, alertas_crudas):
        """
        Transforma los datos crudos de formato ArcGIS a un GeoJSON FeatureCollection estándar.
        """
        print("-> 2. Transformando alertas a formato GeoJSON...")
        features = []
        for alerta in alertas_crudas.get('features', []):
            try:
                attrs = alerta.get('attributes', {})
                geom = alerta.get('geometry', {})

                # Los timestamps de ArcGIS a menudo vienen en milisegundos desde la época Unix
                timestamp_ms = attrs.get('FECHA_REGISTRO')
                if timestamp_ms:
                    fecha_hora_utc = datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc)
                else:
                    fecha_hora_utc = datetime.now(timezone.utc)  # Fallback

                feature = {
                    "type": "Feature",
                    "properties": {
                        "tipo_amenaza": "inundacion",
                        "fuente": "DGA MOP",
                        "estacion_monitoreo": attrs.get('NOMBRE_ESTACION'),
                        "rio": attrs.get('RIO'),
                        "region": attrs.get('REGION'),
                        "estado_actual": attrs.get('ESTADO_ALERTA'),
                        "caudal_m3s": attrs.get('CAUDAL'),
                        "fecha_hora_utc": fecha_hora_utc.isoformat(),
                        "nivel_alerta": self._calcular_nivel_alerta(attrs.get('ESTADO_ALERTA'))
                    },
                    "geometry": {
                        "type": "Point",
                        "coordinates": [geom.get('x'), geom.get('y')]
                    }
                }
                features.append(feature)

            except (KeyError, TypeError, AttributeError) as e:
                print(f"   -> Advertencia: Saltando una alerta por datos incompletos. Error: {e}")
                continue

        feature_collection = {
            "type": "FeatureCollection",
            "metadata": {
                "generado": datetime.now().isoformat(),
                "fuente_api": self.API_URL,
                "descripcion": "Alertas hidrológicas de estaciones de monitoreo de la DGA."
            },
            "features": features
        }

        print(f"   -> Transformación completada: {len(features)} alertas procesadas.")
        return feature_collection

    def _calcular_nivel_alerta(self, estado):
        """Determina un nivel de alerta simple basado en el texto del estado."""
        if not estado:
            return 'verde'  # Valor por defecto

        estado_lower = estado.lower()
        if 'rojo' in estado_lower or 'desborde' in estado_lower:
            return 'rojo'
        elif 'amarillo' in estado_lower:
            return 'amarillo'
        else:
            return 'verde'

    def guardar_json(self, data_geojson):
        """Guarda el GeoJSON FeatureCollection en un archivo."""
        output_path = os.path.join(self.output_dir, "amenaza_inundaciones.geojson")
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data_geojson, f, indent=2, ensure_ascii=False)
            print(f"-> 3. Archivo 'amenaza_inundaciones.geojson' guardado exitosamente.")
        except IOError as e:
            print(f"   -> ERROR al guardar el archivo: {e}")

    def ejecutar(self):
        """Orquesta el proceso completo de Extracción, Transformación y Guardado."""
        print("\n--- Iniciando Proceso ETL para Amenaza de Inundaciones ---")
        datos_crudos = self.extraer_alertas()
        if datos_crudos:
            datos_geojson = self.transformar_a_geojson(datos_crudos)
            self.guardar_json(datos_geojson)
        print("--- Proceso Finalizado ---\n")


if __name__ == "__main__":
    etl_inundaciones = InundacionesETL()
    etl_inundaciones.ejecutar()