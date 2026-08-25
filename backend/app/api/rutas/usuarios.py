from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.api.dependencies import VerificadorDeRoles, get_db
from app.controllers.usuarios_ctrl import cambiar_rol, crear_usuario, listar_usuarios
from app.models import models
from app.schemas import schemas


router = APIRouter(prefix="/usuarios", tags=["usuarios"])
solo_superadmin = Depends(VerificadorDeRoles(["SUPERADMIN"]))


@router.get("/roles", response_model=list[schemas.CatalogoRef], dependencies=[solo_superadmin])
def listar_roles(db: Session = Depends(get_db)) -> list[models.Rol]:
    """Devuelve los roles disponibles para el formulario administrativo."""
    return list(db.scalars(select(models.Rol).order_by(models.Rol.nombre)).all())


@router.get("", response_model=list[schemas.UsuarioResponse], dependencies=[solo_superadmin])
def obtener_usuarios(db: Session = Depends(get_db)) -> list[models.UsuarioSistema]:
    """Lista cuentas sin exponer contrasenas ni hashes."""
    return listar_usuarios(db)


@router.post("", response_model=schemas.UsuarioResponse, status_code=status.HTTP_201_CREATED, dependencies=[solo_superadmin])
def registrar_usuario(datos: schemas.UsuarioCreate, db: Session = Depends(get_db)) -> models.UsuarioSistema:
    """Crea una cuenta con el rol elegido por el superadministrador."""
    try:
        return crear_usuario(db, datos)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.patch("/{usuario_id}/rol", response_model=schemas.UsuarioResponse, dependencies=[solo_superadmin])
def actualizar_rol(usuario_id: int, datos: schemas.UsuarioRolUpdate, db: Session = Depends(get_db)) -> models.UsuarioSistema:
    """Actualiza exclusivamente el rol de una cuenta."""
    usuario = db.scalar(
        select(models.UsuarioSistema)
        .options(joinedload(models.UsuarioSistema.rol))
        .where(models.UsuarioSistema.id == usuario_id)
    )
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    try:
        return cambiar_rol(db, usuario, datos.rol_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc