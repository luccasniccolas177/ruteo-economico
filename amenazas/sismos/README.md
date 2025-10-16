# 🌋 Estructura del Archivo `amenaza_sismos.geojson`

## 📝 Descripción General

Este archivo en formato **GeoJSON** contiene información sobre los **sismos más recientes y relevantes** para el territorio chileno.  
Los datos son obtenidos mediante **web scraping** del **Centro Sismológico Nacional (CSN)**, la fuente oficial de sismología en Chile.

El propósito del archivo es proporcionar una **capa de datos geoespaciales** lista para ser consumida por aplicaciones de mapeo (como **Leaflet**) y visualizar la amenaza sísmica como puntos en un mapa.  
El script de generación **filtra automáticamente los sismos de baja magnitud** para mostrar solo aquellos potencialmente relevantes.

---

## 📄 Formato del Archivo

El archivo es un objeto **`FeatureCollection`** de GeoJSON, que actúa como contenedor estándar para una lista de características geográficas.

La estructura principal contiene una lista (`features`) donde cada elemento es un objeto **`Feature`** que representa un **sismo individual**.

---

## 🌍 Ejemplo de un Objeto `Feature` (Sismo)

```json
{
  "type": "Feature",
  "properties": {
    "tipo_amenaza": "sismo",
    "fuente": "CSN",
    "fecha_local": "2025-10-15 10:37:41",
    "magnitud": 4.2,
    "profundidad_km": 72.0,
    "referencia_geografica": "39 km al NE de Copiapó",
    "url_detalle": "https://www.sismologia.cl/sismicidad/informes/2025/10/321739.html",
    "nivel_alerta": "verde"
  },
  "geometry": {
    "type": "Point",
    "coordinates": [-69.98, -27.11]
  }
}

```
### Objeto Principal
| **Campo**  | **Tipo** | **Descripción**                                                                  |
| ---------- | -------- | -------------------------------------------------------------------------------- |
| `type`     | String   | Siempre será `"FeatureCollection"`.                                              |
| `metadata` | Object   | Contiene información sobre la generación del archivo, como la fecha y la fuente. |
| `features` | Array    | La lista que contiene todos los *Feature* de los sismos.                         |


### Propiedades
| **Campo**               | **Tipo** | **Descripción**                                                                                                  |
| ----------------------- | -------- | ---------------------------------------------------------------------------------------------------------------- |
| `tipo_amenaza`          | String   | Identificador fijo del tipo de amenaza. Siempre será `"sismo"`.                                                  |
| `fuente`                | String   | La institución que reporta el dato. Siempre será `"CSN"`.                                                        |
| `fecha_local`           | String   | Fecha y hora en que ocurrió el sismo en hora local de Chile (formato `YYYY-MM-DD HH:MM:SS`).                     |
| `magnitud`              | Number   | Magnitud del sismo en la escala correspondiente (ej. `4.2`).                                                     |
| `profundidad_km`        | Number   | Profundidad del hipocentro del sismo, medida en kilómetros.                                                      |
| `referencia_geografica` | String   | Descripción textual de la ubicación del epicentro. Ejemplo: `"39 km al NE de Copiapó"`.                          |
| `url_detalle`           | String   | Enlace directo al informe oficial del sismo en [sismologia.cl](https://www.sismologia.cl).                       |
| `nivel_alerta`          | String   | Clasificación simple del riesgo potencial según magnitud: `verde` (menor), `amarillo` (moderado), `rojo` (alto). |


### Geometry
| **Campo**     | **Tipo** | **Descripción**                                                                  |
| ------------- | -------- | -------------------------------------------------------------------------------- |
| `type`        | String   | El tipo de geometría. Para sismos, siempre será `"Point"`.                       |
| `coordinates` | Array    | Coordenadas del epicentro en formato `[longitud, latitud]`, estándar de GeoJSON. |
