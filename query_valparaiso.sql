-- ============================================================
-- 🌎 Análisis completo de ruta a Valparaíso (autos/camionetas)
-- ============================================================

WITH ruta AS (
  SELECT * FROM pgr_dijkstra(
    'SELECT id, source, target, cost, reverse_cost FROM chile_2po_4pgr',
    331717, 33400, false
  )
),
segmentos AS (
  SELECT
      g.id,
      g.osm_name,
      g.km AS distancia_km,
      g.kmh AS velocidad_max,
      g.geom_way
  FROM chile_2po_4pgr g
  JOIN ruta r ON g.id = r.edge
),
peajes_en_ruta AS (
  SELECT DISTINCT
      p.id AS peaje_id,
      p.nombre,
      p.tipo,
      p.concesionaria,
      p.tramo,
      t.categoria_vehiculo,
      t.tipo_tarifa,
      t.precio,
      p.geom
  FROM peajes p
  JOIN tarifas_peaje t ON t.peaje_id = p.id
  WHERE t.categoria_vehiculo = 'autos_y_camionetas'
    AND EXISTS (
      SELECT 1
      FROM segmentos s
      WHERE ST_DWithin(p.geom::geography, s.geom_way::geography, 300)
    )
),
consumo AS (
  SELECT
    SUM(distancia_km)::numeric AS total_km,
    (SELECT consumo_mixto_kml::numeric FROM versiones WHERE id = 1) AS km_por_litro
  FROM segmentos
),
prom_precio AS (
  SELECT AVG(precio_gasolina_95)::numeric AS precio
  FROM bencineras
  WHERE precio_gasolina_95 IS NOT NULL
),
peajes_sum AS (
  SELECT COALESCE(SUM(precio), 0)::numeric AS total_peajes
  FROM peajes_en_ruta
),
resumen AS (
  SELECT
    c.total_km,
    ROUND(c.total_km / NULLIF(c.km_por_litro, 0), 2) AS litros_necesarios,
    ROUND((c.total_km / NULLIF(c.km_por_litro, 0)) * pp.precio, 0) AS costo_combustible_aprox,
    ps.total_peajes AS costo_peajes,
    ROUND((c.total_km / NULLIF(c.km_por_litro, 0)) * pp.precio + ps.total_peajes, 0) AS costo_total_estimado
  FROM consumo c
  CROSS JOIN prom_precio pp
  CROSS JOIN peajes_sum ps
)
SELECT jsonb_build_object(
  'resumen', (
    SELECT jsonb_build_object(
      'distancia_km', total_km,
      'litros_necesarios', litros_necesarios,
      'costo_combustible_aprox', costo_combustible_aprox,
      'costo_peajes', costo_peajes,
      'costo_total_estimado', costo_total_estimado
    )
    FROM resumen
  ),
  'ruta', (
    SELECT jsonb_agg(
      jsonb_build_object(
        'id', s.id,
        'nombre_via', s.osm_name,
        'distancia_km', s.distancia_km,
        'velocidad_max', s.velocidad_max,
        'geometry', ST_AsGeoJSON(s.geom_way)::jsonb
      )
    )
    FROM segmentos s
  ),
  'peajes', (
    SELECT jsonb_agg(
      jsonb_build_object(
        'id', p.peaje_id,
        'nombre', p.nombre,
        'tipo', p.tipo,
        'concesionaria', p.concesionaria,
        'tramo', p.tramo,
        'tarifa', p.precio,
        'geometry', ST_AsGeoJSON(p.geom)::jsonb
      )
    )
    FROM peajes_en_ruta p
  )
) AS resultado_json;
