from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.controllers.auth_ctrl import autenticar_usuario
from app.schemas.schemas import TokenResponse


router = APIRouter(prefix="/auth", tags=["autenticacion"])


@router.post("/login", response_model=TokenResponse)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> TokenResponse:
    """Acepta formulario OAuth2 y devuelve el JWT junto con el rol."""
    resultado = autenticar_usuario(db, form_data.username, form_data.password)
    if not resultado:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o password incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token, rol = resultado
    return TokenResponse(access_token=token, rol=rol)
