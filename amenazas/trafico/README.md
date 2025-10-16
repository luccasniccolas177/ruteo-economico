# Estructura del Archivo `transformed_congestion_[fecha].json`

## Descripción General 📝

Este archivo JSON contiene una "fotografía" del estado del tráfico en segmentos de ruta predefinidos dentro de Santiago. Los datos son extraídos de la **API Directions de Google** y procesados para calcular una métrica de congestión.

El propósito de este archivo en el contexto del proyecto es cumplir con el requisito de un proceso ETL para la amenaza de "congestión". En una aplicación final en tiempo real, estos datos se consultarían directamente a la API en el momento de la solicitud de ruta.

## Formato del Archivo 📄

El archivo es un **Array de Objetos JSON**. Cada objeto representa un "tramo" o segmento de ruta analizado y contiene la siguiente estructura:

### Ejemplo de un Objeto de Tramo

```json
{
  "nombre_tramo": "Alameda (Poniente a Oriente)",
  "tiempo_ideal_seg": 650,
  "tiempo_real_seg": 980,
  "factor_congestion": 0.5077,
  "polyline_google": "hl`~F|rwqL....(texto muy largo)...",
  "fecha_medicion": "2025-10-15T22:15:30.123456"
}
```

---

### Descripción de Campos 🔎

| Campo | Tipo de Dato | Descripción |
| :--- | :--- | :--- |
| `nombre_tramo` | String | Nombre descriptivo del segmento de ruta analizado. Ej: "Costanera Norte (Oriente a Poniente)". |
| `tiempo_ideal_seg` | Integer | El tiempo de viaje estimado **sin considerar el tráfico** actual, en segundos. Corresponde al valor `duration` de la API de Google. |
| `tiempo_real_seg` | Integer | El tiempo de viaje estimado **incluyendo las condiciones de tráfico** en el momento de la consulta, en segundos. Corresponde al valor `duration_in_traffic`. |
| `factor_congestion` | Number | Un índice calculado que representa el nivel de congestión. Se calcula como `(tiempo_real - tiempo_ideal) / tiempo_ideal`. Un valor de **0** indica tráfico fluido, **0.5** indica que el viaje toma un 50% más de tiempo, y **1.0** indica que toma el doble de tiempo. |
| `polyline_google` | String | Una cadena de texto codificada que representa la geometría de la ruta del tramo. Es muy útil para dibujar la ruta en un mapa (como Leaflet o Google Maps) sin necesidad de almacenar todas las coordenadas. |
| `fecha_medicion` | String (ISO 8601) | La fecha y hora exactas en que se realizó la consulta a la API de Google, indicando la vigencia de los datos de tráfico. |