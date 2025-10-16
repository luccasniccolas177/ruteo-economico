# Estructura del Archivo `amenaza_inundaciones.geojson`

## Descripción General 📝

Este archivo en formato **GeoJSON** contiene información sobre las alertas hidrológicas activas en Chile, que son un indicador clave para el riesgo de inundaciones. Los datos son extraídos directamente del servicio de mapas (MapServer) de la **Dirección General de Aguas (DGA)**, perteneciente al Ministerio de Obras Públicas (MOP).

El script de ETL procesa estos datos para estandarizarlos en un formato GeoJSON `FeatureCollection`, ideal para ser consumido por librerías de mapeo como Leaflet y visualizar las estaciones de monitoreo en alerta como puntos en un mapa.

---

## Formato del Archivo 📄

El archivo es un objeto **`FeatureCollection`** de GeoJSON. La estructura principal contiene una lista (`features`) donde cada elemento es un objeto `Feature` que representa una alerta en una estación de monitoreo específica.

### Ejemplo de un Objeto `Feature` (Alerta)

```json
{
  "type": "Feature",
  "properties": {
    "tipo_amenaza": "inundacion",
    "fuente": "DGA MOP",
    "estacion_monitoreo": "Río Cautín en Cajón",
    "rio": "Río Cautín",
    "region": "La Araucanía",
    "estado_actual": "BAJO UMBRAL AMARILLO",
    "caudal_m3s": 150.75,
    "fecha_hora_utc": "2025-10-15T20:30:00Z",
    "nivel_alerta": "amarillo"
  },
  "geometry": {
    "type": "Point",
    "coordinates": [
      -72.5,
      -38.7
    ]
  }
}
```

---

## Descripción de Campos 🔎

### Objeto Principal

| Campo | Tipo | Descripción |
| :--- | :--- | :--- |
| **`type`** | String | Siempre será `"FeatureCollection"`. |
| **`metadata`** | Object | Información sobre la generación del archivo, como la fecha y la URL de la fuente. |
| **`features`** | Array | La lista que contiene todos los `Feature` de las alertas. |

### `properties` (Dentro de cada `Feature`)

Estos son los datos descriptivos de cada alerta hidrológica.

| Campo | Tipo | Descripción |
| :--- | :--- | :--- |
| **`tipo_amenaza`** | String | Identificador fijo del tipo de amenaza. Siempre será `"inundacion"`. |
| **`fuente`** | String | La institución que reporta el dato. Siempre será `"DGA MOP"`. |
| **`estacion_monitoreo`**| String | Nombre de la estación fluviométrica que registra la alerta. |
| **`rio`** | String | Nombre del río que está siendo monitoreado por la estación. |
| **`region`** | String | Región donde se ubica la estación de monitoreo. |
| **`estado_actual`** | String | El estado descriptivo de la alerta según la DGA (ej. "BAJO UMBRAL AMARILLO"). |
| **`caudal_m3s`** | Number | El caudal medido en la estación, expresado en metros cúbicos por segundo (m³/s). |
| **`fecha_hora_utc`** | String (ISO 8601)| La fecha y hora de la medición en formato estándar UTC. |
| **`nivel_alerta`** | String | Una clasificación simple del riesgo: `verde` (normal), `amarillo` (alerta/precaución), `rojo` (alarma/desborde). |

### `geometry` (Dentro de cada `Feature`)

Esta es la información geográfica de la estación de monitoreo.

| Campo | Tipo | Descripción |
| :--- | :--- | :--- |
| **`type`** | String | El tipo de geometría. Para estas alertas, siempre será `"Point"`. |
| **`coordinates`** | Array | Un array con las coordenadas de la estación de monitoreo en el formato estándar de GeoJSON: **`[longitud, latitud]`**. |