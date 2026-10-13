#  Sistema de Gestión de Adopción de Mascotas

Sistema web completo para gestionar la adopción de mascotas, desarrollado con una arquitectura de **3 capas**: Frontend (React/Vite), API Gateway (FastAPI) y Backend Interno (FastAPI con arquitectura DDD).

---

##  Arquitectura del Sistema

```
┌──────────────────────┐     ┌───────────────────────┐     ┌──────────────────────────┐
│   Frontend React     │────▶│   API Gateway         │────▶│   Backend Interno        │
│   (Vite - :3000)     │     │   (FastAPI - :8000)    │     │   (FastAPI - :8001)      │
│                      │     │                       │     │                          │
│ • Vista de mascotas  │     │ • Validación JWT      │     │ • Domain (Entidades)     │
│ • Solicitudes        │     │ • Verificar adoptante │     │ • Application (Use Cases)│
│ • Login / Registro   │     │ • Inyección X-Cedula  │     │ • Infrastructure (DB)    │
│ • Supabase (lectura) │     │ • Rate Limiting       │     │ • Supabase PostgreSQL    │
└──────────────────────┘     └───────────────────────┘     └──────────────────────────┘
```

### Flujo de una petición autenticada

1. El **Frontend** envía una petición a `/gateway/v1/...` con el `Authorization: Bearer <JWT>`.
2. El **Gateway** valida el JWT contra Supabase Auth (JWKS o API directa).
3. El **Gateway** verifica que la cédula del usuario exista en la tabla `adoptantes` (HTTP 403 si no).
4. El **Gateway** inyecta la cabecera `X-User-Cedula: <cédula>` y reenvía al Backend Interno.
5. El **Backend Interno** extrae la cédula del header, ejecuta las reglas de negocio y responde.
6. El **Gateway** propaga transparentemente el status HTTP y body JSON al Frontend.

---

##  Estructura del Repositorio

```
├── adopciones-frontend/          # App React/Vite (puerto 3000)
│   ├── src/
│   │   ├── context/              # AuthContext (Supabase Auth)
│   │   ├── pages/                # LoginPage, RegisterPage, MascotasPage, SolicitudesPage
│   │   ├── services/             # api.js (llamadas al Gateway)
│   │   └── App.jsx               # Router principal
│   ├── vite.config.js            # Proxy /gateway → localhost:8000
│   └── package.json
│
├── gateway/                      # API Gateway de Seguridad (puerto 8000)
│   ├── middleware/
│   │   ├── auth.py               # Validación JWT (JWKS + Supabase API)
│   │   ├── verify_user.py        # Verificación de adoptante en DB
│   │   ├── rate_limit.py         # Rate limiting (slowapi)
│   │   └── enforce_https.py      # Forzar HTTPS en producción
│   ├── routers/
│   │   └── proxy.py              # Proxy transparente al Backend Interno
│   ├── register.py               # Endpoint público de registro de adoptantes
│   ├── config.py                 # Configuración con pydantic-settings
│   ├── dependencies.py           # Engine de BD síncrono para verificaciones
│   └── main.py                   # Aplicación FastAPI del Gateway
│
├── adopciones_dominio/           # Backend Interno con Arquitectura DDD (puerto 8001)
│   ├── domain/
│   │   ├── entities/             # Adoptante, Mascota, SolicitudAdopcion
│   │   ├── exceptions/           # DomainError, MaxSolicitudesExcedido, MascotaNoDisponible
│   │   └── repositories/         # Interfaces abstractas (ABC)
│   ├── application/
│   │   ├── routers/              # solicitudes_router.py, mascotas_router.py
│   │   ├── use_cases/            # CrearSolicitudAdopcion, VerificarMascotaDisponible
│   │   ├── dependencies.py       # Inyección de repos + validación X-User-Cedula
│   │   └── dtos.py               # Pydantic v2 DTOs
│   ├── infrastructure/
│   │   ├── database/
│   │   │   ├── config.py         # pydantic-settings (DATABASE_URL, SUPABASE_URL, etc.)
│   │   │   └── connection.py     # SQLAlchemy Async + asyncpg (statement_cache_size=0)
│   │   ├── repositories/         # Implementaciones SQL (MascotaRepo, SolicitudRepo)
│   │   └── mappers/              # Conversión de filas SQL a entidades de dominio
│   ├── tests/                    # Tests unitarios y de integración
│   └── main.py                   # Aplicación FastAPI del Backend Interno
│
├── schema.sql                    # DDL PostgreSQL idempotente para Supabase
├── requirements.txt              # Dependencias de Python
├── .env.example                  # Plantilla de variables de entorno
├── .env                          # Variables de entorno (NO se sube al repositorio)
├── start.ps1                     # Script de inicio para Windows (PowerShell)
└── start.sh                      # Script de inicio para Linux/macOS/Git Bash
```

---

##  Instalación y Ejecución

### Prerrequisitos

- **Python 3.13+**
- **Node.js 18+** y **npm**
- Proyecto en **Supabase** (base de datos PostgreSQL + Auth)

### 1. Clonar el repositorio

```bash
git clone https://github.com/SalgadoCifu/sistema-gesti-n-adopci-n-mascotas--main.git
cd sistema-gesti-n-adopci-n-mascotas--main
```

### 2. Configurar variables de entorno

Copia la plantilla y edita tus credenciales de Supabase:

```bash
cp .env.example .env
```

Edita `.env` con:

```env
DATABASE_URL=postgresql://postgres.[ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres
INTERNAL_API_URL=http://localhost:8001
SUPABASE_URL=https://[ref].supabase.co
SUPABASE_KEY=sb_publishable_...
ENVIRONMENT=development
```

### 3. Configurar la base de datos en Supabase

Abre el **SQL Editor** de tu proyecto Supabase y ejecuta el contenido completo de [`schema.sql`](schema.sql). Este script:

- Crea las tablas: `usuarios`, `adoptantes`, `mascotas`, `solicitudes`, `adopciones` y catálogos.
- Configura un trigger para sincronizar `auth.users` con las tablas de negocio.
- Establece políticas de Row Level Security (RLS).
- Inserta datos semilla (localidades, tipos de mascota, mascotas y un adoptante de prueba).

> **Nota:** Si tienes tablas previas, ejecuta primero:
> ```sql
> DROP TABLE IF EXISTS adopciones, solicitudes, mascotas, adoptantes, usuarios, tipomascotas, localidades CASCADE;
> DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
> DROP FUNCTION IF EXISTS public.handle_new_auth_user();
> ```

### 4. Ejecutar el sistema completo

#### En Windows (PowerShell):

```powershell
.\start.ps1
```

#### En Linux / macOS / Git Bash:

```bash
bash start.sh
```

El script automáticamente:

1.  Crea el entorno virtual `.venv` si no existe e instala dependencias Python.
2.  Instala las dependencias de Node.js del frontend si faltan.
3.  Levanta el **Backend Interno** en `http://localhost:8001`.
4.  Levanta el **API Gateway** en `http://localhost:8000`.
5.  Levanta el **Frontend React** en `http://localhost:3000`.

---

##  URLs del sistema en desarrollo

| Servicio | URL | Documentación |
| :--- | :--- | :--- |
| Frontend React | http://localhost:3000 | — |
| API Gateway | http://localhost:8000 | http://localhost:8000/docs |
| Backend Interno | http://localhost:8001 | http://localhost:8001/docs |

---

##  Seguridad del Gateway

El API Gateway implementa las siguientes capas de seguridad antes de reenviar cualquier petición al Backend Interno:

| Capa | Descripción | HTTP si falla |
| :--- | :--- | :--- |
| **CORS** | Permite orígenes configurados | — |
| **HTTPS Enforcement** | Fuerza HTTPS en producción | 301 Redirect |
| **JWT Auth** | Valida token contra Supabase Auth (JWKS + API) | 401 Unauthorized |
| **Verify Adoptante** | Verifica que la cédula exista en tabla `adoptantes` | 403 Forbidden |
| **Rate Limiting** | Máximo 60 peticiones/minuto por IP | 429 Too Many Requests |
| **Inyección X-User-Cedula** | Agrega la cédula verificada como header al Backend | — |

---

##  Ejecutar las pruebas

```powershell
# Windows (PowerShell)
$env:PYTHONPATH=".;adopciones_dominio"; .\.venv\Scripts\pytest.exe
```

```bash
# Linux / macOS
PYTHONPATH=".:adopciones_dominio" .venv/bin/pytest
```

La suite incluye:

- **Tests de dominio**: Entidades `Mascota`, `Adoptante`, `SolicitudAdopcion`.
- **Tests de casos de uso**: `CrearSolicitudAdopcion`, `VerificarMascotaDisponible`.
- **Tests de endpoints**: Verificación de status HTTP (201, 400, 401, 404, 409, 422).
- **Tests del Gateway**: Auth, verificación de adoptante, inyección de headers, propagación de errores.
- **Tests de integración**: Conexión a Supabase (se saltan automáticamente si la DB no está disponible).

---

##  Modelo de Datos

```
┌──────────────┐    ┌──────────────┐    ┌───────────────┐
│ tipomascotas │    │  localidades │    │  auth.users   │
│──────────────│    │──────────────│    │  (Supabase)   │
│ codtipomascota│   │ codlocalidad │    │───────────────│
│ nomtipomascota│   │ nomlocalidad │    │ id (UUID)     │
└──────┬───────┘    └──────┬───────┘    │ email         │
       │                   │            │ user_metadata  │
       ▼                   ▼            └───────┬───────┘
┌──────────────┐    ┌──────────────┐            │ trigger
│   mascotas   │    │  adoptantes  │◀───────────┘
│──────────────│    │──────────────│    ┌──────────────┐
│ codmascota   │    │ cedula (PK)  │◀───│  usuarios    │
│ nombre       │    │ direccion    │    │──────────────│
│ especie      │    │ telefono     │    │ cedula (PK)  │
│ estado       │    │ codlocalidad │    │ correo       │
│ codtipomascota│   │ user_id      │    │ nombre       │
└──────┬───────┘    └──────┬───────┘    │ tipouser     │
       │                   │            │ user_id      │
       ▼                   ▼            └──────────────┘
┌─────────────────────────────┐
│        solicitudes          │
│─────────────────────────────│
│ codsolicitud (PK)           │
│ cedula → adoptantes         │
│ codmascota → mascotas       │
│ fechasolicitud (TIMESTAMPTZ)│
│ estado (pendiente/aprobada/ │
│         en_proceso/rechazada)│
└─────────────┬───────────────┘
              ▼
┌─────────────────────────────┐
│        adopciones           │
│─────────────────────────────│
│ codadopcion (PK)            │
│ cedula → adoptantes         │
│ codmascota → mascotas       │
│ fechaadopcion (TIMESTAMPTZ) │
└─────────────────────────────┘
```

---

##  Tecnologías Utilizadas

| Componente | Tecnologías |
| :--- | :--- |
| **Frontend** | React, Vite, Supabase JS Client |
| **API Gateway** | FastAPI, python-jose (JWT), httpx, slowapi |
| **Backend Interno** | FastAPI, SQLAlchemy 2.0 (async), asyncpg, Pydantic v2 |
| **Base de Datos** | Supabase PostgreSQL (Transaction Pooler, puerto 6543) |
| **Autenticación** | Supabase Auth (JWT RS256), JWKS |
| **Testing** | pytest, unittest.mock |

---

##  Autores

- Santiago Villamil
- Maria Salgado
- Sofia Carrero
- Paula Ortiz
