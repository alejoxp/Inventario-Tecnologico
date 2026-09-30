from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.api.dependencies import VerificadorDeRoles, get_db
from app.models import models
from app.schemas import schemas


router = APIRouter(prefix="/prestamos", tags=["prestamos"])
roles_gestion = VerificadorDeRoles(["COORDINADOR", "SUPERADMIN"])
roles_devolucion = VerificadorDeRoles(["TECNICO", "COORDINADOR", "SUPERADMIN"])


def _estado_temporal(prestamo: models.Prestamo, ahora: datetime) -> str:
    if prestamo.estado_solicitud == "Finalizada":
        return "Devuelto"
    if prestamo.estado_solicitud == "Rechazada":
        return "Rechazado"
    if prestamo.estado_solicitud == "Pendiente":
        return "Pendiente"
    if prestamo.estado_solicitud == "Aprobada" and ahora > prestamo.fecha_fin:
        return "Olvidado"
    if prestamo.fecha_inicio <= ahora <= prestamo.fecha_fin:
        return "Ocupado"
    if ahora < prestamo.fecha_inicio:
        return "Apartado"
    return "Libre"


def _nombre_equipo(equipo: models.Equipo) -> str:
    return " ".join(filter(None, [equipo.marca.nombre if equipo.marca else None, equipo.modelo, equipo.bien_nacional]))


def _equipos_prestamo(prestamo: models.Prestamo) -> list[models.Equipo]:
    vinculados = [relacion.equipo for relacion in prestamo.equipos if relacion.equipo]
    return vinculados or ([prestamo.equipo] if prestamo.equipo else [])


def _respuesta(prestamo: models.Prestamo) -> schemas.PrestamoResponse:
    equipos = _equipos_prestamo(prestamo)
    ahora = datetime.now(timezone.utc)
    estado_temp = _estado_temporal(prestamo, ahora)
    dias_totales = max(1, (prestamo.fecha_fin - prestamo.fecha_inicio).days)
    dias_restantes = (prestamo.fecha_fin - ahora).days if prestamo.estado_solicitud == "Aprobada" else None
    es_olvidado = (estado_temp == "Olvidado")

    return schemas.PrestamoResponse(
        id=prestamo.id,
        equipo_id=prestamo.equipo_id,
        custodio_solicitante=prestamo.custodio_solicitante,
        fecha_inicio=prestamo.fecha_inicio,
        fecha_fin=prestamo.fecha_fin,
        estado_solicitud=prestamo.estado_solicitud,
        aprobado_por_usuario_id=prestamo.aprobado_por_usuario_id,
        motivo_uso=prestamo.motivo_uso,
        estado_temporal_equipo=estado_temp,
        equipo_nombre=_nombre_equipo(equipos[0]) if equipos else "Sin equipo",
        equipos_ids=[equipo.id for equipo in equipos],
        equipos_nombres=[_nombre_equipo(equipo) for equipo in equipos],
        actividad=prestamo.actividad or prestamo.motivo_uso,
        descripcion=prestamo.descripcion,
        observaciones=prestamo.observaciones,
        dias=dias_totales,
        dias_restantes=dias_restantes,
        es_olvidado=es_olvidado,
        aprobador_username=prestamo.aprobador.username if prestamo.aprobador else None,
    )


def _hay_solapamiento(db: Session, equipo_ids: list[int], datos: schemas.PrestamoCreate) -> bool:
    for equipo_id in equipo_ids:
        conflicto_antiguo = db.scalar(select(models.Prestamo.id).where(
            models.Prestamo.equipo_id == equipo_id,
            models.Prestamo.estado_solicitud.in_(["Pendiente", "Aprobada"]),
            models.Prestamo.fecha_inicio < datos.fecha_fin,
            models.Prestamo.fecha_fin > datos.fecha_inicio,
        ))
        conflicto_nuevo = db.scalar(select(models.PrestamoEquipo.id).join(models.Prestamo).where(
            models.PrestamoEquipo.equipo_id == equipo_id,
            models.Prestamo.estado_solicitud.in_(["Pendiente", "Aprobada"]),
            models.Prestamo.fecha_inicio < datos.fecha_fin,
            models.Prestamo.fecha_fin > datos.fecha_inicio,
        ))
        if conflicto_antiguo or conflicto_nuevo:
            return True
    return False


def _consulta_prestamo():
    return select(models.Prestamo).options(
        joinedload(models.Prestamo.equipo).joinedload(models.Equipo.marca),
        joinedload(models.Prestamo.equipos).joinedload(models.PrestamoEquipo.equipo).joinedload(models.Equipo.marca),
        joinedload(models.Prestamo.aprobador),
    )


@router.post("", response_model=schemas.PrestamoResponse, status_code=status.HTTP_201_CREATED)
def crear_prestamo(
    datos: schemas.PrestamoCreate,
    db: Session = Depends(get_db),
    auth_user: dict = Depends(VerificadorDeRoles(["CONSULTA", "TECNICO", "COORDINADOR", "SUPERADMIN"])),
) -> schemas.PrestamoResponse:
    if datos.fecha_fin <= datos.fecha_inicio:
        raise HTTPException(status_code=422, detail="La fecha final debe ser posterior a la inicial")
    if datos.custodio_solicitante != auth_user.get("sub"):
        raise HTTPException(status_code=403, detail="La solicitud debe pertenecer al usuario autenticado")
    equipo_ids = list(dict.fromkeys(datos.equipos_ids or ([datos.equipo_id] if datos.equipo_id else [])))
    if not equipo_ids:
        raise HTTPException(status_code=422, detail="Debe seleccionar al menos un equipo")
    usuario = db.scalar(select(models.UsuarioSistema).where(models.UsuarioSistema.username == auth_user.get("sub")))
    equipos = list(db.scalars(select(models.Equipo).where(models.Equipo.id.in_(equipo_ids))).all())
    if len(equipos) != len(equipo_ids) or not usuario:
        raise HTTPException(status_code=404, detail="Equipo o usuario no encontrado")
    if any(equipo.estado == "Desincorporado" for equipo in equipos):
        raise HTTPException(status_code=409, detail="El equipo no está disponible para préstamos")
    if _hay_solapamiento(db, equipo_ids, datos):
        raise HTTPException(status_code=409, detail="El equipo ya tiene una solicitud en ese rango")
    rol_actual = auth_user.get("rol")
    estado_deseado = datos.estado_solicitud or "Pendiente"
    aprobador_id = None
    if estado_deseado == "Aprobada" and rol_actual in ["TECNICO", "COORDINADOR", "SUPERADMIN"]:
        estado_deseado = "Aprobada"
        aprobador_id = usuario.id
    else:
        estado_deseado = "Pendiente"

    prestamo = models.Prestamo(
        equipo_id=equipo_ids[0],
        custodio_solicitante=datos.custodio_solicitante,
        custodio_solicitante_id=usuario.id,
        fecha_inicio=datos.fecha_inicio,
        fecha_fin=datos.fecha_fin,
        estado_solicitud=estado_deseado,
        aprobado_por_usuario_id=aprobador_id,
        motivo_uso=datos.motivo_uso or datos.actividad,
        actividad=datos.actividad,
        descripcion=datos.descripcion,
        observaciones=datos.observaciones,
    )
    db.add(prestamo)
    db.flush()
    db.add_all([models.PrestamoEquipo(prestamo_id=prestamo.id, equipo_id=equipo_id) for equipo_id in equipo_ids])
    db.commit()
    db.refresh(prestamo)
    prestamo = db.scalar(_consulta_prestamo().where(models.Prestamo.id == prestamo.id))
    return _respuesta(prestamo)


@router.get("", response_model=list[schemas.PrestamoResponse])
def listar_prestamos(
    db: Session = Depends(get_db),
    _auth_user: dict = Depends(VerificadorDeRoles(["CONSULTA", "TECNICO", "COORDINADOR", "SUPERADMIN"])),
) -> list[schemas.PrestamoResponse]:
    prestamos = db.scalars(_consulta_prestamo().order_by(models.Prestamo.fecha_inicio.desc())).unique().all()
    return [_respuesta(prestamo) for prestamo in prestamos]


@router.get("/calendario/eventos", response_model=list[schemas.PrestamoCalendarioResponse])
def eventos_calendario(
    db: Session = Depends(get_db),
    _auth_user: dict = Depends(VerificadorDeRoles(["CONSULTA", "TECNICO", "COORDINADOR", "SUPERADMIN"])),
) -> list[schemas.PrestamoCalendarioResponse]:
    prestamos = db.scalars(_consulta_prestamo()).unique().all()
    colores = {
        "Pendiente": "#d97706",
        "Aprobada": "#15803d",
        "Rechazada": "#b91c1c",
        "Finalizada": "#64748b",
        "Devuelto": "#64748b",
        "Olvidado": "#dc2626",
        "Ocupado": "#2563eb",
        "Apartado": "#0891b2",
        "Libre": "#10b981",
    }
    ahora = datetime.now(timezone.utc)
    return [schemas.PrestamoCalendarioResponse(
        id=prestamo.id,
        title=f"{prestamo.actividad or 'Préstamo'} · {_estado_temporal(prestamo, ahora)}",
        start=prestamo.fecha_inicio,
        end=prestamo.fecha_fin,
        estado=_estado_temporal(prestamo, ahora),
        backgroundColor=colores.get(_estado_temporal(prestamo, ahora), "#2563eb"),
        extendedProps={"estado": _estado_temporal(prestamo, ahora), "custodio": prestamo.custodio_solicitante, "motivo": prestamo.motivo_uso, "actividad": prestamo.actividad, "descripcion": prestamo.descripcion, "observaciones": prestamo.observaciones, "equipo": ", ".join(_nombre_equipo(equipo) for equipo in _equipos_prestamo(prestamo))},
    ) for prestamo in prestamos]


@router.patch("/{prestamo_id}/decision", response_model=schemas.PrestamoResponse)
def decidir_prestamo(
    prestamo_id: int,
    datos: schemas.PrestamoUpdate,
    db: Session = Depends(get_db),
    auth_user: dict = Depends(roles_gestion),
) -> schemas.PrestamoResponse:
    prestamo = db.scalar(_consulta_prestamo().where(models.Prestamo.id == prestamo_id))
    aprobador = db.scalar(select(models.UsuarioSistema).where(models.UsuarioSistema.username == auth_user.get("sub")))
    if not prestamo or not aprobador:
        raise HTTPException(status_code=404, detail="Préstamo o usuario aprobador no encontrado")
    if prestamo.estado_solicitud != "Pendiente":
        raise HTTPException(status_code=409, detail="Solo se pueden decidir solicitudes pendientes")
    if datos.estado_solicitud == "Aprobada":
        conflicto = db.scalar(select(models.Prestamo.id).where(
            models.Prestamo.id != prestamo.id,
            models.Prestamo.equipo_id == prestamo.equipo_id,
            models.Prestamo.estado_solicitud == "Aprobada",
            models.Prestamo.fecha_inicio < prestamo.fecha_fin,
            models.Prestamo.fecha_fin > prestamo.fecha_inicio,
        ))
        if conflicto:
            raise HTTPException(status_code=409, detail="Ya existe otro préstamo aprobado en ese rango")
    prestamo.estado_solicitud = datos.estado_solicitud
    prestamo.aprobado_por_usuario_id = aprobador.id
    db.commit()
    db.refresh(prestamo)
    return _respuesta(prestamo)


@router.patch("/{prestamo_id}/devolver", response_model=schemas.PrestamoResponse)
def devolver_prestamo(
    prestamo_id: int,
    datos: schemas.PrestamoDevolucion,
    db: Session = Depends(get_db),
    _auth_user: dict = Depends(roles_devolucion),
) -> schemas.PrestamoResponse:
    prestamo = db.scalar(_consulta_prestamo().where(models.Prestamo.id == prestamo_id))
    if not prestamo:
        raise HTTPException(status_code=404, detail="Préstamo no encontrado")
    if prestamo.estado_solicitud != "Aprobada":
        raise HTTPException(status_code=409, detail="Solo se pueden devolver préstamos aprobados")
    prestamo.estado_solicitud = "Finalizada"
    if datos.observaciones:
        prestamo.observaciones = datos.observaciones
    db.commit()
    prestamo = db.scalar(_consulta_prestamo().where(models.Prestamo.id == prestamo_id))
    return _respuesta(prestamo)

