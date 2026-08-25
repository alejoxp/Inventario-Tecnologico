# Imagen Node compatible con las versiones actuales de Vite y Rolldown.
FROM node:20-alpine

# Directorio donde se monta el frontend.
WORKDIR /app

# Copia las dependencias antes del codigo para reutilizar la cache.
COPY package*.json ./
RUN npm install

# Copia el resto de la aplicacion.
COPY . .
