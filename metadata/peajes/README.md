# Estructura del Archivo `transformed_peajes.json`

## Descripción General

Este archivo JSON contiene una lista de pórticos y plazas de peaje de Chile. Los datos son el resultado de un cruce (mapeo) entre dos fuentes: un archivo con información de precios (`precios.json`) y otro con datos de georreferenciación (`georef.json`). El script de transformación se encarga de unificar esta información, seleccionando los datos más relevantes y descartando aquellos que no pudieron ser mapeados geográficamente.

## Formato del Archivo

El archivo es un **Array de Objetos JSON**. Cada objeto representa un peaje único con su información y una lista de sus posibles tarifas.

### Ejemplo de un Objeto de Peaje

```json
[
  {
    "nombre": "Angostura",
    "concesionaria": "Ruta 5 Sur",
    "tipo": "Troncal",
    "latitud": -33.930814,
    "longitud": -70.715414,
    "tarifas": [
      {
        "categoria_vehiculo": "autos_y_camionetas",
        "tipo_tarifa": "TBFP",
        "precio": 3700.00
      },
      {
        "categoria_vehiculo": "motos_y_motonetas",
        "tipo_tarifa": "TBFP",
        "precio": 1100.00
      }
    ]
  }
]
```

### Descripción de Campos

| Campo | Tipo de Dato | Descripción |
| :--- | :--- | :--- |
| `nombre` | String | El nombre identificador del peaje o pórtico. |
| `concesionaria` | String | El nombre de la autopista o ruta concesionada a la que pertenece el peaje. |
| `tipo` | String | Clasificación del peaje. Generalmente "Troncal" o "Lateral". |
| `latitud` | Number | La coordenada de latitud (en formato WGS 84). |
| `longitud` | Number | La coordenada de longitud (en formato WGS 84). |
| `tarifas` | Array de Objetos | Una lista con las diferentes tarifas que aplica el peaje. |
| `tarifas[].categoria_vehiculo`| String | La descripción de la categoría de vehículo a la que aplica la tarifa (ej. "autos_y_camionetas"). |
| `tarifas[].tipo_tarifa` | String | El código del tipo de tarifa. **TBFP**: Tarifa Base Fuera Punta, **TBP**: Tarifa Base Punta, **TS**: Tarifa Saturación. |
| `tarifas[].precio` | Number | El costo de la tarifa en pesos chilenos (CLP). |