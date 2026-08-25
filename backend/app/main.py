from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select

from app.core.config import settings
from app.core.security import generar_hash
from app.db.database import Base, engine, preparar_esquema
from app.db.database import SessionLocal
from app.models import models
from app.api.rutas.equipos import router as equipos_router
from app.api.rutas.auth import router as auth_router
from app.api.rutas.catalogos import router as catalogos_router
from app.api.rutas.usuarios import router as usuarios_router

# Instancia principal de la API que sera descubierta por Uvicorn.
app = FastAPI(
    title="Inventario Tecnologico Fundacite Sucre",
    version="0.1.0",
)

# Permite que la SPA local consuma la API durante el desarrollo.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(equipos_router, prefix="/api")
app.include_router(auth_router, prefix="/api")
app.include_router(catalogos_router, prefix="/api")
app.include_router(usuarios_router, prefix="/api")


@app.on_event("startup")
def initialize_database() -> None:
    """Crea las tablas faltantes para facilitar el primer arranque local."""
    Base.metadata.create_all(bind=engine)
    preparar_esquema()
    db = SessionLocal()
    try:
        valores = {
            models.Rol: ["TECNICO", "COORDINADOR", "SUPERADMIN", "CONSULTA"],
            models.Marca: [
                "Acer", "Asus", "Brother", "Canon", "Dell", "Epson", "HP",
                "Huawei", "Lenovo", "Samsung", "Siragon", "Polo Cientifico", "VIT", "Otro",
            ],
            models.TipoEquipo: [
                "Laptop", "CPU", "Servidor", "Monitor", "Impresora",
                "Mouse", "Raton", "Cornetas", "Webcams", "VideoBeam",
            ],
            models.Ubicacion: [
                "Unidad de Telematica e Innovacion tecnologica",
                "Presidencia",
                "Direccion ejecutiva",
                "Talento Humano",
                "Administracion",
                "Bienes Nacionales",
                "Planificacion y Presupuesto",
                "Oficina de Atencion Al Ciudadano",
                "Prensa y Comunicaciones",
                "Unidad de Programas y Proyectos",
                "Deposito",
            ],
        }
        for modelo, nombres in valores.items():
            existentes = {fila.nombre for fila in db.scalars(select(modelo)).all()}
            for nombre in nombres:
                if nombre not in existentes:
                    db.add(modelo(nombre=nombre))
        db.flush()
        ubicaciones_antiguas = db.scalars(
            select(models.Ubicacion).where(
                models.Ubicacion.nombre.in_(["Oficina de Telematica", "Almacen", "Direccion"])
            )
        ).all()
        for ubicacion in ubicaciones_antiguas:
            if not db.scalar(select(models.Equipo.id).where(models.Equipo.ubicacion_id == ubicacion.id)):
                db.delete(ubicacion)
        db.flush()
        marca_apple = db.scalar(select(models.Marca).where(models.Marca.nombre == "Apple"))
        if marca_apple and not db.scalar(select(models.Equipo.id).where(models.Equipo.marca_id == marca_apple.id)):
            db.delete(marca_apple)
            db.flush()
        rol_admin = db.scalar(select(models.Rol).where(models.Rol.nombre == "SUPERADMIN"))
        usuario = db.scalar(select(models.UsuarioSistema).where(models.UsuarioSistema.username == settings.admin_username))
        if rol_admin and not usuario:
            db.add(models.UsuarioSistema(username=settings.admin_username, password_hash=generar_hash(settings.admin_password), rol=rol_admin))
        elif usuario:
            usuario.password_hash = generar_hash(settings.admin_password)
        db.commit()
    finally:
        db.close()


@app.get("/health", tags=["sistema"])
def health_check() -> dict[str, str]:
    """Confirma que el proceso HTTP del backend esta disponible."""
    return {"status": "ok"}
