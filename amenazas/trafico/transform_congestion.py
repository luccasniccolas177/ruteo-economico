import json
import os
import glob
from datetime import datetime


class TransformadorCongestion:
    """
    Transforma los datos crudos de la API de Google Directions en un formato
    limpio y estandarizado con un factor de congestión calculado.
    """

    def __init__(self):
        self.script_dir = os.path.dirname(os.path.realpath(__file__))

    def encontrar_ultimo_json_crudo(self):
        """Encuentra el archivo raw_congestion_*.json más reciente."""
        try:
            lista_de_archivos = glob.glob(os.path.join(self.script_dir, 'raw_congestion_*.json'))
            if not lista_de_archivos: return None
            return max(lista_de_archivos, key=os.path.getctime)
        except Exception as e:
            print(f"Error buscando archivo crudo: {e}")
            return None

    def transformar(self):
        print("--- Iniciando Proceso de Transformación de Datos de Congestión ---")

        archivo_crudo = self.encontrar_ultimo_json_crudo()
        if not archivo_crudo:
            print("Error: No se encontró un archivo 'raw_congestion_*.json' para procesar.")
            return

        print(f"Procesando archivo: {os.path.basename(archivo_crudo)}")

        try:
            with open(archivo_crudo, 'r', encoding='utf-8') as f:
                datos_crudos = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error al leer el archivo JSON crudo: {e}")
            return

        tramos_transformados = []
        fecha_medicion = datetime.now().isoformat()

        for resultado in datos_crudos:
            try:
                # La información principal está en la primera (y usualmente única) ruta
                ruta = resultado['routes'][0]
                tramo = ruta['legs'][0]

                tiempo_ideal = tramo['duration']['value']
                tiempo_real = tramo['duration_in_traffic']['value']

                # Calcular el factor de congestión
                if tiempo_ideal > 0:
                    factor = (tiempo_real - tiempo_ideal) / tiempo_ideal
                else:
                    factor = 0.0

                tramo_limpio = {
                    "nombre_tramo": resultado['segmento_nombre'],
                    "tiempo_ideal_seg": tiempo_ideal,
                    "tiempo_real_seg": tiempo_real,
                    "factor_congestion": round(factor, 4),  # Redondear a 4 decimales
                    "polyline_google": ruta['overview_polyline']['points'],
                    "fecha_medicion": fecha_medicion
                }
                tramos_transformados.append(tramo_limpio)

            except (KeyError, IndexError) as e:
                print(
                    f"  -> Advertencia: No se pudo procesar el tramo '{resultado.get('segmento_nombre', 'N/A')}' por falta de datos. Error: {e}")

        print(f"Transformación completada. Se procesaron {len(tramos_transformados)} tramos.")
        self.guardar_json(tramos_transformados)

    def guardar_json(self, data):
        timestamp_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"transformed_congestion_{timestamp_str}.json"
        filepath = os.path.join(self.script_dir, filename)

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"Archivo transformado guardado exitosamente en: {filepath}")
        except IOError as e:
            print(f"Error al guardar el archivo JSON transformado: {e}")


if __name__ == '__main__':
    transformador = TransformadorCongestion()
    transformador.transformar()