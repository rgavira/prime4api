# ⚡ PRIME4API

**Motor de cálculo y evaluación de datasheets de APIs.**

PRIME4API es una API REST construida con FastAPI que permite modelar y evaluar los límites de uso (rates y quotas) definidos en los datasheets de APIs. Proporciona herramientas para calcular capacidades, tiempos mínimos y umbrales de agotamiento a partir de planes de uso acotados (*Bounded Rates*).

---

## 📐 Arquitectura

```
app/
├── main.py                          # Punto de entrada FastAPI
├── engine/                          # Motor de cálculo
│   ├── time_models.py               # TimeUnit, TimeDuration
│   └── evaluators/
│       ├── bounded_rate.py          # BoundedRate (core)
│       ├── rate_evaluator.py        # Evaluador de rates
│       └── quota_evaluator.py       # Evaluador de quotas
├── models/                          # Modelos de datos (Pydantic)
│   ├── rate.py                      # Rate
│   └── quota.py                     # Quota
├── schemas/                         # Schemas de request/response
│   └── basic_operations.py          # BoundedRateRequest, MinTimeResponse
├── services/                        # Lógica de negocio
│   └── basic_operations_service.py  # BasicOperationsService
├── routers/                         # Endpoints
│   └── bounded_rate/
│       └── basic_operations.py      # POST /min-time
└── utils/
    └── time_utils.py                # Utilidades de tiempo
```

---

## 🚀 Despliegue

### Opción 1: Docker (recomendado)

> Solo necesitas **Docker** instalado.

```bash
# 1. Clonar el repositorio
git clone https://github.com/API-TaskForce/prime4api.git
cd prime4api

# 2. Levantar el contenedor
docker compose up -d

# 3. Verificar que está corriendo
curl http://localhost:8000
# {"status": "ok", "message": "PRIME4API is alive and ready."}
```

Para parar el servicio:
```bash
docker compose down
```

Para reconstruir tras cambios:
```bash
docker compose up -d --build
```

### Opción 2: Desarrollo local (con uv)

> Necesitas **Python 3.10+** y [**uv**](https://docs.astral.sh/uv/).

```bash
# 1. Clonar el repositorio
git clone https://github.com/API-TaskForce/prime4api.git
cd prime4api

# 2. Instalar dependencias
uv sync

# 3. Lanzar en modo desarrollo
uv run uvicorn app.main:app --reload
```

---

## 📖 Documentación interactiva

Una vez levantada la API, accede a la documentación Swagger:

- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 🔌 Endpoints

### Health Check

```
GET /
```
```json
{"status": "ok", "message": "PRIME4API is alive and ready."}
```

### Calcular tiempo mínimo

```
POST /api/v1/bounded-rate/min-time?capacity_goal={n}
```

Calcula el tiempo mínimo necesario para alcanzar un objetivo de capacidad dado un plan de rates y/o quotas.

**Request body:**
```json
{
  "rate": {
    "value": 100,
    "unit": "req",
    "period": "1h"
  },
  "quota": {
    "value": 1000,
    "unit": "req",
    "period": "1day"
  }
}
```

> Tanto `rate` como `quota` son opcionales, pero al menos uno debe estar presente. También aceptan listas para múltiples rates/quotas.

**Respuesta:**
```json
{
  "capacity_goal": 500,
  "min_time": "4h"
}
```

**Ejemplos con curl:**

```bash
# Rate + Quota
curl -X POST "http://localhost:8000/api/v1/bounded-rate/min-time?capacity_goal=500" \
  -H "Content-Type: application/json" \
  -d '{"rate": {"value": 100, "unit": "req", "period": "1h"}, "quota": {"value": 1000, "unit": "req", "period": "1day"}}'

# Solo Rate
curl -X POST "http://localhost:8000/api/v1/bounded-rate/min-time?capacity_goal=500" \
  -H "Content-Type: application/json" \
  -d '{"rate": {"value": 100, "unit": "req", "period": "1h"}}'

# Solo Quota
curl -X POST "http://localhost:8000/api/v1/bounded-rate/min-time?capacity_goal=500" \
  -H "Content-Type: application/json" \
  -d '{"quota": {"value": 1000, "unit": "req", "period": "1day"}}'
```

---

## 🛠️ Stack tecnológico

| Tecnología | Uso |
|---|---|
| **FastAPI** | Framework web |
| **Pydantic v2** | Validación de datos |
| **NumPy** | Cálculos numéricos |
| **uv** | Gestión de dependencias |
| **Docker** | Contenerización |

---

## 📄 Licencia

Este proyecto es parte del trabajo del equipo **API-TaskForce**.
