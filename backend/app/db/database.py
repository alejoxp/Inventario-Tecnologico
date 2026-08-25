from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings


class Base(DeclarativeBase):
    """Clase base que registra la metadata de todas las tablas del dominio."""


engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)


def preparar_esquema() -> None:
    """Agrega columnas nuevas en instalaciones existentes sin perder datos."""
    with engine.begin() as connection:
        connection.execute(text("ALTER TABLE equipos ADD COLUMN IF NOT EXISTS marca_detalle VARCHAR(120)"))
        connection.execute(text("ALTER TABLE equipos ADD COLUMN IF NOT EXISTS custodio VARCHAR(150)"))
        connection.execute(text("ALTER TABLE especificaciones_pc ADD COLUMN IF NOT EXISTS cpu_generacion VARCHAR(50)"))
        connection.execute(text("ALTER TABLE especificaciones_pc ADD COLUMN IF NOT EXISTS ram_cantidad_gb INTEGER"))
        connection.execute(text("ALTER TABLE especificaciones_pc ADD COLUMN IF NOT EXISTS ram_tipo VARCHAR(20)"))
        connection.execute(text("ALTER TABLE especificaciones_pc ADD COLUMN IF NOT EXISTS arquitectura VARCHAR(20)"))
        connection.execute(text("ALTER TABLE historial_movimientos ADD COLUMN IF NOT EXISTS ubicacion_anterior_id INTEGER REFERENCES ubicaciones(id) ON DELETE SET NULL"))
        connection.execute(text("ALTER TABLE historial_movimientos ADD COLUMN IF NOT EXISTS ubicacion_nueva_id INTEGER REFERENCES ubicaciones(id) ON DELETE SET NULL"))
        connection.execute(text("ALTER TABLE historial_movimientos ADD COLUMN IF NOT EXISTS custodio_anterior VARCHAR(150)"))
        connection.execute(text("ALTER TABLE historial_movimientos ADD COLUMN IF NOT EXISTS custodio_nuevo VARCHAR(150)"))
        connection.execute(text("ALTER TABLE historial_movimientos ADD COLUMN IF NOT EXISTS fecha_movimiento TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP"))
        connection.execute(text("CREATE INDEX IF NOT EXISTS idx_equipos_marca ON equipos(marca_id)"))
        connection.execute(text("CREATE INDEX IF NOT EXISTS idx_equipos_tipo ON equipos(tipo_id)"))
        connection.execute(text("CREATE INDEX IF NOT EXISTS idx_equipos_ubicacion ON equipos(ubicacion_id)"))
        connection.execute(text("CREATE INDEX IF NOT EXISTS idx_equipos_custodio ON equipos(custodio)"))
        connection.execute(text("CREATE INDEX IF NOT EXISTS idx_historial_equipo ON historial_movimientos(equipo_id)"))
        connection.execute(text("CREATE INDEX IF NOT EXISTS idx_historial_fecha ON historial_movimientos(fecha_movimiento)"))


def get_db() -> Generator[Session, None, None]:
    """Entrega una sesion por request y garantiza su cierre posterior."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
