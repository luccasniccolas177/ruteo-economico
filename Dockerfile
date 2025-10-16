# Usar una imagen oficial de Python
FROM python:3.11-slim

# Instalar dependencias del sistema, incluyendo osm2pgsql y librerías de PostGIS
RUN apt-get update && apt-get install -y --no-install-recommends \
    osm2pgsql \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Establecer el directorio de trabajo
WORKDIR /app

# Instalar dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar todo el código del proyecto
COPY . .

# Comando que se ejecuta al iniciar el contenedor:
# 1. Corre todo el pipeline ETL con main.py
# 2. Si tiene éxito, inicia el servidor web
CMD ["sh", "-c", "python3 main.py && python3 sitio_web/app.py --host=0.0.0.0"]