from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.models import models
from app.schemas.schemas import CatalogoRef


router = APIRouter(prefix="/catalogos", tags=["catalogos"])


@router.get("")
def listar_catalogos(db: Session = Depends(get_db)) -> dict[str, list[CatalogoRef]]:
    """Entrega las opciones necesarias para el formulario de equipos."""
    return {
        "marcas": [CatalogoRef.model_validate(item) for item in db.scalars(select(models.Marca).order_by(models.Marca.nombre)).all()],
        "tipos": [CatalogoRef.model_validate(item) for item in db.scalars(select(models.TipoEquipo).order_by(models.TipoEquipo.nombre)).all()],
        "ubicaciones": [CatalogoRef.model_validate(item) for item in db.scalars(select(models.Ubicacion).order_by(models.Ubicacion.nombre)).all()],
    }
