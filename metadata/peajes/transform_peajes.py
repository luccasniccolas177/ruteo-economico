import json
import os
from unidecode import unidecode
import re


class RobustTransformadorPeajes:
    """
    Versión robusta que utiliza matching por tokens para cruzar precios.json y georef.json,
    aumentando significativamente la cantidad de coincidencias.
    """

    def __init__(self):
        self.script_dir = os.path.dirname(os.path.realpath(__file__))

        # Palabras comunes a ignorar durante el matching para evitar falsos positivos
        self.STOP_WORDS = {
            'de', 'la', 'el', 'los', 'las', 'y', 'en', 'con', 'a',
            'troncal', 'lateral', 'paso', 'superior', 'acceso', 'enlace', 'plaza'
        }

        self.georef_data = self._cargar_y_preprocesar_georef()
        if not self.georef_data:
            raise RuntimeError("No se pudo cargar 'georef.json'.")

    def _normalizar_y_tokenizar(self, texto):
        """Convierte un texto en un conjunto de palabras clave (tokens) para comparar."""
        if not texto:
            return set()
        # Elimina caracteres no alfanuméricos (excepto espacios), convierte a minúsculas y quita tildes
        texto_limpio = unidecode(texto.lower())
        texto_limpio = re.sub(r'[^a-z0-9\s]', '', texto_limpio)
        # Divide en palabras y elimina las stop words
        tokens = set(texto_limpio.split())
        return tokens - self.STOP_WORDS

    def _cargar_y_preprocesar_georef(self):
        """Carga georef.json y pre-procesa los nombres en tokens para una búsqueda rápida."""
        georef_path = os.path.join(self.script_dir, 'georef.json')
        try:
            with open(georef_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            for peaje in data.get('peajes', []):
                # Añade un nuevo campo con los tokens pre-procesados a cada objeto de peaje
                peaje['tokens'] = self._normalizar_y_tokenizar(peaje.get('nombre'))

            print(f"Se cargaron y pre-procesaron {len(data.get('peajes', []))} peajes georreferenciados.")
            return data.get('peajes', [])
        except (IOError, json.JSONDecodeError) as e:
            print(f"Error crítico al leer 'georef.json': {e}")
            return None

    def _encontrar_mejor_match(self, nombre_portico):
        """
        Busca en todos los peajes georreferenciados y devuelve el que mejor coincida.
        """
        if not nombre_portico:
            return None

        tokens_portico = self._normalizar_y_tokenizar(nombre_portico)
        if not tokens_portico:
            return None

        mejor_match = None
        max_coincidencias = 0

        for peaje_geo in self.georef_data:
            coincidencias = len(tokens_portico.intersection(peaje_geo['tokens']))

            # Criterio de match: debe tener al menos una palabra clave en común y ser la mejor opción hasta ahora
            if coincidencias > 0 and coincidencias > max_coincidencias:
                max_coincidencias = coincidencias
                mejor_match = peaje_geo

        return mejor_match

    def transformar(self):
        precios_path = os.path.join(self.script_dir, 'precios.json')
        try:
            with open(precios_path, 'r', encoding='utf-8') as f:
                precios_data = json.load(f)
        except (IOError, json.JSONDecodeError) as e:
            print(f"Error crítico al leer 'precios.json': {e}")
            return

        peajes_transformados = {}

        for autopista in precios_data.get('autopistas', []):
            concesionaria = autopista.get('nombre_autopista')

            for eje in autopista.get('ejes', []):
                secciones = eje.get('direcciones', [eje])  # Unifica las dos estructuras
                for seccion in secciones:
                    for portico in seccion.get('porticos', []):
                        nombre_original = portico.get('nombre') or portico.get('referencia_tramo')

                        geo_data = self._encontrar_mejor_match(nombre_original)
                        if not geo_data:
                            # print(f"  -> Advertencia: No se encontró georreferencia para '{nombre_original}'")
                            continue

                        clave_unica = f"{concesionaria}-{geo_data['nombre']}"
                        if clave_unica in peajes_transformados:
                            continue

                        peaje_obj = {
                            "nombre": geo_data['nombre'],
                            "concesionaria": concesionaria,
                            "tipo": geo_data.get('tipo'),
                            "latitud": geo_data.get('latitude'),
                            "longitud": geo_data.get('longitude'),
                            "tarifas": []
                        }

                        peajes_raw = portico.get('peajes', {})
                        for cat_key, precios in peajes_raw.items():
                            # ... (El resto de la lógica de extracción de precios es la misma) ...
                            if isinstance(precios, dict):
                                for tipo_tarifa, precio_val in precios.items():
                                    if precio_val is not None:
                                        peaje_obj["tarifas"].append({
                                            "categoria_vehiculo": cat_key,
                                            "tipo_tarifa": tipo_tarifa,
                                            "precio": precio_val
                                        })
                            else:
                                peaje_obj["tarifas"].append({
                                    "categoria_vehiculo": cat_key,
                                    "tipo_tarifa": "TBFP",
                                    "precio": precios
                                })

                        if peaje_obj["tarifas"]:
                            peajes_transformados[clave_unica] = peaje_obj

        lista_final = list(peajes_transformados.values())
        print(f"Transformación completada. Se mapearon y procesaron {len(lista_final)} peajes únicos.")
        self.guardar_json(lista_final)

    def guardar_json(self, data):
        """Guarda los datos transformados en un archivo JSON."""
        output_path = os.path.join(self.script_dir, 'transformed_peajes.json')
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"Archivo transformado guardado exitosamente en: {output_path}")
        except IOError as e:
            print(f"Error al guardar el archivo transformado: {e}")


if __name__ == '__main__':
    # Es necesario instalar unidecode: pip install unidecode
    print("--- Iniciando Proceso de Transformación ROBUSTA de Datos de Peajes ---")
    transformador = RobustTransformadorPeajes()
    transformador.transformar()