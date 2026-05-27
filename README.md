# Sistema de Adopción de Mascotas

## Descripción general
Este sistema permite la gestión de adopciones de mascotas mediante una aplicación web moderna. El objetivo principal de este corte vertical es garantizar el funcionamiento end-to-end del flujo "crear una solicitud de adopción", abarcando desde la interfaz de usuario en el frontend, pasando por un gateway de seguridad, hasta llegar al backend con su lógica de dominio y persistencia en base de datos.

## Arquitectura
El sistema se compone de tres bloques principales que interactúan entre sí:
- **Frontend (React/Vite)**: Interfaz de usuario donde los adoptantes pueden ver las mascotas disponibles y enviar sus solicitudes. Consume el listado de mascotas directamente de Supabase y se comunica con el Gateway para acciones de negocio.
- **Gateway (FastAPI)**: Proxy de seguridad que valida los tokens JWT emitidos por Supabase, verifica que el usuario esté registrado como adoptante y enruta las peticiones válidas hacia el backend interno.
- **Backend Interno (FastAPI)**: API protegida que implementa la lógica de negocio usando una arquitectura en capas (Domain, Application, Infrastructure). Se encarga de validar la disponibilidad de las mascotas y las reglas de negocio de las solicitudes.
- **Supabase (PostgreSQL + Auth)**: Actúa como proveedor de identidad para la autenticación de usuarios y como base de datos principal tanto para el listado de mascotas (acceso directo desde el frontend) como para la persistencia de las solicitudes (acceso desde el backend interno).

## Estructura del repositorio
- `adopciones_dominio/` — Backend principal en Python/FastAPI que contiene las reglas de negocio, casos de uso y conexión a la base de datos siguiendo una arquitectura limpia.
- `gateway/` — API proxy en Python/FastAPI encargada de la autenticación, validación de usuarios y reenvío de peticiones.
- `adopciones-frontend/` — Aplicación web frontend construida con React y Vite.

## Flujo principal: Crear solicitud de adopción
1. **Frontend**: El usuario autenticado visualiza el listado y hace clic en "Solicitar adopción" para una mascota específica.
2. **Validación Frontend**: La aplicación realiza una petición `GET /gateway/v1/mascotas/{codmascota}/disponible` enviando el token JWT.
3. **Gateway**: El middleware de autenticación valida el token con Supabase, extrae la cédula y verifica que el usuario sea un adoptante registrado. Luego reenvía la petición al backend interno.
4. **Backend (Disponibilidad)**: Consulta en base de datos si la mascota existe y si no tiene solicitudes activas. Devuelve el estado al frontend.
5. **Solicitud Frontend**: Si la mascota está disponible, el frontend envía un `POST /gateway/v1/solicitudes` con la cédula y el código de la mascota.
6. **Gateway**: Repite el proceso de validación y además inyecta el header `X-User-Cedula` antes de reenviar la petición al backend interno.
7. **Backend (Creación)**: Valida que la mascota siga disponible y que el adoptante no tenga otra solicitud activa. Crea la solicitud en estado `pendiente`, actualiza el estado de la mascota y responde con código 201.
8. **Confirmación**: El frontend recibe la respuesta exitosa y actualiza la vista para mostrar la confirmación al usuario.

## Configuración y variables de entorno
Para ejecutar el proyecto, se requiere configurar las siguientes variables de entorno en un archivo `.env` en la raíz del repositorio:

- `DATABASE_URL` — Cadena de conexión a PostgreSQL (formato: `postgresql://usuario:password@host:puerto/bd`). Es obligatorio para que el backend pueda persistir datos.
- `INTERNAL_API_URL` — URL del backend interno (por defecto `http://localhost:8001`). Utilizada por el Gateway para enrutar las peticiones.
- `SUPABASE_URL` — URL base del proyecto en Supabase (ej. `https://xxx.supabase.co`). Necesaria para el Auth y las consultas directas.
- `SUPABASE_KEY` — Clave anónima pública de Supabase utilizada para interactuar con su API.
- `ENVIRONMENT` — Define el entorno de ejecución (`development` o `production`).

## Cómo correr el proyecto localmente
1. **Instalar dependencias del backend y gateway**:
   ```bash
   py -3.13 -m venv .venv
   # Windows: .venv\Scripts\activate
   # Linux/Mac: source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Levantar los servicios backend**:
   Puedes levantar ambos servicios a la vez (Dominio en puerto 8001 y Gateway en puerto 8000) usando el script automatizado según tu sistema operativo:

   * **En Windows (PowerShell)**:
     ```powershell
     Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass; .\start.ps1
     ```

   * **En Linux / macOS / Git Bash (Bash)**:
     ```bash
     bash start.sh
     ```

   *Alternativamente, puedes levantarlos por separado en terminales distintas:*
   - Backend interno (Dominio): `cd adopciones_dominio && uvicorn main:app --host 0.0.0.0 --port 8001 --reload`
   - Gateway de Autenticación: `uvicorn gateway.main:app --host 0.0.0.0 --port 8000 --reload`

3. **Levantar el frontend**:
   ```bash
   cd adopciones-frontend
   npm install
   npm run dev
   ```

## Códigos de error

| HTTP Status | Código de Dominio | Descripción |
|-------------|-------------------|-------------|
| 404 | `MASCOTA_NO_ENCONTRADA` | La mascota solicitada no existe en la base de datos. |
| 422 | `MASCOTA_NO_DISPONIBLE` | La mascota ya tiene una solicitud de adopción activa u otro estado que impide su adopción. |
| 409 | `MAX_SOLICITUDES_EXCEDIDO` | El adoptante ya posee una solicitud en proceso y no puede realizar otra simultáneamente. |
| 401 | `UNAUTHORIZED` | Token JWT ausente, expirado o inválido, o no contiene una cédula válida. |
| 403 | `FORBIDDEN` | El usuario está autenticado pero no existe en la tabla de adoptantes. |
| 429 | `RATE_LIMIT_EXCEEDED` | Se han realizado demasiadas solicitudes en un corto periodo de tiempo. |

## Notas de consistencia de datos
Es **crítico** que ambas partes lean información consistente: las actualizaciones de estado que realiza el backend (por ejemplo, cambiar una mascota a `en_proceso`) deben reflejarse en la base de datos de Supabase para evitar que el frontend ofrezca mascotas no disponibles, mejorando así la experiencia del usuario y previniendo conflictos concurrentes.
