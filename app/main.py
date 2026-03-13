from fastapi import FastAPI
from app.routers.bounded_rate.basic_operations import router as bounded_rate_router
from app.routers.datasheet import router as datasheet_router

# 1. Instanciamos la aplicación pura
app = FastAPI(
    title="PRIME4API",
    description="Motor de cálculo y evaluación de datasheets de APIs",
    version="0.1.0"
)

# 2. Endpoint de salud (Health Check) - El único permitido en main.py
@app.get("/")
def health_check():
    return {"status": "ok", "message": "PRIME4API is alive and ready."}

# 3. Aquí es donde "enchufaremos" las rutas reales más adelante

app.include_router(datasheet_router, prefix="/api/v1/datasheet", tags=["Datasheets"])
app.include_router(bounded_rate_router, prefix="/api/v1/bounded-rate", tags=["Bounded Rate"])