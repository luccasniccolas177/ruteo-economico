import requests
import json
import os
from dotenv import load_dotenv
from datetime import datetime


class ExtractorCongestion:
    """
    Extrae datos de tráfico de la API de Google Directions para segmentos predefinidos.
    """

    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv("GOOGLE_MAPS_API_KEY")
        if not self.api_key:
            raise ValueError("No se encontró GOOGLE_MAPS_API_KEY en el archivo .env.")

        self.api_url = "https://maps.googleapis.com/maps/api/directions/json"
        self.output_dir = os.path.dirname(os.path.realpath(__file__))

        # Lista de tramos de ruta representativos para analizar en Santiago.
        # Puedes añadir, modificar o quitar los que estimes convenientes.
        self.segmentos = [
            {"nombre": "Alameda (Poniente a Oriente)", "origen": "-33.4475,-70.6800", "destino": "-33.4373,-70.6350"},
            {"nombre": "Providencia (Oriente a Poniente)", "origen": "-33.4200,-70.6070",
             "destino": "-33.4323,-70.6270"},
            {"nombre": "Costanera Norte (Oriente a Poniente)", "origen": "-33.4070,-70.5750",
             "destino": "-33.4200,-70.7100"},
            {"nombre": "Vespucio Norte (Oriente a Poniente)", "origen": "-33.3700,-70.6100",
             "destino": "-33.3890,-70.7300"},
            {"nombre": "Vespucio Sur (Poniente a Oriente)", "origen": "-33.5300,-70.6900",
             "destino": "-33.5150,-70.5850"},
            {"nombre": "Autopista Central (Norte a Sur)", "origen": "-33.4250,-70.6600", "destino": "-33.4750,-70.6630"}
        ]

    def extraer(self):
        """
        Itera sobre los segmentos, consulta la API de Google y guarda los resultados crudos.
        """
        print(f"Iniciando extracción de datos de congestión para {len(self.segmentos)} tramos...")
        resultados_crudos = []

        for segmento in self.segmentos:
            params = {
                'origin': segmento['origen'],
                'destination': segmento['destino'],
                'departure_time': 'now',  # Crucial para obtener 'duration_in_traffic'
                'key': self.api_key
            }

            try:
                print(f"  -> Consultando tramo: {segmento['nombre']}...")
                response = requests.get(self.api_url, params=params)
                response.raise_for_status()
                data = response.json()

                if data['status'] == 'OK':
                    # Añadir el nombre del segmento a la respuesta para usarlo después
                    data['segmento_nombre'] = segmento['nombre']
                    resultados_crudos.append(data)
                else:
                    print(
                        f"  -> Advertencia: La API devolvió estado '{data['status']}' para el tramo '{segmento['nombre']}'.")

            except requests.exceptions.RequestException as e:
                print(f"  -> Error de red al consultar el tramo '{segmento['nombre']}': {e}")

        self.guardar_json(resultados_crudos)

    def guardar_json(self, data):
        """Guarda los datos crudos en un archivo JSON con timestamp."""
        timestamp_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"raw_congestion_{timestamp_str}.json"
        filepath = os.path.join(self.output_dir, filename)

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"\nDatos crudos de congestión guardados en: {filepath}")
        except IOError as e:
            print(f"Error al guardar el archivo JSON: {e}")


if __name__ == "__main__":
    extractor = ExtractorCongestion()
    extractor.extraer()