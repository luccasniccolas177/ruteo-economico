# Estructura del Archivo `amenaza_incendios.geojson`

## Descripción General 📝

Este archivo en formato **GeoJSON** contiene información sobre los incendios forestales registrados durante la temporada actual en Chile. Los datos son extraídos directamente del repositorio público de **CONAF** en GitHub, que es la fuente de datos cruda que alimenta su visor oficial.

El propósito del archivo es proporcionar una capa de datos geoespaciales lista para ser consumida por aplicaciones de mapeo (como Leaflet) para visualizar la amenaza de incendios como puntos en un mapa. El script de generación (`extract_transform_incendios.py`) se encarga de convertir el formato CSV original a GeoJSON y estandarizar los campos.

---

## Formato del Archivo 📄

El archivo es un objeto **`FeatureCollection`** de GeoJSON. La estructura principal contiene una lista (`features`) donde cada elemento es un objeto `Feature` que representa un incendio individual. La lista de incendios está **ordenada cronológicamente** por la fecha de inicio.

### Ejemplo de un Objeto `Feature` (Incendio)

```json
{
  "type": "Feature",
  "properties": {
    "tipo_amenaza": "incendio_forestal",
    "fuente": "CONAF (GitHub)",
    "titulo": "LAS MERCEDES",
    "estado": "Extinguido",
    "comuna": "Lampa",
    "region": "Metropolitana",
    "fecha_inicio_utc": "2025-10-15T16:47:00+00:00",
    "superficie_ha": 0.0,
    "nivel_alerta": "verde"
  },
  "geometry": {
    "type": "Point",
    "coordinates": [
      -70.92805,
      -33.23722
    ]
  }
}
```

## Descripción de Campos

### Objeto Principal

| Campo | Tipo | Descripción |
| :--- | :--- | :--- |
| **`type`** | String | Siempre será `"FeatureCollection"`. |
| **`metadata`** | Object | Contiene información sobre la generación del archivo, como la fecha y la fuente de datos. |
| **`features`** | Array | La lista que contiene todos los `Feature` de los incendios, ordenada por fecha de inicio. |

### `properties` (Dentro de cada `Feature`)

| Campo | Tipo | Descripción |
| :--- | :--- | :--- |
| **`tipo_amenaza`** | String | Identificador fijo del tipo de amenaza. Siempre será `"incendio_forestal"`. |
| **`fuente`** | String | La institución que reporta el dato. En este caso, `"CONAF (GitHub)"`. |
| **`titulo`** | String | El nombre oficial del incendio. |
| **`estado`** | String | El estado actual del incendio reportado por CONAF (ej. "Extinguido", "Controlado", "En combate"). |
| **`comuna`** | String | La comuna donde se ubica el incendio. |
| **`region`** | String | La región donde se ubica el incendio. |
| **`fecha_inicio_utc`** | String (ISO 8601)| La fecha y hora de inicio del evento en formato estándar UTC. |
| **`superficie_ha`** | Number | La superficie total afectada por el incendio, medida en hectáreas (ha). |
| **`nivel_alerta`** | String | Una clasificación simple del riesgo basada en el estado del incendio: `verde` (Extinguido), `amarillo` (Controlado), `rojo` (En combate). |

### `geometry` (Dentro de cada `Feature`)

| Campo | Tipo | Descripción |
| :--- | :--- | :--- |
| **`type`** | String | El tipo de geometría. Para incendios, siempre será `"Point"`. |
| **`coordinates`** | Array | Un array con las coordenadas del punto de referencia del incendio en el formato estándar de GeoJSON: **`[longitud, latitud]`**. |