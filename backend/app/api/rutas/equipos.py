from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.api.dependencies import VerificadorDeRoles, get_db
from app.controllers.equipos_ctrl import actualizar_equipo, crear_equipo, crear_equipos_lote, eliminar_equipo
from app.models import models
from app.schemas import schemas


router = APIRouter(prefix="/equipos", tags=["equipos"])


@router.post(
    "/nuevo",
    response_model=schemas.EquipoResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(VerificadorDeRoles(["TECNICO", "COORDINADOR", "SUPERADMIN"]))],
)
def registrar_equipo(
    equipo_data: schemas.EquipoCreate,
    db: Session = Depends(get_db),
) -> models.Equipo:
    """Registra un equipo para coordinadores y superadministradores."""
    try:
        return crear_equipo(db, equipo_data)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post(
    "/lote",
    response_model=list[schemas.EquipoResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(VerificadorDeRoles(["TECNICO", "COORDINADOR", "SUPERADMIN"]))],
)
def registrar_equipos_lote(
    lote: schemas.EquiposLoteCreate,
    db: Session = Depends(get_db),
) -> list[models.Equipo]:
    """Registra varias computadoras con oficina y custodio por fila."""
    try:
        return crear_equipos_lote(db, lote.equipos)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/", response_model=list[schemas.EquipoResponse])
def listar_equipos(db: Session = Depends(get_db)) -> list[models.Equipo]:
    """Lista equipos cargando relaciones en una consulta para evitar N+1."""
    consulta = (
        select(models.Equipo)
        .options(
            joinedload(models.Equipo.marca),
            joinedload(models.Equipo.tipo),
            joinedload(models.Equipo.ubicacion),
            joinedload(models.Equipo.especificaciones),
        )
        .order_by(models.Equipo.id.desc())
    )
    return list(db.scalars(consulta).unique().all())


@router.get("/{equipo_id}", response_model=schemas.EquipoResponse)
def obtener_equipo(equipo_id: int, db: Session = Depends(get_db)) -> models.Equipo:
    """Obtiene un equipo y sus relaciones para la pantalla de edicion."""
    consulta = (
        select(models.Equipo)
        .options(
            joinedload(models.Equipo.marca),
            joinedload(models.Equipo.tipo),
            joinedload(models.Equipo.ubicacion),
            joinedload(models.Equipo.especificaciones),
        )
        .where(models.Equipo.id == equipo_id)
    )
    equipo = db.scalars(consulta).unique().first()
    if not equipo:
        raise HTTPException(status_code=404, detail="Equipo no encontrado")
    return equipo


@router.put("/{equipo_id}", response_model=schemas.EquipoResponse)
def editar_equipo(
    equipo_id: int,
    equipo_data: schemas.EquipoUpdate,
    db: Session = Depends(get_db),
    _usuario: dict = Depends(VerificadorDeRoles(["TECNICO", "COORDINADOR", "SUPERADMIN"])),
) -> models.Equipo:
    """Modifica un equipo existente y devuelve su estado actualizado."""
    equipo = db.get(models.Equipo, equipo_id)
    if not equipo:
        raise HTTPException(status_code=404, detail="Equipo no encontrado")
    try:
        return actualizar_equipo(db, equipo, equipo_data)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.delete("/{equipo_id}", status_code=status.HTTP_204_NO_CONTENT)
def borrar_equipo(
    equipo_id: int,
    db: Session = Depends(get_db),
    _usuario: dict = Depends(VerificadorDeRoles(["SUPERADMIN"])),
) -> None:
    """Permite eliminar inventario solo al superadministrador."""
    equipo = db.get(models.Equipo, equipo_id)
    if not equipo:
        raise HTTPException(status_code=404, detail="Equipo no encontrado")
    eliminar_equipo(db, equipo)


@router.get("/{equipo_id}/movimientos", response_model=list[schemas.MovimientoResponse])
def listar_movimientos(equipo_id: int, db: Session = Depends(get_db)) -> list[models.HistorialMovimiento]:
    """Consulta los cambios de ubicación y custodia del equipo."""
    return list(db.scalars(select(models.HistorialMovimiento).where(models.HistorialMovimiento.equipo_id == equipo_id).order_by(models.HistorialMovimiento.fecha_movimiento.desc())).all())


@router.get("/{equipo_id}/auditoria", response_model=list[schemas.AuditoriaResponse])
def listar_auditoria(equipo_id: int, db: Session = Depends(get_db)) -> list[models.AuditoriaEquipo]:
    """Consulta el ciclo de vida registrado para auditoría."""
    return list(db.scalars(select(models.AuditoriaEquipo).where(models.AuditoriaEquipo.equipo_id == equipo_id).order_by(models.AuditoriaEquipo.fecha_evento.desc())).all())
