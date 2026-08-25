# Inventario Tecnologico Fundacite Sucre

Aplicacion para gestionar el inventario de equipos de la Coordinacion de Telematica.

## Requisitos

- Docker Desktop con Compose habilitado.

## Inicio

Desde esta carpeta:

```powershell
docker compose up -d
```

Abrir:

- Frontend: http://localhost:5173
- API y documentacion: http://localhost:8000/docs
- Estado del backend: http://localhost:8000/health

PostgreSQL se publica en el puerto local `5433`; dentro de Docker usa `5432`.

## Usuario inicial

El primer arranque crea el usuario definido en `.env`:

- Usuario: `admin`
- Contraseña: `admin123_cambiar`

Cambiar estos valores antes de usar el sistema en un entorno real.

## Funcionalidades

- Autenticacion OAuth2 con JWT y roles.
- Rol `TECNICO` para registrar y editar equipos durante los controles de Telematica.
- Listado y busqueda por bien nacional o MAC.
- Busqueda por bien nacional, MAC, nombre del custodio, oficina, marca y modelo.
- Alta, edicion y eliminacion de equipos.
- Carga múltiple de computadoras con oficina y custodio por fila.
- Especificaciones de CPU y RAM para Laptop, CPU y Servidor.
- PostgreSQL con relaciones, restricciones y persistencia Docker.
- Historial de movimientos de ubicación/custodia y auditoría del ciclo de vida.
- Custodio registrado como nombre de texto, sin tabla adicional de personas.
- Ubicaciones institucionales configuradas para las unidades de Fundacite Sucre.
- El custodio se registra directamente como nombre de texto en cada equipo.
- Estados controlados: `Operativo`, `Dañado`, `En Reparación` y `Desincorporado`.
