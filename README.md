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

## Documentación y Tutorial

- Consulta [TUTORIAL_SISTEMA.txt](file:///c:/Users/Alejandro/Desktop/Nueva%20carpeta/inventario-telematica/TUTORIAL_SISTEMA.txt) para una guía paso a paso de uso y administración.
- Consulta [documentador.TXT](file:///c:/Users/Alejandro/Desktop/Nueva%20carpeta/inventario-telematica/documentador.TXT) para la documentación técnica y arquitectónica completa.

## Funcionalidades

- Autenticacion OAuth2 con JWT y roles (`SUPERADMIN`, `COORDINADOR`, `TECNICO`, `CONSULTA`).
- Login institucional 100% responsivo para móviles, tablets y PCs.
- Panel de búsqueda avanzada con **filtros combinables**:
  - Filtro por **Oficina / Ubicación**.
  - Filtro por **Custodio / Responsable**.
  - Filtro por **Estado** (`Operativo`, `Dañado`, `En Reparación`, `Desincorporado`).
  - Filtro por **Marca** (incluyendo soporte de marca libre "Otro").
  - Búsqueda rápida por texto (Bien Nacional, Serial, MAC, Modelo).
  - Botón de limpieza de filtros y contador reactivo en tiempo real.
- Alta, edición y desincorporación controlada de equipos.
- Carga múltiple de computadoras con oficina y custodio independiente por fila.
- Especificaciones de hardware (CPU, generación, RAM, arquitectura, SO) para Laptop, CPU y Servidor.
- PostgreSQL con relaciones, restricciones, triggers de auditoría inmutable y persistencia Docker (`pgdata`).
- Historial automático de movimientos de ubicación y custodia.
- Panel de gestión de usuarios y roles para el superadministrador.
