from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
import bcrypt

from app.core.config import settings


def verificar_password(password_plano: str, password_hash: str) -> bool:
    """Compara una contrasena recibida con su hash persistido."""
    return bcrypt.checkpw(password_plano.encode(), password_hash.encode())


def generar_hash(password_plano: str) -> str:
    """Genera el hash que se almacena, nunca la contrasena original."""
    return bcrypt.hashpw(password_plano.encode(), bcrypt.gensalt()).decode()


def crear_token_acceso(subject: str, rol: str) -> str:
    """Firma un JWT con identidad, rol y vencimiento controlado."""
    vencimiento = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    payload = {"sub": subject, "rol": rol, "exp": vencimiento}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def decodificar_token(token: str) -> dict:
    """Valida la firma JWT y devuelve sus claims para autorización."""
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    except JWTError as exc:
        raise ValueError("Token invalido o expirado") from exc
