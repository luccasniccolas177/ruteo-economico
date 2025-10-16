import requests
import json
from datetime import datetime
import os
from dotenv import load_dotenv


class RawExtractorCombustibleCNE:
    """
    Clase dedicada a la EXTRACCIÓN de datos crudos de la API de la CNE.
    Obtiene el email y la contraseña desde el archivo .env, solicita un token
    y guarda la respuesta de la API directamente en un archivo JSON.
    """

    def __init__(self):
        """
        Inicializa el extractor cargando las credenciales desde el archivo .env.
        """
        load_dotenv()  # Carga las variables de entorno del archivo .env

        self.email = os.getenv("CNE_EMAIL")
        self.password = os.getenv("CNE_PASSWORD")

        if not self.email or not self.password:
            raise ValueError("Las variables CNE_EMAIL y CNE_PASSWORD no están definidas en el archivo .env.")

        self.token = None
        self.output_dir = os.path.dirname(os.path.realpath(__file__))
        self.url_login = "https://api.cne.cl/api/login"
        self.url_estaciones_base = "https://api.cne.cl/api/v4/estaciones"
        self.headers = {'Accept': 'application/json', 'User-Agent': 'RuteoEconomico-Extractor/1.0'}

    def obtener_token_cne(self):
        """
        Solicita un token de autenticación a la API de la CNE.
        """
        print("Solicitando token de autenticación a la CNE...")
        payload = {"email": self.email, "password": self.password}
        try:
            response = requests.post(self.url_login, json=payload, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            if 'token' in data:
                self.token = data['token']
                print("Token obtenido exitosamente.")
                return True
            else:
                print(f"Error: La respuesta de login no contenía un token. Respuesta: {data}")
                return False
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                print("-> ERROR CRÍTICO: Email o contraseña incorrectos en el archivo .env.")
            else:
                print(f"Error HTTP al obtener el token: {e.response.status_code} {e.response.reason}")
            return False
        except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
            print(f"Error crítico de conexión o formato al obtener el token: {e}")
            return False

    def extraer_datos_crudos(self):
        """
        Extrae la lista de estaciones y la devuelve como una lista de diccionarios (JSON crudo).
        """
        if not self.token:
            print("Error: No hay token disponible para realizar la solicitud.")
            return None
        print("Conectando con la API para descargar datos crudos de estaciones...")
        url_con_token = f"{self.url_estaciones_base}?token={self.token}"
        try:
            respuesta = requests.get(url_con_token, headers=self.headers, timeout=60)
            respuesta.raise_for_status()
            datos_json = respuesta.json()
            if isinstance(datos_json, list):
                print(f"Datos crudos recibidos. Se encontraron {len(datos_json)} registros.")
                return datos_json
            else:
                print(f"Error: La respuesta de la API no fue una lista. Respuesta: {datos_json}")
                return None
        except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
            print(f"Error crítico al consultar o decodificar la API de estaciones: {e}")
            return None

    def guardar_datos_crudos(self, datos_crudos):
        """
        Guarda la lista de datos crudos directamente en un archivo JSON.
        """
        timestamp_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename_json = f"raw_combustibles_{timestamp_str}.json"
        filepath_json = os.path.join(self.output_dir, filename_json)
        try:
            with open(filepath_json, 'w', encoding='utf-8') as f:
                json.dump(datos_crudos, f, ensure_ascii=False, indent=2)
            print(f"Archivo JSON con datos crudos generado exitosamente en: {filepath_json}")
            return filepath_json
        except IOError as e:
            print(f"Error al guardar el archivo JSON: {e}")
            return None

    def ejecutar(self):
        """
        Orquesta el proceso de extracción y guardado de datos crudos.
        """
        if not self.obtener_token_cne():
            return None
        datos_crudos = self.extraer_datos_crudos()
        if datos_crudos:
            return self.guardar_datos_crudos(datos_crudos)
        return None


if __name__ == "__main__":
    print("--- Proceso de EXTRACCIÓN CRUDA de Metadata de Combustibles (Automatizado) ---")
    try:
        extractor = RawExtractorCombustibleCNE()  # Ya no necesita argumentos
        if extractor.ejecutar():
            print("\nProceso de extracción finalizado con éxito.")
        else:
            print("\nEl proceso de extracción falló.")
    except Exception as e:
        # Captura errores de inicialización (ej. si faltan las variables en .env)
        print(f"Ha ocurrido un error inesperado durante la ejecución: {e}")