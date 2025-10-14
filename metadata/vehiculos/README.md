# Estructura del Archivo `metadata_vehiculos.json`

## Descripción General

Este archivo JSON contiene una lista de vehículos, donde cada objeto representa una versión específica de un modelo. Los datos han sido extraídos (scraping) del portal Chileautos y posteriormente transformados para estandarizar y limpiar los campos más relevantes para el cálculo de costos de ruta, como el consumo de combustible y la capacidad del estanque.

## Formato del Archivo

El archivo es un **Array de Objetos JSON**. Cada objeto tiene la siguiente estructura:

### Ejemplo de un Objeto de Vehículo

```json
{
  "modelo_base": "Toyota Yaris",
  "version": "1.5 GLI MT",
  "especificaciones_clave": {
    "consumo_mixto_kml": 17.1,
    "consumo_urbano_kml": 13.6,
    "consumo_extraurbano_kml": 20.0,
    "capacidad_estanque_litros": 42.0,
    "motor_litros": 1.5,
    "transmision": "Mecánica",
    "traccion": "delantera"
  }
}
```

### Descripción de Campos

| Campo | Tipo de Dato | Descripción |
| :--- | :--- | :--- |
| `modelo_base` | String | El nombre de la marca y el modelo base del vehículo. Ejemplo: "Toyota Yaris". |
| `version` | String | La descripción de la versión específica del modelo. Ejemplo: "1.5 GLI MT". |
| `especificaciones_clave` | Object | Un objeto que contiene las especificaciones técnicas más importantes del vehículo. |
| `especificaciones_clave.consumo_mixto_kml` | Number / Null | El rendimiento de combustible en modo mixto, medido en kilómetros por litro (km/l). |
| `especificaciones_clave.consumo_urbano_kml` | Number / Null | El rendimiento de combustible en ciudad, medido en kilómetros por litro (km/l). |
| `especificaciones_clave.consumo_extraurbano_kml` | Number / Null | El rendimiento de combustible en carretera, medido en kilómetros por litro (km/l). |
| `especificaciones_clave.capacidad_estanque_litros` | Number / Null | La capacidad total del estanque de combustible, medida en litros. |
| `especificaciones_clave.motor_litros` | Number / Null | La cilindrada del motor, medida en litros. |
| `especificaciones_clave.transmision` | String / Null | El tipo de transmisión del vehículo. Ejemplo: "Mecánica", "Automática". |
| `especificaciones_clave.traccion` | String / Null | El tipo de tracción del vehículo. Ejemplo: "delantera", "4x4". |