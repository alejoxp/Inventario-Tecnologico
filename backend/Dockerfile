# Imagen base ligera con Python para ejecutar la API.
FROM python:3.11-slim

# Evita archivos compilados y mantiene los logs visibles en Docker.
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Directorio compartido con el volumen de desarrollo.
WORKDIR /code

# Dependencias del sistema necesarias para compilar el driver PostgreSQL.
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Instala primero las dependencias para aprovechar la cache de Docker.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia el código de la aplicación al contenedor.
COPY . .
