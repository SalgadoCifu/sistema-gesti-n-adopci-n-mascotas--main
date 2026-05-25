# Sistema de Gestión de Adopciones de Mascotas

Backend FastAPI en Python con arquitectura en capas (vertical slice). Proyecto simplificado centrado en la lógica de negocio de solicitudes de adopción.

## Alcance actual

- **Flujo principal**: crear solicitud de adopción (con validaciones de dominio)
- **Regla de negocio**: un adoptante solo puede tener una solicitud activa
- **Base de datos**: PostgreSQL 15+ en Supabase (con soporte `timestamptz`)
- **Autenticación**: pasada por header `X-User-Cedula` (responsabilidad de gateway)

## Estructura del proyecto

```
adopciones_dominio/
├── domain/                    # Reglas y entidades de negocio
│   ├── entities/              # Adoptante, Mascota, SolicitudAdopcion
│   ├── exceptions/            # Errores de dominio
│   └── repositories/          # Contratos abstractos
├── infrastructure/            # Implementación técnica
│   ├── database/              # Conexión y configuración
│   ├── repositories/          # Implementación concreta con DB
│   ├── mappers/               # Mapeo DB ↔ dominio
│   └── tests/                 # Pruebas de conexión e infra
├── application/               # Capa HTTP y casos de uso
│   ├── routers/               # Endpoints FastAPI
│   ├── use_cases/             # Lógica de aplicación
│   ├── dtos.py                # Modelos Pydantic
│   └── dependencies.py        # Inyección de dependencias
├── tests/                     # Pruebas unitarias y de integración
│   ├── application/           # Tests de endpoints
│   └── domain/                # Tests de entidades
└── main.py                    # Punto de entrada FastAPI
```

## Configuración inicial

### 1. Variables de entorno

Crear un archivo `.env` **en la raíz del repo** copiando desde `.env.example`:

```env
# Obligatorio: cadena de conexión a PostgreSQL
DATABASE_URL=postgresql://postgres:PASSWORD@host:5432/postgres

# Opcionales (para integración futura con Supabase SDK)
SUPABASE_URL=https://PROJECT_REF.supabase.co
SUPABASE_KEY=ANON_KEY

# Configuración de aplicación
ENVIRONMENT=development
DEBUG=True
```

**Notas importantes:**
- `DATABASE_URL` es **obligatoria** para que la app funcione
- Si usas Supabase, toma la URL directa de PostgreSQL (no la URL de Supabase API)
- Para pgbouncer/pooler, la URL típica termina en `pooler.supabase.com:6543`
- Asegúrate que la contraseña esté URL-encoded si contiene caracteres especiales
- `.env` está ignorado en `.gitignore` (nunca comitees credenciales)

### 2. Crear entorno virtual

Desde la raíz del repo (PowerShell en Windows):

```powershell
# Crear entorno con Python 3.13
py -3.13 -m venv venv

# Activar
(Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned) ; (& .\venv\Scripts\Activate.ps1)

# Instalar dependencias
pip install -r requirements.txt
```

**En Linux/macOS:**
```bash
python3.13 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Base de datos

- **Motor:** PostgreSQL 15+ (Supabase)
- **Timestamp:** todas las fechas usan `timestamptz` (timezone-aware)
- **Restricciones:** FK en `solicitudes(cedula) → adoptantes(cedula)`
- **Tablas esperadas:** `adopciones`, `mascotas`, `solicitudes`, `usuarios`

Crea al menos un registro en `adoptantes` antes de hacer pruebas:
```sql
INSERT INTO adoptantes (cedula, direccion, telefono, codlocalidad)
VALUES ('1002003001', NULL, NULL, NULL);
```

## Levantar la aplicación

### Desarrollo local

Desde la raíz del repo con entorno activado:

```powershell
# PowerShell (Windows)
uvicorn --env-file .env --app-dir adopciones_dominio main:app --reload --host 0.0.0.0 --port 8000
```

```bash
# Bash (Linux/macOS)
uvicorn --env-file .env --app-dir adopciones_dominio main:app --reload --host 0.0.0.0 --port 8000
```

Luego accede a:
- **Swagger UI:** http://127.0.0.1:8000/docs
- **ReDoc:** http://127.0.0.1:8000/redoc

### Producción (ejemplo)

```bash
uvicorn --env-file .env --app-dir adopciones_dominio main:app --workers 4 --host 0.0.0.0 --port 8000
```

## Pruebas

### Ejecutar suite completa (recomendado)

Desde `adopciones_dominio/`:

```powershell
cd adopciones_dominio
pytest -v                    # Todos los tests con output detallado
pytest -q                    # Modo silencioso
pytest --cov                 # Con cobertura
```

### Pruebas por componente

```powershell
# 1. Domain: lógica de negocio
pytest tests/ -v -k domain

# 2. Application: endpoints y use cases (sin BD real)
pytest tests/application/ -v

# 3. Infrastructure: conexión a BD
pytest infrastructure/tests/ -v
```

**Nota:** Los tests de aplicación usan mocks y no requieren conexión a BD. Los de infraestructura **sí** requieren `.env` configurado.

### Validar conexión a BD (antes de desarrollar)

```powershell
pytest infrastructure/tests/test_connection.py -v
```

Resultado esperado: 2 tests pass (conexión y info de BD).

## Contrato API

**Base URL:** `http://localhost:8000/api/v1`

Todos los endpoints están documentados en **Swagger** (`/docs`) cuando la app está corriendo.

### GET `/mascotas/{codmascota}/disponible`

Consulta si una mascota está disponible para adopción.

**Respuesta 200 - Disponible:**
```json
{
  "disponible": true,
  "codmascota": 1,
  "nombre": "Luna",
  "razon": null
}
```

**Respuesta 200 - No disponible:**
```json
{
  "disponible": false,
  "codmascota": 1,
  "nombre": "Luna",
  "razon": "La mascota tiene una solicitud activa."
}
```

**Respuesta 404:**
```json
{
  "detail": "No existe la mascota con código 9999.",
  "code": "MASCOTA_NO_ENCONTRADA"
}
```

### POST `/solicitudes`

Crear una solicitud de adopción.

**Body requerido:**
```json
{
  "cedula": "1002003001",
  "codmascota": 1
}
```

**Respuesta 201 (éxito):**
```json
{
  "cedula": "1002003001",
  "codmascota": 1,
  "fechasolicitud": "2026-05-18T20:30:45.123456+00:00",
  "estado": "pendiente"
}
```

**Códigos de error:**

| Código | Causa |
|--------|-------|
| `400` `BAD_REQUEST` | Payload inválido (parámetros faltantes o malformados) |
| `404` `MASCOTA_NO_ENCONTRADA` | `codmascota` no existe en BD |
| `409` `MAX_SOLICITUDES_EXCEDIDO` | El adoptante ya tiene una solicitud activa |
| `422` `MASCOTA_NO_DISPONIBLE` | La mascota no está disponible (ya tiene solicitud activa) |

**Formato de error:**
```json
{
  "detail": "El adoptante 1002003001 ya tiene una solicitud activa.",
  "code": "MAX_SOLICITUDES_EXCEDIDO"
}
```

### Headers sugeridos (para futura autenticación)

- `X-User-Cedula: <string>` — Cédula del usuario autenticado (puede ser usado por gateway para auditoría)

## Problemas comunes

### Base de datos

| Problema | Solución |
|----------|----------|
| `DATABASE_URL no está configurada` | Verifica que `.env` exista en la raíz y contenga `DATABASE_URL` |
| `No module named adopciones_dominio` | Asegúrate de estar en la raíz al ejecutar tests o usa `--app-dir adopciones_dominio` con uvicorn |
| FK violation `cedula not present in adoptantes` | Crea un registro en `adoptantes` con la cédula que estés usando |
| `Invalid password / Authentication failed` | Revisa que la contraseña en `DATABASE_URL` sea correcta (URL-encódela si tiene caracteres especiales) |
| `DuplicatePreparedStatementError` | Usa pooler de Supabase (puerto 6543) si comes prepared statements; ya está configurado `statement_cache_size=0` |

### Python / Dependencias

| Problema | Solución |
|----------|----------|
| `pydantic_core` con Python 3.14 | Usa Python 3.13: `py -3.13 -m venv venv` |
| `ModuleNotFoundError: No module named 'fastapi'` | Activa el entorno virtual y ejecuta `pip install -r requirements.txt` |
| Tests fallan con `datetime.utcnow() is deprecated` | Es una advertencia, no un error. Los tests pasan igualmente. |

### API / Desarrollo

| Problema | Solución |
|----------|----------|
| `GET /docs` devuelve 404 | Asegúrate que uvicorn está corriendo y que estás en `http://127.0.0.1:8000` |
| `POST /solicitudes` devuelve 500 | Revisa los logs de uvicorn; probablemente sea FK violation o error en el mapeo |
| CORS bloqueado desde frontend | Ya está configurado CORS `allow_origins=["*"]` en `main.py` |

## Comandos útiles

### Probar endpoints desde terminal

```powershell
# PowerShell (Windows)
# Chequear disponibilidad de mascota
curl -X GET "http://127.0.0.1:8000/api/v1/mascotas/1/disponible"

# Crear solicitud
$body = '{"cedula":"1002003001","codmascota":1}'
curl -X POST "http://127.0.0.1:8000/api/v1/solicitudes" `
  -H "Content-Type: application/json" `
  -d $body
```

```bash
# Bash (Linux/macOS)
curl -X GET "http://127.0.0.1:8000/api/v1/mascotas/1/disponible"

curl -X POST "http://127.0.0.1:8000/api/v1/solicitudes" \
  -H "Content-Type: application/json" \
  -d '{"cedula":"1002003001","codmascota":1}'
```

### Desarrollo

```powershell
# Activar entorno (Windows)
(Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned) ; (& .\venv\Scripts\Activate.ps1)

# Desactivar entorno
deactivate

# Regenerar requirements.txt (después de instalar nuevos paquetes)
pip freeze > requirements.txt

# Ejecutar tests con output detallado
cd adopciones_dominio
pytest -v -s

# Salir
cd ..
```

## Estructura de directorios clave

**Para agregar un nuevo endpoint:**
1. Crear entidad en `domain/entities/`
2. Crear repositorio abstracto en `domain/repositories/`
3. Implementar repositorio en `infrastructure/repositories/`
4. Crear caso de uso en `application/use_cases/`
5. Crear router en `application/routers/`
6. Importar router en `main.py`
7. Escribir tests en `tests/`

**Para cambiar BD:**
1. Actualizar `infrastructure/database/config.py`
2. Verificar mapeo en `infrastructure/mappers/mapper.py`
3. Ejecutar `pytest infrastructure/tests/test_connection.py` para validar

## Archivos importantes

- `.env` — Credenciales (nunca comitear)
- `.env.example` — Template de configuración
- `requirements.txt` — Dependencias Python
- `.gitignore` — Ignora `.env`, `venv/`, `__pycache__/`, etc.
- `pyproject.toml` — Configuración de pytest

## Notas finales

- Este proyecto usa **arquitectura hexagonal simplificada** (domain-driven design)
- Las pruebas son unitarias (mocks) y de integración (con BD)
- Usa **SQLAlchemy ORM async** con asyncpg para PostgreSQL
- Pydantic v2 para validación de datos
- FastAPI automáticamente genera documentación OpenAPI en `/docs`

¿Preguntas? Revisa Swagger (`/docs`) o ejecuta `pytest -v` para entender el flujo.
