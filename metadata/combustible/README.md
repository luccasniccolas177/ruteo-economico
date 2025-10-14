# Estructura del Archivo `transformed_combustibles_[fecha].json`

## Descripción General

Este archivo JSON contiene una lista de estaciones de servicio (bencineras) de Chile. Los datos son extraídos de la API de la Comisión Nacional de Energía (CNE), procesados para eliminar duplicados, estandarizar campos y prepararlos para su carga en la base de datos. Cada estación incluye su información principal y una lista de los combustibles que vende con sus respectivos precios.

## Formato del Archivo

El archivo es un **Objeto JSON** con dos claves principales: `metadata` y `estaciones`. La clave `estaciones` contiene un **Array de Objetos**, donde cada objeto representa una bencinera única.

### Ejemplo de la Estructura

```json
{
  "metadata": {
    "fuente": "Transformación de datos crudos CNE",
    "fecha_transformacion": "2025-10-14T12:30:00.123456",
    "total_estaciones_procesadas": 1792
  },
  "estaciones": [
    {
      "id_estacion_cne": "co110101",
      "nombre": "IRACABAL OTTH HENRI EDWARD JEAN",
      "marca": "COPEC",
      "direccion": "VIVAR 402",
      "comuna": "Iquique",
      "region": "Tarapacá",
      "horario": "Lunes a Domingo 24 horas",
      "latitud": -20.213349,
      "longitud": -70.148566,
      "precios": [
        {
          "tipo_combustible": "gasolina_93",
          "precio": 1310,
          "fecha_actualizacion": "2025-10-09T14:07:32"
        },
        {
          "tipo_combustible": "petroleo_diesel",
          "precio": 1046,
          "fecha_actualizacion": "2025-10-09T14:07:32"
        }
      ]
    }
  ]
}
```

### Descripción de Campos

| Campo | Tipo de Dato | Descripción |
| :--- | :--- | :--- |
| `metadata` | Object | Contiene información sobre el proceso de generación del archivo. |
| `metadata.fuente` | String | Indica el origen de los datos. |
| `metadata.fecha_transformacion` | String (ISO 8601) | La fecha y hora en que se ejecutó el script de transformación. |
| `metadata.total_estaciones_procesadas` | Integer | El número total de estaciones incluidas en el archivo. |
| `estaciones` | Array de Objetos | La lista principal de estaciones de servicio. |
| `estaciones[].id_estacion_cne` | String | El código identificador único de la estación según la CNE. |
| `estaciones[].nombre` | String | La razón social o nombre comercial de la estación. |
| `estaciones[].marca` | String | La marca de la distribuidora (ej. "COPEC", "Shell"). |
| `estaciones[].direccion` | String | La dirección física de la estación. |
| `estaciones[].comuna` | String | La comuna donde se ubica la estación. |
| `estaciones[].region` | String | La región donde se ubica la estación. |
| `estaciones[].horario` | String / Null | El horario de atención informado. |
| `estaciones[].latitud` | Number | La coordenada de latitud (en formato WGS 84). |
| `estaciones[].longitud` | Number | La coordenada de longitud (en formato WGS 84). |
| `estaciones[].precios` | Array de Objetos | Una lista con los precios de los combustibles disponibles en la estación. |
| `precios[].tipo_combustible` | String | El nombre estandarizado del combustible (ej. "gasolina_93", "petroleo_diesel"). |
| `precios[].precio` | Integer | El precio del combustible por litro, en pesos chilenos (CLP). |
| `precios[].fecha_actualizacion` | String (ISO 8601) | La fecha y hora de la última actualización de ese precio. |