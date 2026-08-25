from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import crear_token_acceso, verificar_password
from app.models import models


def autenticar_usuario(db: Session, username: str, password: str) -> tuple[str, str] | None:
    """Busca el usuario y valida su password sin revelar cual dato fallo."""
    usuario = db.scalar(
        select(models.UsuarioSistema)
        .options()
        .where(models.UsuarioSistema.username == username)
    )
    if not usuario or not verificar_password(password, usuario.password_hash):
        return None
    return crear_token_acceso(usuario.username, usuario.rol.nombre), usuario.rol.nombre
