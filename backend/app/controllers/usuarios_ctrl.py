from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import generar_hash
from app.models import models
from app.schemas import schemas


def listar_usuarios(db: Session) -> list[models.UsuarioSistema]:
    """Carga usuarios junto con su rol para la tabla administrativa."""
    consulta = select(models.UsuarioSistema).join(models.UsuarioSistema.rol).order_by(models.UsuarioSistema.username)
    return list(db.scalars(consulta).all())


def crear_usuario(db: Session, datos: schemas.UsuarioCreate) -> models.UsuarioSistema:
    """Crea una cuenta almacenando solo el hash de su password."""
    rol = db.get(models.Rol, datos.rol_id)
    if not rol:
        raise ValueError("El rol seleccionado no existe")
    usuario = models.UsuarioSistema(
        username=datos.username,
        password_hash=generar_hash(datos.password),
        rol=rol,
    )
    db.add(usuario)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ValueError("El nombre de usuario ya existe") from exc
    db.refresh(usuario)
    return usuario


def cambiar_rol(db: Session, usuario: models.UsuarioSistema, rol_id: int) -> models.UsuarioSistema:
    """Cambia el rol validando que la nueva referencia exista."""
    rol = db.get(models.Rol, rol_id)
    if not rol:
        raise ValueError("El rol seleccionado no existe")
    usuario.rol = rol
    db.commit()
    db.refresh(usuario)
    return usuario


def eliminar_usuario(db: Session, usuario_id: int, username_solicitante: str) -> None:
    """Elimina una cuenta de usuario validando reglas de seguridad."""
    usuario = db.get(models.UsuarioSistema, usuario_id)
    if not usuario:
        raise ValueError("El usuario no existe")

    if usuario.username == username_solicitante:
        raise ValueError("No puede eliminar su propia cuenta en sesión")

    if usuario.rol.nombre == "SUPERADMIN":
        total_superadmins = db.scalar(
            select(func.count(models.UsuarioSistema.id))
            .join(models.UsuarioSistema.rol)
            .where(models.Rol.nombre == "SUPERADMIN")
        )
        if total_superadmins and total_superadmins <= 1:
            raise ValueError("No se puede eliminar el único superadministrador del sistema")

    db.delete(usuario)
    db.commit()