import requests
import json
import os

# --- CONFIGURACIÓN ---
# 1. REEMPLAZA ESTO CON TU PROPIA API KEY DE TOLLGURU
#    La puedes obtener gratis en https://tollguru.com/developers
API_KEY = "tg_476C95B6D2F74B4EA739A81ECFD3A5AB"

# 2. Define el origen y destino
ORIGEN = "Santiago, Chile"
DESTINO = "Viña del Mar, Chile"

# 3. Nombre del archivo de salida
NOMBRE_ARCHIVO_SALIDA = "peajes_santiago_vina_tollguru.json"


# --- LÓGICA DEL SCRIPT ---

def consultar_peajes_tollguru():
    """
    Realiza la consulta a la API de TollGuru y guarda la respuesta en un archivo JSON.
    """
    if API_KEY == "REEMPLAZA_CON_TU_API_KEY":
        print(
            "Error: Por favor, reemplaza 'REEMPLAZA_CON_TU_API_KEY' con tu clave de API real de TollGuru en el script.")
        return

    # URL del endpoint de la API según la documentación
    url = "https://apis.tollguru.com/toll/v2/origin-destination-waypoints"

    # Encabezados de la petición, incluyendo la clave de la API
    headers = {
        'Content-Type': 'application/json',
        'x-api-key': API_KEY
    }

    # Cuerpo (payload) de la petición.
    # Usamos '2AxlesAuto' para un vehículo liviano estándar.
    payload = {
        "from": {
            "address": ORIGEN
        },
        "to": {
            "address": DESTINO
        },
        "vehicle": {
            "type": "2AxlesAuto"
        }
        # Puedes agregar más parámetros aquí si es necesario, como 'waypoints'
    }

    print(f"Realizando consulta a TollGuru para la ruta: '{ORIGEN}' -> '{DESTINO}'...")

    try:
        # Realizamos la petición POST
        response = requests.post(url, headers=headers, json=payload)

        # Verificamos si la petición fue exitosa (código 200)
        if response.status_code == 200:
            print("¡Consulta exitosa!")

            # Convertimos la respuesta a formato JSON
            data = response.json()

            # Guardamos la data en un archivo
            # Usamos indent=4 para que el JSON sea legible y ensure_ascii=False para caracteres como 'ñ'
            with open(NOMBRE_ARCHIVO_SALIDA, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)

            print(f"Los datos de los peajes se han guardado en el archivo: '{os.path.abspath(NOMBRE_ARCHIVO_SALIDA)}'")

            # Imprimimos un resumen útil en la consola
            if data.get('routes'):
                print("\n--- Resumen de la Ruta Más Rápida ---")
                ruta_principal = data['routes'][0]
                distancia = ruta_principal['summary']['distance']['metric']
                duracion = ruta_principal['summary']['duration']['text']
                costo_tag = ruta_principal['costs'].get('tag', 'N/A')
                moneda = data['summary'].get('currency', '')

                print(f"  Distancia: {distancia}")
                print(f"  Duración: {duracion}")
                print(f"  Costo total en peajes (TAG): {costo_tag} {moneda}")
                print("\nPeajes encontrados en la ruta:")
                for peaje in ruta_principal.get('tolls', []):
                    print(f"  - {peaje['name']} ({peaje['road']}): {peaje.get('tagCost', 'N/A')} {moneda}")

        else:
            # Si hay un error, lo mostramos para facilitar el diagnóstico
            print(f"Error en la consulta. Código de estado: {response.status_code}")
            print("Respuesta de la API:")
            print(response.text)

    except requests.exceptions.RequestException as e:
        print(f"Ocurrió un error de conexión: {e}")


if __name__ == "__main__":
    consultar_peajes_tollguru()