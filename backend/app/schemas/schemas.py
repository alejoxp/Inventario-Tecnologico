from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class EspecificacionesPCCreate(BaseModel):
    """Datos opcionales de hardware para equipos informaticos."""

    cpu: str = Field(min_length=1, max_length=120)
    cpu_generacion: str | None = Field(default=None, max_length=50)
    ram: str = Field(min_length=1, max_length=50)
    ram_cantidad_gb: int | None = Field(default=None, gt=0)
    ram_tipo: str | None = Field(default=None, max_length=20)
    arquitectura: str | None = Field(default=None, max_length=20)
    almacenamiento: str | None = Field(default=None, max_length=100)
    sistema_operativo: str | None = Field(default=None, max_length=100)


class EquipoCreate(BaseModel):
    """Datos validados para registrar un equipo nuevo."""

    bien_nacional: str = Field(min_length=1, max_length=80)
    serial: str | None = Field(default=None, max_length=120)
    mac: str | None = Field(default=None, max_length=17)
    modelo: str | None = Field(default=None, max_length=120)
    marca_detalle: str | None = Field(default=None, max_length=120)
    estado: str = Field(default="Operativo", pattern="^(Operativo|Dañado|En Reparación|Desincorporado)$")
    observaciones: str | None = None
    marca_id: int
    tipo_id: int
    ubicacion_id: int
    custodio: str | None = Field(default=None, max_length=150)
    movimiento_motivo: str | None = Field(default=None, max_length=500)
    especificaciones: EspecificacionesPCCreate | None = None


class EquipoUpdate(EquipoCreate):
    """Payload completo para modificar un equipo existente."""


class EquiposLoteCreate(BaseModel):
    """Conjunto de equipos que se persiste de forma atomica."""

    equipos: list[EquipoCreate] = Field(min_length=1, max_length=100)


class CatalogoRef(BaseModel):
    """Representacion reducida de una marca, tipo o ubicacion."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str


class EspecificacionesPCResponse(EspecificacionesPCCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int


class EquipoResponse(BaseModel):
    """Respuesta publica de un equipo con sus relaciones cargadas."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    bien_nacional: str
    serial: str | None
    mac: str | None
    modelo: str | None
    marca_detalle: str | None
    estado: str
    observaciones: str | None
    creado_en: datetime
    marca: CatalogoRef
    tipo: CatalogoRef
    ubicacion: CatalogoRef
    custodio: str | None
    especificaciones: EspecificacionesPCResponse | None = None


class MovimientoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    equipo_id: int
    ubicacion_anterior_id: int | None
    ubicacion_nueva_id: int | None
    custodio_anterior: str | None
    custodio_nuevo: str | None
    fecha_movimiento: datetime
    motivo: str


class AuditoriaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    equipo_id: int
    accion: str
    datos_anteriores: dict | None
    datos_nuevos: dict | None
    fecha_evento: datetime
    usuario_db: str


class TokenResponse(BaseModel):
    """Respuesta OAuth2 simplificada para el frontend institucional."""

    access_token: str
    token_type: str = "bearer"
    rol: str


class UsuarioCreate(BaseModel):
    """Datos para crear una cuenta y asignarle un rol institucional."""

    username: str = Field(min_length=3, max_length=80)
    password: str = Field(min_length=8, max_length=72)
    rol_id: int


class UsuarioRolUpdate(BaseModel):
    """Cambio controlado del rol de una cuenta existente."""

    rol_id: int


class UsuarioResponse(BaseModel):
    """Representacion administrativa de un usuario sin exponer su hash."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    rol: CatalogoRef
