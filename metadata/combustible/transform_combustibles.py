import json
import os
import glob
from datetime import datetime


class TransformadorCombustible:
    def __init__(self):
        self.script_dir = os.path.dirname(os.path.realpath(__file__))
        self.COMBUSTIBLE_KEY_MAP = {
            "93": "gasolina_93", "A93": "gasolina_93",
            "95": "gasolina_95", "A95": "gasolina_95",
            "97": "gasolina_97", "A97": "gasolina_97",
            "DI": "petroleo_diesel", "ADI": "petroleo_diesel",
            "GLP": "glp_vehicular",
            "GNC": "gnc"
        }

    def encontrar_ultimo_json_crudo(self):
        try:
            lista_de_archivos = glob.glob(os.path.join(self.script_dir, 'raw_combustibles_*.json'))
            if not lista_de_archivos: return None
            return max(lista_de_archivos, key=os.path.getctime)
        except Exception as e:
            print(f"Error al buscar el archivo JSON crudo: {e}")
            return None

    def transformar_datos(self, datos_crudos):
        if not isinstance(datos_crudos, list):
            print("Error: Los datos de entrada no son una lista.")
            return []

        print(f"Transformando {len(datos_crudos)} registros crudos de estaciones...")

        # --- INICIO DE LA CORRECCIÓN CLAVE ---
        # Usar un diccionario para almacenar las estaciones transformadas,
        # usando el 'id_estacion_cne' como clave para eliminar duplicados automáticamente.
        estaciones_transformadas_dict = {}
        # --- FIN DE LA CORRECCIÓN CLAVE ---

        for estacion_raw in datos_crudos:
            try:
                id_cne = estacion_raw.get('codigo')
                if not id_cne:
                    continue  # Saltar registros sin código

                ubicacion_raw = estacion_raw.get('ubicacion', {})
                lat_str = str(ubicacion_raw.get("latitud", "")).replace(',', '.')
                lon_str = str(ubicacion_raw.get("longitud", "")).replace(',', '.')
                lat = float(lat_str) if lat_str else None
                lon = float(lon_str) if lon_str else None

                if lat is None or lon is None:
                    continue  # Saltar estaciones sin coordenadas válidas

                estacion_limpia = {
                    "id_estacion_cne": id_cne,
                    "nombre": estacion_raw.get('razon_social', 'N/A').strip(),
                    "marca": estacion_raw.get('distribuidor', {}).get('marca', 'Sin Marca'),
                    "direccion": ubicacion_raw.get('direccion', 'N/A').strip(),
                    "comuna": ubicacion_raw.get('nombre_comuna'),
                    "region": ubicacion_raw.get('nombre_region'),
                    "horario": estacion_raw.get('horario_atencion'),
                    "latitud": lat,
                    "longitud": lon
                }

                precios_procesados = {}
                for key_raw, data_precio in estacion_raw.get('precios', {}).items():
                    tipo_combustible_limpio = self.COMBUSTIBLE_KEY_MAP.get(key_raw)
                    if not tipo_combustible_limpio or tipo_combustible_limpio in precios_procesados:
                        continue

                    try:
                        fecha_str = data_precio.get('fecha_actualizacion')
                        hora_str = data_precio.get('hora_actualizacion')
                        fecha_obj = datetime.strptime(f"{fecha_str} {hora_str}", "%Y-%m-%d %H:%M:%S")
                        precio_entero = int(float(data_precio.get('precio')))

                        precios_procesados[tipo_combustible_limpio] = {
                            "tipo_combustible": tipo_combustible_limpio,
                            "precio": precio_entero,
                            "fecha_actualizacion": fecha_obj.isoformat()
                        }
                    except (ValueError, TypeError, AttributeError):
                        continue

                estacion_limpia["precios"] = list(precios_procesados.values())

                if estacion_limpia["precios"]:
                    # --- CORRECCIÓN CLAVE ---
                    # Añadir/sobreescribir la estación en el diccionario.
                    estaciones_transformadas_dict[id_cne] = estacion_limpia
                    # --- FIN DE LA CORRECCIÓN ---

            except Exception as e:
                print(
                    f"Advertencia: No se pudo procesar la estación con código '{estacion_raw.get('codigo')}'. Error: {e}")

        # --- CORRECCIÓN CLAVE ---
        # Convertir los valores del diccionario de nuevo a una lista para el resultado final.
        estaciones_finales = list(estaciones_transformadas_dict.values())
        # --- FIN DE LA CORRECCIÓN ---

        print(f"Transformación completada. Se procesaron {len(estaciones_finales)} estaciones ÚNICAS y válidas.")
        return estaciones_finales

    def guardar_json_transformado(self, datos_transformados):
        timestamp_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename_json = f"transformed_combustibles_{timestamp_str}.json"
        filepath_json = os.path.join(self.script_dir, filename_json)

        final_data = {
            "metadata": {
                "fuente": "Transformación de datos crudos CNE",
                "fecha_transformacion": datetime.now().isoformat(),
                "total_estaciones_procesadas": len(datos_transformados)
            },
            "estaciones": datos_transformados
        }

        try:
            with open(filepath_json, 'w', encoding='utf-8') as f:
                json.dump(final_data, f, ensure_ascii=False, indent=2)
            print(f"Archivo JSON transformado guardado exitosamente en: {filepath_json}")
            return filepath_json
        except IOError as e:
            print(f"Error al guardar el archivo JSON transformado: {e}")
            return None

    def ejecutar(self):
        print("--- Iniciando proceso de Transformación de Datos de Combustibles ---")
        archivo_crudo = self.encontrar_ultimo_json_crudo()
        if not archivo_crudo:
            print("Error: No se encontró ningún archivo 'raw_combustibles_*.json' para procesar.")
            return

        print(f"Procesando archivo: {os.path.basename(archivo_crudo)}")
        try:
            with open(archivo_crudo, 'r', encoding='utf-8') as f:
                datos_crudos = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error al leer o decodificar el archivo JSON crudo: {e}")
            return

        datos_transformados = self.transformar_datos(datos_crudos)

        if datos_transformados:
            self.guardar_json_transformado(datos_transformados)
            print("\nProceso de transformación finalizado con éxito.")
        else:
            print("\nNo se generaron datos transformados. Revisa las advertencias anteriores.")


if __name__ == "__main__":
    transformador = TransformadorCombustible()
    transformador.ejecutar()