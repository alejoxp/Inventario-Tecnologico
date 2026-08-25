from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class Rol(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    usuarios: Mapped[list["UsuarioSistema"]] = relationship(back_populates="rol")


class UsuarioSistema(Base):
    __tablename__ = "usuarios_sistema"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    # RESTRICT conserva usuarios que aun dependan de un rol existente.
    rol_id: Mapped[int] = mapped_column(ForeignKey("roles.id", ondelete="RESTRICT"), nullable=False)
    rol: Mapped[Rol] = relationship(back_populates="usuarios")


class Marca(Base):
    __tablename__ = "marcas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    equipos: Mapped[list["Equipo"]] = relationship(back_populates="marca")


class TipoEquipo(Base):
    __tablename__ = "tipos_equipo"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    equipos: Mapped[list["Equipo"]] = relationship(back_populates="tipo")


class Ubicacion(Base):
    __tablename__ = "ubicaciones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    equipos: Mapped[list["Equipo"]] = relationship(back_populates="ubicacion")


class Equipo(Base):
    __tablename__ = "equipos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    bien_nacional: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    serial: Mapped[str | None] = mapped_column(String(120), unique=True, nullable=True)
    mac: Mapped[str | None] = mapped_column(String(17), unique=True, nullable=True)
    modelo: Mapped[str | None] = mapped_column(String(120), nullable=True)
    marca_detalle: Mapped[str | None] = mapped_column(String(120), nullable=True)
    estado: Mapped[str] = mapped_column(String(30), default="Operativo", nullable=False)
    observaciones: Mapped[str | None] = mapped_column(Text, nullable=True)
    custodio: Mapped[str | None] = mapped_column(String(150), nullable=True)
    # RESTRICT evita borrar una marca que todavía está referenciada por equipos.
    marca_id: Mapped[int] = mapped_column(ForeignKey("marcas.id", ondelete="RESTRICT"), nullable=False)
    # RESTRICT evita borrar un tipo mientras existan equipos de ese tipo.
    tipo_id: Mapped[int] = mapped_column(ForeignKey("tipos_equipo.id", ondelete="RESTRICT"), nullable=False)
    # RESTRICT evita perder la trazabilidad de equipos asignados a la ubicación.
    ubicacion_id: Mapped[int] = mapped_column(ForeignKey("ubicaciones.id", ondelete="RESTRICT"), nullable=False)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    __table_args__ = (
        CheckConstraint("estado IN ('Operativo', 'Dañado', 'En Reparación', 'Desincorporado')", name="chk_estado_equipo"),
    )

    marca: Mapped[Marca] = relationship(back_populates="equipos")
    tipo: Mapped[TipoEquipo] = relationship(back_populates="equipos")
    ubicacion: Mapped[Ubicacion] = relationship(back_populates="equipos")
    especificaciones: Mapped["EspecificacionesPC | None"] = relationship(
        back_populates="equipo",
        uselist=False,
        cascade="all, delete-orphan",
    )
    movimientos: Mapped[list["HistorialMovimiento"]] = relationship(
        back_populates="equipo",
        cascade="all, delete-orphan",
    )


class EspecificacionesPC(Base):
    __tablename__ = "especificaciones_pc"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    equipo_id: Mapped[int] = mapped_column(
        # CASCADE elimina las especificaciones huérfanas al eliminar su equipo.
        ForeignKey("equipos.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    cpu: Mapped[str] = mapped_column(String(120), nullable=False)
    cpu_generacion: Mapped[str | None] = mapped_column(String(50), nullable=True)
    ram: Mapped[str] = mapped_column(String(50), nullable=False)
    ram_cantidad_gb: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ram_tipo: Mapped[str | None] = mapped_column(String(20), nullable=True)
    arquitectura: Mapped[str | None] = mapped_column(String(20), nullable=True)
    almacenamiento: Mapped[str | None] = mapped_column(String(100), nullable=True)
    sistema_operativo: Mapped[str | None] = mapped_column(String(100), nullable=True)
    __table_args__ = (
        CheckConstraint("ram_cantidad_gb IS NULL OR ram_cantidad_gb > 0", name="chk_ram_positiva"),
    )

    equipo: Mapped[Equipo] = relationship(back_populates="especificaciones")


class HistorialMovimiento(Base):
    __tablename__ = "historial_movimientos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    equipo_id: Mapped[int] = mapped_column(
        # CASCADE elimina el historial dependiente junto con el equipo archivado.
        ForeignKey("equipos.id", ondelete="CASCADE"),
        nullable=False,
    )
    ubicacion_anterior_id: Mapped[int | None] = mapped_column(ForeignKey("ubicaciones.id", ondelete="SET NULL"), nullable=True)
    ubicacion_nueva_id: Mapped[int | None] = mapped_column(ForeignKey("ubicaciones.id", ondelete="SET NULL"), nullable=True)
    custodio_anterior: Mapped[str | None] = mapped_column(String(150), nullable=True)
    custodio_nuevo: Mapped[str | None] = mapped_column(String(150), nullable=True)
    fecha_movimiento: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    motivo: Mapped[str] = mapped_column(Text, nullable=False)

    equipo: Mapped[Equipo] = relationship(back_populates="movimientos")


class AuditoriaEquipo(Base):
    """Registro inmutable de cambios y tentativas de baja del inventario."""

    __tablename__ = "auditoria_equipos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    equipo_id: Mapped[int] = mapped_column(Integer, nullable=False)
    accion: Mapped[str] = mapped_column(String(20), nullable=False)
    datos_anteriores: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    datos_nuevos: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    fecha_evento: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    usuario_db: Mapped[str] = mapped_column(String(50), server_default=func.current_user(), nullable=False)
