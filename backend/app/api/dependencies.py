from collections.abc import Callable, Generator

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.database import SessionLocal


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_db() -> Generator[Session, None, None]:
    """Crea una sesion por request y la cierra incluso si ocurre una excepcion."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class VerificadorDeRoles:
    """Dependencia que permite el acceso solo a los roles indicados."""

    def __init__(self, roles_permitidos: list[str]):
        self.roles_permitidos = roles_permitidos

    def __call__(self, token: str = Depends(oauth2_scheme)) -> dict:
        """Decodifica el JWT y compara el rol antes de ejecutar el endpoint."""
        try:
            payload = jwt.decode(
                token,
                settings.secret_key,
                algorithms=[settings.algorithm],
            )
        except JWTError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales invalidas",
                headers={"WWW-Authenticate": "Bearer"},
            ) from exc

        rol = payload.get("rol")
        if not rol or rol not in self.roles_permitidos:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acceso denegado para este rol",
            )
        return payload
