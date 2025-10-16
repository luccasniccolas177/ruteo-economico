-- Archivo: database/schema.sql
-- Descripción: Script para crear la estructura de la base de datos del proyecto de ruteo económico.

-- Habilitar extensiones necesarias si se van a usar funciones geoespaciales más adelante.
-- CREATE EXTENSION IF NOT EXISTS postgis;

-- ========= SECCIÓN 1: METADATA DE VEHÍCULOS =========

-- Tabla para almacenar las marcas de los vehículos (ej. Toyota, Kia, Hyundai).
-- Se crea para normalizar los datos y evitar la repetición de nombres.
CREATE TABLE IF NOT EXISTS marcas (
    id SERIAL PRIMARY KEY,            -- Identificador único autoincremental para cada marca.
    nombre VARCHAR(100) NOT NULL UNIQUE -- Nombre de la marca, debe ser único para no tener duplicados.
);

-- Tabla para almacenar los modelos de los vehículos (ej. Yaris, Sportage, Tucson).
-- Cada modelo pertenece a una marca.
CREATE TABLE IF NOT EXISTS modelos (
    id SERIAL PRIMARY KEY,            -- Identificador único autoincremental para cada modelo.
    marca_id INT NOT NULL,            -- Llave foránea que referencia a la tabla 'marcas'.
    nombre VARCHAR(150) NOT NULL,     -- Nombre del modelo base.

    -- Restricción de llave foránea para asegurar la integridad referencial.
    -- Si una marca se elimina, todos sus modelos asociados también se eliminarán en cascada.
    CONSTRAINT fk_marca
        FOREIGN KEY(marca_id)
        REFERENCES marcas(id)
        ON DELETE CASCADE,

    -- Restricción para asegurar que no exista el mismo nombre de modelo para la misma marca.
    UNIQUE (marca_id, nombre)
);

-- Tabla para almacenar las versiones específicas y sus especificaciones técnicas.
-- Cada versión está asociada a un modelo.
CREATE TABLE IF NOT EXISTS versiones (
    id SERIAL PRIMARY KEY,            -- Identificador único autoincremental para cada versión.
    modelo_id INT NOT NULL,           -- Llave foránea que referencia a la tabla 'modelos'.
    nombre VARCHAR(255) NOT NULL,     -- Nombre de la versión específica (ej. "1.5 GLI MT").

    -- Especificaciones técnicas clave para el cálculo de costos de ruta.
    -- Se usan tipos de datos numéricos para permitir cálculos precisos.
    -- DECIMAL(5, 2) significa hasta 5 dígitos en total, con 2 de ellos después del punto decimal.
    consumo_mixto_kml DECIMAL(5, 2),  -- Consumo mixto en kilómetros por litro.
    consumo_urbano_kml DECIMAL(5, 2), -- Consumo urbano en kilómetros por litro.
    consumo_extraurbano_kml DECIMAL(5, 2), -- Consumo en carretera en kilómetros por litro.
    capacidad_estanque_litros DECIMAL(5, 1), -- Capacidad del estanque de combustible en litros.
    motor_litros DECIMAL(3, 1),       -- Cilindrada del motor en litros.
    transmision VARCHAR(50),          -- Tipo de transmisión (ej. "Mecánica", "Automática").
    traccion VARCHAR(50),             -- Tipo de tracción (ej. "4x2", "AWD").

    -- Restricción de llave foránea. Si un modelo se elimina, todas sus versiones se eliminan.
    CONSTRAINT fk_modelo
        FOREIGN KEY(modelo_id)
        REFERENCES modelos(id)
        ON DELETE CASCADE,

    -- Restricción para que no se repita el mismo nombre de versión para el mismo modelo.
    UNIQUE (modelo_id, nombre)
);

-- Mensaje de finalización para la consola.
\echo ">>> Base de datos para 'ruteo-economico' creada exitosamente."
\echo ">>> Tablas: 'marcas', 'modelos', 'versiones' listas para recibir datos."

-- ========= SECCIÓN 2: METADATA DE ESTACIONES DE SERVICIO =========

-- Habilitar la extensión PostGIS para manejar datos geoespaciales.
-- Es crucial para almacenar y consultar las coordenadas de las estaciones.
-- (Si ya lo tienes de la sección de vehículos, no necesitas repetirlo).
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS pgrouting;
CREATE EXTENSION IF NOT EXISTS hstore;

-- Tabla para almacenar la información de cada estación de servicio (bencinera).
CREATE TABLE IF NOT EXISTS estaciones_servicio (
    id SERIAL PRIMARY KEY,                          -- ID interno autoincremental de la base de datos.
    id_estacion_cne VARCHAR(20) NOT NULL UNIQUE,    -- El 'codigo' único de la CNE (ej. 'co110101'). Se usa para evitar duplicados.
    nombre VARCHAR(255) NOT NULL,                   -- Nombre o razón social de la estación.
    marca VARCHAR(50),                              -- Marca de la distribuidora (ej. 'COPEC', 'Shell').
    direccion VARCHAR(255),                         -- Dirección física de la estación.
    comuna VARCHAR(100),                            -- Comuna donde se ubica.
    region VARCHAR(100),                            -- Región donde se ubica.
    horario VARCHAR(255),                           -- Horario de atención (texto libre).

    -- Columna para la ubicación geoespacial.
    -- GEOMETRY(Point, 4326) es el tipo de dato estándar para coordenadas (longitud, latitud).
    -- El '4326' es el sistema de referencia espacial estándar (WGS 84).
    ubicacion GEOMETRY(Point, 4326)
);

-- Crear un índice espacial en la columna 'ubicacion'.
-- Esto acelera enormemente las búsquedas geográficas (ej. buscar estaciones cercanas a una ruta).
CREATE INDEX IF NOT EXISTS idx_estaciones_ubicacion ON estaciones_servicio USING GIST (ubicacion);


-- Tabla para almacenar los precios de los diferentes combustibles por estación.
-- Se relaciona con la tabla 'estaciones_servicio'.
CREATE TABLE IF NOT EXISTS precios_combustibles (
    id SERIAL PRIMARY KEY,                          -- ID interno autoincremental del precio.
    estacion_id INT NOT NULL,                       -- Llave foránea que referencia el ID de la tabla 'estaciones_servicio'.
    tipo_combustible VARCHAR(50) NOT NULL,          -- Tipo de combustible (ej. 'gasolina_93', 'petroleo_diesel').
    precio INT NOT NULL,                            -- Precio por litro, almacenado como entero.
    fecha_actualizacion TIMESTAMP NOT NULL,         -- Fecha y hora de la última actualización del precio.

    -- Restricción de llave foránea para mantener la integridad de los datos.
    -- Si una estación se elimina, todos sus precios asociados se eliminarán en cascada.
    CONSTRAINT fk_estacion
        FOREIGN KEY(estacion_id)
        REFERENCES estaciones_servicio(id)
        ON DELETE CASCADE,

    -- Restricción para asegurar que solo haya un precio por tipo de combustible en cada estación.
    UNIQUE (estacion_id, tipo_combustible)
);

-- Mensaje de finalización para la consola.
\echo ">>> Tablas para combustibles 'estaciones_servicio' y 'precios_combustibles' creadas/actualizadas."

-- ========= SECCIÓN 3: METADATA DE PEAJES (PÓRTICOS) =========

-- Tabla para almacenar la información de cada pórtico o plaza de peaje.
CREATE TABLE IF NOT EXISTS peajes (
    id SERIAL PRIMARY KEY,                          -- ID interno autoincremental de la base de datos.
    nombre VARCHAR(255) NOT NULL,                   -- Nombre del pórtico o plaza de peaje.
    concesionaria VARCHAR(255),                     -- Nombre de la autopista o concesionaria.
    tipo VARCHAR(50),                               -- Tipo de peaje, ej: 'Troncal', 'Lateral'.

    -- Columna para la ubicación geoespacial del peaje.
    ubicacion GEOMETRY(Point, 4326),

    -- Restricción para asegurar que no haya peajes duplicados por nombre y concesionaria.
    UNIQUE (nombre, concesionaria)
);

-- Crear un índice espacial en la columna 'ubicacion' para acelerar búsquedas geográficas.
CREATE INDEX IF NOT EXISTS idx_peajes_ubicacion ON peajes USING GIST (ubicacion);


-- Tabla para almacenar las diferentes tarifas asociadas a cada peaje.
CREATE TABLE IF NOT EXISTS tarifas_peaje (
    id SERIAL PRIMARY KEY,
    peaje_id INT NOT NULL,                          -- Llave foránea que referencia el ID de la tabla 'peajes'.
    categoria_vehiculo VARCHAR(255) NOT NULL,       -- Descripción de la categoría del vehículo.
    tipo_tarifa VARCHAR(50) NOT NULL,               -- Tipo de tarifa, ej: 'TBFP' (Fuera de Punta), 'TBP' (Punta), 'TS' (Saturación).
    precio NUMERIC(10, 2) NOT NULL,                 -- El costo del peaje. Usamos NUMERIC para valores monetarios.

    -- Restricción de llave foránea. Si un peaje se elimina, sus tarifas también.
    CONSTRAINT fk_peaje
        FOREIGN KEY(peaje_id)
        REFERENCES peajes(id)
        ON DELETE CASCADE
);

\echo ">>> Tablas para peajes 'peajes' y 'tarifas_peaje' creadas/actualizadas."