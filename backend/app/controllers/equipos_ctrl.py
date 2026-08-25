from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models import models
from app.schemas import schemas


def _datos_equipo(equipo: models.Equipo) -> dict:
    """Genera un snapshot JSON pequeño para auditoría."""
    return {
        "id": equipo.id, "bien_nacional": equipo.bien_nacional, "serial": equipo.serial,
        "marca_id": equipo.marca_id, "modelo": equipo.modelo, "tipo_id": equipo.tipo_id,
        "ubicacion_id": equipo.ubicacion_id, "custodio": equipo.custodio, "estado": equipo.estado,
    }


def _validar_ubicacion_estado(db: Session, estado: str, ubicacion_id: int) -> None:
    """Garantiza que solo los equipos desincorporados lleguen al depósito."""
    ubicacion = db.scalar(select(models.Ubicacion).where(models.Ubicacion.id == ubicacion_id))
    if not ubicacion:
        raise ValueError("La ubicación seleccionada no existe")
    es_deposito = ubicacion.nombre == "Deposito"
    if (estado == "Desincorporado") != es_deposito:
        raise ValueError("Deposito solo puede usarse con estado Desincorporado")


def crear_equipo(db: Session, equipo_data: schemas.EquipoCreate) -> models.Equipo:
    """Persiste un equipo y sus especificaciones como una sola transaccion."""
    _validar_ubicacion_estado(db, equipo_data.estado, equipo_data.ubicacion_id)
    equipo = models.Equipo(
        bien_nacional=equipo_data.bien_nacional,
        serial=equipo_data.serial,
        mac=equipo_data.mac,
        modelo=equipo_data.modelo,
        marca_detalle=equipo_data.marca_detalle,
        custodio=equipo_data.custodio,
        estado=equipo_data.estado,
        observaciones=equipo_data.observaciones,
        marca_id=equipo_data.marca_id,
        tipo_id=equipo_data.tipo_id,
        ubicacion_id=equipo_data.ubicacion_id,
    )
    db.add(equipo)
    db.flush()

    if equipo_data.especificaciones:
        equipo.especificaciones = models.EspecificacionesPC(
            equipo_id=equipo.id,
            **equipo_data.especificaciones.model_dump(),
        )

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ValueError("El bien nacional, serial o MAC ya existe") from exc

    db.add(models.AuditoriaEquipo(equipo_id=equipo.id, accion="INGRESO", datos_nuevos=_datos_equipo(equipo)))
    db.commit()
    db.refresh(equipo)
    return equipo


def crear_equipos_lote(db: Session, equipos_data: list[schemas.EquipoCreate]) -> list[models.Equipo]:
    """Registra el lote completo o revierte todas sus filas ante un error."""
    equipos = []
    try:
        for equipo_data in equipos_data:
            _validar_ubicacion_estado(db, equipo_data.estado, equipo_data.ubicacion_id)
            equipo = models.Equipo(
                bien_nacional=equipo_data.bien_nacional,
                serial=equipo_data.serial,
                mac=equipo_data.mac,
                modelo=equipo_data.modelo,
                marca_detalle=equipo_data.marca_detalle,
                custodio=equipo_data.custodio,
                estado=equipo_data.estado,
                observaciones=equipo_data.observaciones,
                marca_id=equipo_data.marca_id,
                tipo_id=equipo_data.tipo_id,
                ubicacion_id=equipo_data.ubicacion_id,
            )
            db.add(equipo)
            db.flush()
            if equipo_data.especificaciones:
                equipo.especificaciones = models.EspecificacionesPC(
                    equipo_id=equipo.id,
                    **equipo_data.especificaciones.model_dump(),
                )
            db.add(models.AuditoriaEquipo(equipo_id=equipo.id, accion="INGRESO", datos_nuevos=_datos_equipo(equipo)))
            equipos.append(equipo)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ValueError("El lote contiene un bien nacional, serial o MAC duplicado") from exc
    for equipo in equipos:
        db.refresh(equipo)
    return equipos


def actualizar_equipo(db: Session, equipo: models.Equipo, equipo_data: schemas.EquipoUpdate) -> models.Equipo:
    """Actualiza campos del equipo y reemplaza sus especificaciones atomicas."""
    _validar_ubicacion_estado(db, equipo_data.estado, equipo_data.ubicacion_id)
    datos_anteriores = _datos_equipo(equipo)
    datos = equipo_data.model_dump(exclude={"especificaciones", "movimiento_motivo"})
    for campo, valor in datos.items():
        setattr(equipo, campo, valor)
    if equipo_data.especificaciones:
        especificaciones = equipo_data.especificaciones.model_dump()
        if equipo.especificaciones:
            for campo, valor in especificaciones.items():
                setattr(equipo.especificaciones, campo, valor)
        else:
            equipo.especificaciones = models.EspecificacionesPC(**especificaciones)
    elif equipo.especificaciones:
        equipo.especificaciones = None
    if datos_anteriores["ubicacion_id"] != equipo.ubicacion_id or datos_anteriores["custodio"] != equipo.custodio:
        db.add(models.HistorialMovimiento(
            equipo_id=equipo.id,
            ubicacion_anterior_id=datos_anteriores["ubicacion_id"],
            ubicacion_nueva_id=equipo.ubicacion_id,
            custodio_anterior=datos_anteriores["custodio"],
            custodio_nuevo=equipo.custodio,
            motivo=equipo_data.movimiento_motivo or "Actualización de asignación",
        ))
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ValueError("El bien nacional, serial o MAC ya existe") from exc
    db.add(models.AuditoriaEquipo(equipo_id=equipo.id, accion="MODIFICACION", datos_anteriores=datos_anteriores, datos_nuevos=_datos_equipo(equipo)))
    db.commit()
    db.refresh(equipo)
    return equipo


def eliminar_equipo(db: Session, equipo: models.Equipo) -> None:
    """Registra la tentativa y desincorpora sin destruir la trazabilidad."""
    anterior = _datos_equipo(equipo)
    equipo.estado = "Desincorporado"
    deposito = db.scalar(select(models.Ubicacion).where(models.Ubicacion.nombre == "Deposito"))
    if deposito:
        equipo.ubicacion_id = deposito.id
    db.add(models.AuditoriaEquipo(equipo_id=equipo.id, accion="INTENTO_BORRADO", datos_anteriores=anterior, datos_nuevos=_datos_equipo(equipo)))
    db.commit()
