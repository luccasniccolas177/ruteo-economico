# Usar una imagen oficial de Python como base
FROM python:3.11-slim

# Instalar dependencias del sistema operativo, incluyendo osm2pgsql
RUN apt-get update && apt-get install -y --no-install-recommends \
    osm2pgsql \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Establecer el directorio de trabajo dentro del contenedor
WORKDIR /app

# Instalar las dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar todo el código de tu proyecto al contenedor
COPY . .

# Comando que se ejecuta al iniciar el contenedor:
# 1. Corre el pipeline ETL completo con main.py
# 2. Si tiene éxito (&&), inicia el servidor web
CMD ["sh", "-c", "python3 main.py && python3 sitio_web/app.py"]