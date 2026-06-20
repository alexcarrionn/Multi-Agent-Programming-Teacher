# Codi — Multi-Agent Programming Teacher

**Codi** es un asistente educativo con IA diseñado para enseñar programación (y otros dominios). Implementa un sistema multi-agente (LangGraph) con backend en FastAPI y frontend en Next.js, capaz de explicar conceptos, mostrar ejemplos, evaluar entregas del alumno y dar retroalimentación personalizada adaptada al nivel del alumno. Incluye un panel del docente para gestionar asignaturas, materiales y alumnos autorizados, y soporta **múltiples tipos de asignatura** (programación, formación básica en uso ético de IA, etc.) sin tocar los agentes.

---

## Tabla de contenidos

- [Características](#características)
- [Arquitectura](#arquitectura)
- [Tecnologías](#tecnologías)
- [Requisitos previos](#requisitos-previos)
- [Instalación y ejecución](#instalación-y-ejecución)
- [Variables de entorno](#variables-de-entorno)
- [Seguridad](#seguridad)
- [Despliegue con HTTPS (nginx)](#despliegue-con-https-nginx)
- [Sistema multi-tipo de asignatura](#sistema-multi-tipo-de-asignatura)
- [Estructura del proyecto](#estructura-del-proyecto)
- [Modelo de datos](#modelo-de-datos)
- [Roles: alumno y docente](#roles-alumno-y-docente)
- [Gestión de materiales y alumnos](#gestión-de-materiales-y-alumnos)
- [Endpoints de la API](#endpoints-de-la-api)
- [Tests](#tests)
- [Internacionalización](#internacionalización)

---

## Características

- **Sistema multi-agente** con un supervisor que enruta al agente especializado adecuado según el mensaje del alumno:
  - **Educador**: explica conceptos teóricos.
  - **Demostrador**: muestra ejemplos prácticos (código en `programacion`, prosa en `formacion_basica`).
  - **Evaluador**: corrige las entregas del alumno usando rúbricas.
  - **Crítico**: da retroalimentación cualitativa.
- **Sistema multi-tipo de asignatura** (multi-dominio): cada asignatura lleva un `tipo` (`programacion`, `formacion_basica`…) y cada agente carga un juego de prompts distinto según ese tipo. Se pueden añadir nuevos dominios sin tocar los agentes (ver [Sistema multi-tipo de asignatura](#sistema-multi-tipo-de-asignatura)).
- **RAG (Retrieval-Augmented Generation)**: recupera materiales del curso (PDFs, DOCs, etc.) antes de responder, para que los agentes tengan contexto de la asignatura.
- **Selección dinámica de asignatura por el alumno**: el header carga del backend las asignaturas en las que el alumno está matriculado. Al cambiar, el RAG filtra por la colección correspondiente de Qdrant y el backend resuelve el `tipo` desde la BD.
- **Detección y adaptación de nivel**: el sistema detecta automáticamente el nivel del alumno (principiante → intermedio → avanzado) y adapta las respuestas.
- **Memoria de conversación**: cada alumno tiene sus propios hilos de conversación persistentes (LangGraph `MemorySaver`).
- **Streaming en tiempo real**: las respuestas se envían por SSE (Server-Sent Events).
- **Flujo del demostrador inteligente**: el supervisor detecta cuándo el alumno pide una pregunta de autoevaluación y el grafo salta el demostrador con una arista condicional (`skip_demostrador`). El demostrador, además, recibe contexto limpio del turno actual para evitar mimetizar outputs de turnos previos.
- **Roles diferenciados**: alumno y docente con autenticación, JWT y endpoints separados.
- **Panel del docente**:
  - Alta de asignaturas con **Select de tipo** (programación / formación básica) y badge visual en el listado/detalle.
  - Unión a asignaturas existentes con código de invitación.
  - Gestión de alumnos autorizados (CRUD + import Excel + alta individual con auto-matrícula si ya tienen cuenta).
  - Eliminar alumnos de la asignatura.
  - **Ficha del alumno** con su progreso académico y sus últimas interacciones (con enlace al panel global ya filtrado por ese alumno).
  - **Panel de interacciones de alumnos** (`/docente/interacciones`): vista global de todas las interacciones de sus alumnos, **filtrable por asignatura y por alumno**, ordenable por fecha y con **exportación a Excel** (`.xlsx`) que respeta los filtros activos.
  - **Gestión de documentación del RAG**: subir/listar/eliminar archivos por asignatura desde la UI, separados por tipo (teoría / prácticas).
- **Auto-matrícula**: al registrar a un alumno a través del Excel o al autorizarlo individualmente, queda matriculado automáticamente en las asignaturas donde su correo aparezca como autorizado.
- **Recuperación de contraseña por email** vía Brevo SMTP, con tokens temporales.
- **Recarga en caliente** de los documentos del curso: cualquier cambio en `/code/data/` se indexa sin reiniciar (vía `watchfiles`). El upload/delete desde el panel docente confía en este watcher para indexar de forma asíncrona y evitar timeouts.
- **Multiidioma**:
  - Backend: detección automática del idioma del alumno (es/en) y traducción de mensajes con gettext.
  - Frontend: selector manual de idioma en el header (react-i18next) con traducciones en `web/public/locales/{es,en}/common.json`.
- **Anonimización de cuentas**: la baja de un alumno conserva su progreso académico anonimizando los datos personales.
- **Capa de seguridad**: rate limiting (slowapi, por usuario-o-IP), validación de entrada (Pydantic v2, anti path-traversal), cabeceras de seguridad (CSP/X-Frame/nosniff), CORS por lista blanca y reverse proxy HTTPS con nginx (ver [Seguridad](#seguridad) y [Despliegue con HTTPS (nginx)](#despliegue-con-https-nginx)).
- **Documentación OpenAPI** automática en `/docs` (Swagger UI) y `/redoc`.

---

## Arquitectura

```
Alumno / Docente (Next.js)
       │  SSE / REST
       ▼
FastAPI (main.py)
       │
       ├─ Auth (JWT cookies, rol alumno/docente)
       ├─ MySQL  ◄─── Alumnos, Docentes, Asignaturas (con tipo), Matrículas, Progreso, Interacciones
       │
       └─ LangGraph Workflow
              │
              ├─ Supervisor  ──► RAG (Qdrant, colección por asignatura)
              │   │
              │   └─ Resuelve next_agent + pide_pregunta_autoevaluacion (→ skip_demostrador)
              │
              ├─ Educador     ──► (si skip_demostrador) END
              ├─ Demostrador  (modo DIRECTO o TRAS_EDUCADOR)
              ├─ Evaluador
              └─ Crítico
```

**Flujo de un mensaje**:

1. El alumno envía un mensaje al endpoint `/api/chat` indicando la asignatura activa (slug).
2. El backend resuelve la asignatura desde BD y obtiene su `tipo` (no se confía en el cliente).
3. El supervisor (con el prompt del tipo correspondiente) analiza el mensaje y decide qué agente debe responder. Antes de delegar, valida que la pregunta esté en el ámbito de la asignatura mediante una consulta RAG.
4. El nodo RAG recupera fragmentos relevantes del material desde la colección Qdrant correspondiente.
5. El agente seleccionado (con el prompt del tipo) genera la respuesta con ese contexto.
6. Si tras el educador el supervisor detectó que el alumno pedía una pregunta de autoevaluación (`skip_demostrador=True`), el grafo salta al final. En caso contrario, el demostrador encadena un ejemplo.
7. Si es una evaluación, el Crítico añade retroalimentación y se guarda el progreso en MySQL.
8. La interacción completa se almacena en `interacciones` para el historial del alumno, la ficha del alumno y el panel global de interacciones del docente (filtrable por asignatura y alumno, y exportable a Excel).

**Convención del slug**: la asignatura viaja por el sistema como un slug calculado con `nombre.lower().replace(' ', '_')`. Lo aplican coherentemente: el frontend del alumno, la creación de carpetas en `data/<slug>/`, las funciones de guardado (`guardar_progreso`, `guardar_interaccion`), los endpoints del docente y el helper `get_asignatura_by_slug` del repo que resuelve el `tipo`.

---

## Tecnologías

| Capa | Tecnología |
|---|---|
| Backend | Python 3.12, FastAPI, Uvicorn |
| Agentes / Workflow | LangChain, LangGraph |
| Base de datos relacional | MySQL 8 + SQLAlchemy |
| Base de datos vectorial | Qdrant |
| Embeddings | BAAI/bge-m3 (o text-embedding-3-small) |
| LLMs soportados | Gemini, GPT-compatible (OpenAI API o gpt-oss via Ollama) |
| Autenticación | JWT (python-jose, passlib) |
| Email | Brevo SMTP (recuperación de contraseña) |
| Frontend | Next.js 16, React 19 |
| Estilos | Tailwind CSS 4, shadcn/ui, Radix UI |
| Markdown del chat | react-markdown + remark-gfm |
| i18n | gettext (backend), react-i18next (frontend) |
| Comunicación | Axios, Server-Sent Events |
| Reverse proxy / HTTPS | nginx (TLS, enrutado a api/web, soporte SSE) |
| Seguridad | slowapi (rate limiting), Pydantic v2 (validación), cabeceras CSP/X-Frame/nosniff |
| Tests | pytest (backend), Vitest + Testing Library (frontend) |
| Contenedores | Docker Compose (mysql + api + web + nginx) |

---

## Requisitos previos

### Opción A — con Docker (recomendado)
- Docker Desktop o Docker Engine + Docker Compose
- Instancia de Qdrant accesible (cloud o auto-alojada)
- Clave de API de un LLM compatible
- (Opcional) Cuenta SMTP en Brevo para recuperación de contraseña

### Opción B — sin Docker
- Python 3.12 o superior
- Node.js 18 o superior
- Servidor MySQL en ejecución
- Instancia de Qdrant
- Clave de API de un LLM compatible

---

## Instalación y ejecución

### Opción A — Docker Compose (recomendado)

Levanta los servicios (`mysql`, `api`, `web`, `nginx`) con una sola orden tras crear el `.env`:

```bash
git clone <url-del-repositorio>
cd Multi-Agent-Programming-Teacher
cp .env.example .env       # Edita .env con tus credenciales
docker compose up -d --build
```

- **Frontend**: http://localhost:3000
- **Backend (Swagger)**: http://localhost:8000/docs
- **MySQL**: expuesto solo a la red interna de compose
- **nginx (reverse proxy HTTPS)**: https://localhost — ver [Despliegue con HTTPS (nginx)](#despliegue-con-https-nginx)

> ⚠️ El contenedor `nginx` **necesita certificados TLS** en `nginx/ssl/` (`fullchain.pem` + `privatekey.pem`).
> Sin ellos no arranca (los demás servicios sí). Para desarrollo local puedes generar un certificado
> autofirmado (ver sección de nginx) o simplemente trabajar contra `http://localhost:3000` directamente.

### Opción B — Local

#### 1. Clonar
```bash
git clone <url-del-repositorio>
cd Multi-Agent-Programming-Teacher
```

#### 2. Backend
```bash
python -m venv .venv
source .venv/bin/activate        # Linux/macOS
.venv\Scripts\activate           # Windows

pip install -r requeriments.txt
cd code
uvicorn main:app
```

El backend arranca en `http://localhost:8000` y al iniciar:
- Crea las tablas de MySQL si no existen.
- Lanza un watcher de documentos en `/code/data/` para indexación en caliente en Qdrant.
- Lanza un watcher del Excel `data/docentes_autorizados.xlsx`.

#### 3. Frontend
```bash
cd web
npm install
npm run dev          # desarrollo
# o producción:
npm run build && npm start
```

Disponible en `http://localhost:3000`. Las llamadas a `/backend/api/...` se redirigen al backend en el puerto 8000.

---

## Variables de entorno

Crea un `.env` en la raíz con:

```env
# ─── LLM ────────────────────────────────────────────────────────────────────
LLM_MODEL=                          # gpt-4o, gemini-2.5-flash, ollama/gpt-oss:20b...
LLM_API_KEY=tu_api_key
LLM_URL=                            # base URL (gpt-compatible / Ollama)

# ─── Qdrant ─────────────────────────────────────────────────────────────────
QDRANT_URL=https://tu-instancia.qdrant.io
QDRANT_API_KEY=tu_qdrant_api_key
QDRANT_COLLECTION=                  # colección por defecto

# ─── MySQL ──────────────────────────────────────────────────────────────────
MYSQL_HOST=tu_host                  # con Docker: "mysql" (lo setea docker-compose)
MYSQL_PORT=3306
MYSQL_USER=tu_user
MYSQL_PASSWORD=tu_password
MYSQL_ROOT_PASSWORD=tu_root_password # requerido por el contenedor de mysql
MYSQL_DB=agentes_db

# ─── Embeddings ─────────────────────────────────────────────────────────────
EMBEDDING_MODEL=BAAI/bge-m3

# ─── JWT ────────────────────────────────────────────────────────────────────
JWT_SECRET=cambia_esto_por_un_secreto_hex_de_64_caracteres
JWT_ALGORITHM=HS256
JWT_EXPIRATION=60                   # minutos

# ─── Brevo SMTP (opcional) ──────────────────────────────────────────────────
BREVO_SMTP_HOST=smtp-relay.brevo.com
BREVO_SMTP_PORT=587
BREVO_SMTP_LOGIN=tu_login
BREVO_SMTP_KEY=tu_clave
BREVO_SENDER_EMAIL=noreply@tu-dominio.com
BREVO_SENDER_NAME=Codi
FRONTEND_URL=http://localhost:3000
#FRONTEND_URL=https://${DNS_DOMAIN}
# Origenes permitidos por CORS (coma-separados). Si no se define, usa FRONTEND_URL
# + http://localhost:3000. En produccion: CORS_ALLOWED_ORIGINS=https://tudominio.com

# ─── LangSmith (opcional, trazas) ───────────────────────────────────────────
LANGSMITH_TRACING=false
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
LANGSMITH_API_KEY=tu_langsmith_api_key
LANGSMITH_PROJECT=mi-proyecto

# ─── Rate limiting (slowapi) ────────────────────────────────────────────────
# Calibrable sin rebuild. Formato "N/minute", "N/hour"; varios con ";".
RATE_LIMIT_STORAGE=memory://        # 1 worker; con réplicas usar redis://host:6379
RATE_LIMIT_ENABLED=true
RATE_LIMIT_DEFAULT=100/minute        # red global a todas las rutas
RATE_LIMIT_AUTH=5/minute;20/hour     # login/registro/reset (anti fuerza bruta)
RATE_LIMIT_CHAT=20/minute            # chat (coste real en tokens LLM)
RATE_LIMIT_UPLOAD=20/minute          # subidas de ficheros

# ─── Límites de validación de entrada ───────────────────────────────────────
MAX_CHAT_MESSAGE_CHARS=4000
MAX_EXCEL_BYTES=10485760             # 10 MB
MAX_EXCEL_ROWS=5000
MAX_DOC_BYTES=52428800               # 50 MB (alineado con nginx client_max_body_size)

#----------------------------------------------
#   PUERTOS DEL HOST (mapeo docker-compose)
#----------------------------------------------
WEB_PORT=3000
API_PORT=8000
HTTP_PORT=80                         # puerto host → nginx:80 (redirige a HTTPS)
HTTPS_PORT=443                       # puerto host → nginx:443

#----------------------------------------------
#   DNS DOMAIN
#----------------------------------------------
DNS_DOMAIN=
```

---

## Seguridad

Codi incorpora una capa de endurecimiento en backend y frontend:

- **Rate limiting (slowapi)**: limita las peticiones con una clave **usuario-o-IP** (por identidad si hay JWT en la cookie; si no, por IP real). Los límites se configuran por `.env` (ver bloque *Rate limiting* arriba) y se aplican a auth, chat y subidas, más una red global por defecto. Al superarse se devuelve **429** con `Retry-After`.
  - La IP real se toma de `X-Real-IP` (la pone nginx), no del `X-Forwarded-For` crudo que el cliente podría falsear. **Por eso en producción es necesario un proxy (nginx) delante** (ver siguiente sección).
- **Validación de entrada (Pydantic v2)**: `EmailStr`, longitudes (`Field(min/max)`) y `Enum` para campos cerrados (nivel, tipo de asignatura). Los nombres de asignatura y de fichero se sanean contra **path traversal** antes de usarse como carpeta o colección de Qdrant. Los errores se devuelven como **422** con un mensaje i18n claro por campo.
- **Límites de tamaño**: longitud máxima del mensaje de chat, y tamaño/filas de los Excel y documentos subidos al RAG (configurables por `.env`).
- **Cabeceras de seguridad**: CSP, `X-Content-Type-Options`, `X-Frame-Options: DENY` y `Referrer-Policy` tanto en el frontend (Next.js `headers()`) como en el backend (todas las respuestas).
- **CORS por lista blanca**: solo se reflejan los orígenes de `CORS_ALLOWED_ORIGINS` (por defecto `FRONTEND_URL` + `localhost`), sin comodines.
- **DDL endurecido**: el nombre de base de datos del `CREATE DATABASE` se valida con regex antes de interpolarse (anti-inyección).

---

## Despliegue con HTTPS (nginx)

En producción, **nginx** actúa como único punto de entrada (reverse proxy + terminación TLS) delante de `api` y `web`:

```
Navegador ──HTTPS──► nginx:443 ─┬─ /backend/ ──► api:8000
                                └─ /         ──► web:3000 (Next.js)
            nginx:80 ──► 301 redirección a HTTPS
```

nginx también pasa `X-Real-IP` al backend, necesario para que el rate limiting identifique al cliente real (ver [Seguridad](#seguridad)). La configuración vive en `nginx/default.conf.template` (la imagen oficial sustituye `${DNS_DOMAIN}` con envsubst al arrancar) y soporta SSE/streaming del chat (`proxy_buffering off`, `proxy_read_timeout 3600s`).

### Producción (dominio real)

1. **Dominio** → en `.env`:
   ```env
   DNS_DOMAIN=tudominio.com
   FRONTEND_URL=https://tudominio.com
   # CORS_ALLOWED_ORIGINS se resuelve solo desde FRONTEND_URL; o fíjalo explícito:
   #CORS_ALLOWED_ORIGINS=https://tudominio.com
   ```
2. **Certificados TLS** → coloca en `nginx/ssl/` (gitignored) los certificados reales (p. ej. Let's Encrypt/certbot):
   - `fullchain.pem`
   - `privatekey.pem`
3. **Arranca**:
   ```bash
   docker compose up -d --build
   ```
   La app queda servida en `https://tudominio.com` (HTTP redirige a HTTPS).

### Pruebas locales con nginx (certificado autofirmado)

Si quieres levantar el stack completo (nginx incluido) en local, genera un certificado autofirmado:

```bash
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout nginx/ssl/privatekey.pem \
  -out nginx/ssl/fullchain.pem \
  -subj "/CN=localhost"
```

Luego entra por `https://localhost` (el navegador avisará de certificado no confiable → acéptalo). Alternativamente, omite nginx y trabaja contra `http://localhost:3000` directamente.

> Los puertos del host (`WEB_PORT`, `API_PORT`, `HTTP_PORT`, `HTTPS_PORT`) son configurables por `.env`.

---

## Sistema multi-tipo de asignatura

Cada asignatura lleva un campo `tipo` (`Asignatura.tipo`, `String(50)`, default `"programacion"`). Cada tipo tiene su propio juego de prompts en `code/prompts/<tipo>/`. El supervisor, educador, demostrador, evaluador y crítico cargan dinámicamente el prompt correcto según el `tipo` que viene del state.

### Tipos disponibles

| Tipo | Dominio | Demostrador | Evaluador |
|---|---|---|---|
| `programacion` | Programación / algorítmica | Ejemplos de código en el lenguaje del material | Rúbrica clásica (Correctitud, Eficiencia, Legibilidad, Estilo) |
| `formacion_basica` | Uso ético y responsable de IA en el ámbito académico | Ejemplos en prosa (prompts, citaciones APA, casos de plagio asistido…) | Rúbrica examen-RAG: Correctitud /5 + Cobertura /3 + Precisión conceptual /2 = **10** |

### Cómo añadir un tipo nuevo

1. **Crear carpeta** `code/prompts/<nuevo_tipo>/` con 5 archivos siguiendo la convención de nombres:

```python
# educador_prompts.py
AGENTE_EDUCADOR_PROMPT_ES = "..."
AGENTE_EDUCADOR_PROMPT_EN = "..."

# demostrador_prompts.py
AGENTE_DEMOSTRADOR_PROMPT_ES_DIRECTO = "..."
AGENTE_DEMOSTRADOR_PROMPT_ES_TRAS_EDUCADOR = "..."
AGENTE_DEMOSTRADOR_PROMPT_EN_DIRECTO = "..."
AGENTE_DEMOSTRADOR_PROMPT_EN_TRAS_EDUCADOR = "..."

# evaluador_prompts.py, critico_prompts.py: _ES / _EN
# supervisor_prompts.py: _ES (el supervisor solo tiene ES)
```

Patrón general: `AGENTE_<AGENTE>_PROMPT_<IDIOMA>[_<MODO>]`. El helper `get_prompt(agente, tipo, idioma, modo=None)` en `code/prompts/__init__.py` lo construye dinámicamente.

2. **Añadir el valor al frontend**: en `web/app/docente/page.jsx`, añadir una nueva `<option>` al `<select>` del formulario de creación de asignatura.

3. **Añadir las claves i18n**: en `web/public/locales/{es,en}/common.json`, añadir `tipo_<nuevo_tipo>`.

4. **No hace falta tocar**: agentes, helper, workflow, state, endpoints. Funcionan transparentemente.

---

## Estructura del proyecto

```
Multi-Agent-Programming-Teacher/
├── Dockerfile                          # imagen del backend (Python 3.12-slim)
├── docker-compose.yml                  # mysql + api + web + nginx
├── requeriments.txt
├── README.md
├── CAMBIOS_SESION_2026-05-21.md        # changelog de la última sesión
│
├── nginx/                              # Reverse proxy + HTTPS
│   ├── default.conf.template           # config (envsubst de ${DNS_DOMAIN} al arrancar)
│   └── ssl/                            # certificados TLS (gitignored)
│
├── code/                               # Backend Python (FastAPI)
│   ├── main.py                         # Punto de entrada, rutas, watchers
│   ├── i18n.py                         # Utilidad gettext
│   ├── compile_translations.py         # Script .po → .mo
│   ├── load_data.py                    # Carga e indexación inicial del RAG
│   ├── agents/                         # Agentes LLM especializados
│   │   ├── supervisor.py               # Enrutador con Pydantic Router + flag skip_demostrador
│   │   ├── educador.py
│   │   ├── demostrador.py              # contexto limpio + cap 2000 chars
│   │   ├── evaluador.py                # extrae nota X/10 con regex
│   │   ├── critico.py
│   │   └── agentType.py                # enum
│   ├── graph/                          # Orquestación con LangGraph
│   │   ├── workflow.py                 # Grafo + streaming SSE + arista condicional educador
│   │   └── state.py                    # AgentState (incluye tipo_asignatura, skip_demostrador)
│   ├── prompts/                        # Prompts por tipo
│   │   ├── __init__.py                 # get_prompt(agente, tipo, idioma, modo)
│   │   ├── programacion/
│   │   │   ├── educador_prompts.py
│   │   │   ├── demostrador_prompts.py
│   │   │   ├── evaluador_prompts.py
│   │   │   ├── critico_prompts.py
│   │   │   └── supervisor_prompts.py
│   │   └── formacion_basica/
│   │       └── (mismos 5 archivos)
│   ├── database/
│   │   ├── models.py                   # Modelos SQLAlchemy (incluye Asignatura.tipo)
│   │   ├── repository.py               # Consultas (incluye get_asignatura_by_slug)
│   │   └── hash_password.py
│   ├── rag/
│   │   ├── retriever.py                # top_k=2 (default)
│   │   ├── indexer.py                  # chunk_size=1000, overlap=150
│   │   ├── embeddings.py
│   │   └── qDrantClient.py
│   ├── config/                         # Settings desde .env
│   │   ├── settings.py                 # Config central (rate limit, CORS, límites...)
│   │   └── rate_limit.py               # Limitador slowapi (clave usuario-o-IP)
│   ├── auth/                           # JWT y autenticación
│   ├── tests/                          # pytest: agentes, RAG, BD, workflow
│   ├── data/                           # Materiales (montado como volumen)
│   │   ├── <slug_asignatura>/
│   │   │   ├── teoria/
│   │   │   └── practicas/
│   │   └── docentes_autorizados.xlsx
│   └── locales/                        # Traducciones gettext (es, en)
│
└── web/                                # Frontend Next.js
    ├── Dockerfile                      # Build multi-stage (deps → builder → runner)
    ├── package.json
    ├── next.config.mjs
    ├── app/
    │   ├── page.jsx                    # Página principal del chat
    │   ├── layout.jsx                  # Providers (Auth + i18n)
    │   ├── auth/                       # Login, registro, recuperación
    │   ├── chat/                       # Vista de chat
    │   ├── docente/                    # Panel del docente (dashboard, asignaturas, alumnos)
    │   ├── backend/api/chat/route.js   # Proxy SSE al backend (con fix gzip)
    │   ├── components/
    │   │   ├── chat/                   # ChatArea, ChatInput, MessageBubble (markdown), WelcomeScreen
    │   │   ├── ui/                     # Header, Button, Dialog, Table, SelectorIdioma
    │   │   └── providers/              # I18Provider
    │   └── context/
    │       └── AuthContext.jsx
    ├── lib/
    │   ├── i18n.js                     # Configuración react-i18next
    │   ├── api/                        # Cliente de la API
    │   └── hooks/                      # useChat (gestiona el stream SSE)
    └── public/locales/{es,en}/common.json
```

---

## Modelo de datos

```
alumnos                       docentes
   │                             │
   ▼ (N:M)                       ▼ (N:M)
alumnos_asignaturas      docentes_asignaturas
   │                             │
   └────────► asignaturas (id, nombre, codigo, codigo_invitacion, tipo) ◄──┘
                   ▲
                   │ (autorización pre-registro)
                   │
       alumnos_aula_asignatura  ◄── el docente la rellena vía Excel o CRUD
```

**Tablas principales**:

| Tabla | Propósito |
|---|---|
| `alumnos` | Cuentas de alumnos registrados |
| `docentes` | Cuentas de docentes registrados |
| `docentes_aula` | Lista de docentes autorizados a registrarse (Excel global) |
| `asignaturas` | Catálogo de asignaturas (con campo `tipo`: programacion / formacion_basica…) |
| `docentes_asignaturas` | Relación N:M docente ↔ asignatura |
| `alumnos_asignaturas` | Matrícula real (alumno ↔ asignatura) |
| `alumnos_aula_asignatura` | Lista de correos autorizados por asignatura |
| `progresos` | Historial de evaluaciones del alumno. `asignatura_id` FK para filtrar por asignatura |
| `interacciones` | Historial completo de mensajes del chat. `asignatura_id` FK para filtrar por asignatura |

**Flujo de matrícula**:

1. El docente se registra (su correo debe estar en `docentes_autorizados.xlsx`).
2. Crea una asignatura desde el panel, seleccionando su `tipo`.
3. Importa un Excel de alumnos autorizados o los añade manualmente → filas en `alumnos_aula_asignatura`.
4. Los alumnos cuyos correos estén en esa lista pueden registrarse.
5. Al registrarse, el alumno queda **automáticamente matriculado** en todas las asignaturas donde su correo aparezca autorizado.

---

## Roles: alumno y docente

El sistema diferencia dos roles mediante un campo `rol` en el JWT.

### Alumno
- Se registra en `/auth/register` con un correo `@um.es` autorizado por algún docente.
- Hace login en `/auth/login`.
- Accede al chat y consulta su propio historial.
- Sus rutas de API son `/api/...` (sin el prefijo `/docente/`).

### Docente
- Se registra en `/auth/docente/register` con un correo `@um.es` que figure en `docentes_autorizados.xlsx`.
- Hace login en `/auth/docente/login`.
- Capacidades en el panel:
  - **Asignaturas**: crear (con Select de tipo + badge de tipo en la card), listar las que imparte, unirse a una existente vía código de invitación.
  - **Vista de asignatura** (`/docente/asignaturas/[id]`): cabecera con código + tipo + acciones + tabla de alumnos matriculados + tabla de documentación del agente.
  - **Alumnos autorizados**: importar Excel (UPSERT), añadir individualmente con auto-matrícula si ya tiene cuenta, editar, borrar.
  - **Alumnos matriculados**: listar quienes ya tienen cuenta y están matriculados; eliminarlos de la asignatura.
  - **Ficha del alumno** (`/docente/alumnos/[id]`): progreso académico y sus últimas interacciones (filtradas por la asignatura desde la que se accedió), con enlace al panel global de interacciones ya filtrado por ese alumno.
  - **Panel de interacciones** (`/docente/interacciones`): todas las interacciones de sus alumnos en un solo lugar, con filtros por asignatura y alumno, orden por fecha y **exportación a Excel** respetando los filtros. Es la fuente única de interacciones (la ficha del alumno solo muestra las últimas y enlaza aquí).
  - **Documentación del RAG por asignatura**: subir/listar/eliminar (.pdf, .txt, .docx, .md), separados por tipo (teoría / prácticas). Indexado asíncrono en Qdrant vía watcher.
- La autorización se valida en cada endpoint: un docente solo puede ver/modificar lo que pertenece a sus asignaturas.

---

## Gestión de materiales y alumnos

### Añadir materiales del curso

**Forma recomendada — desde el panel del docente**: en `/docente/asignaturas/[id]`, botón **"Añadir documentación al agente"**. Eliges uno o varios archivos y el tipo (teoría o prácticas). El backend solo escribe los archivos a disco; el watcher los detecta y los indexa en Qdrant en segundo plano (10–20 s para PDFs grandes). Para borrar, papelera junto a cada archivo en la tabla.

**Forma alternativa — vía filesystem**: copia archivos directamente a `/code/data/<slug>/teoria/` o `/code/data/<slug>/practicas/`. El `<slug>` se genera con `nombre.lower().replace(' ', '_')` y la carpeta ya existe (se crea al crear la asignatura). El watcher hace el resto.

| Carpeta | Contenido |
|---|---|
| `teoria/` | Apuntes, diapositivas, material teórico |
| `practicas/` | Guiones de prácticas, ejercicios, rúbricas |

**Formatos soportados**: PDF, DOCX, TXT, MD.

> El watcher (`observar_cambios_documentacion`) usa `watchfiles` y reacciona a `Change.added/modified/deleted`. **No reinicies el servidor** después de cambiar un archivo: ya se ocupa.

### Gestionar docentes autorizados

Edita el archivo `/code/data/docentes_autorizados.xlsx`. Columnas esperadas:

| Columna | Descripción |
|---|---|
| `Nombre` | Nombre completo del docente |
| `Correo electrónico` | Email institucional (`@um.es`) |
| `DNI` | DNI del docente (opcional) |

Los cambios se sincronizan en caliente con la tabla `docentes_aula`.

### Gestionar alumnos autorizados (por asignatura)

Desde el panel del docente. Cada docente puede:

- Importar un Excel con la columna `Correo electrónico`. UPSERT por correo: añade los que falten sin duplicar los existentes.
- Añadir, editar o borrar autorizaciones individualmente.
- Consultar quién está autorizado y quién ya tiene cuenta.

---

## Endpoints de la API

### Autenticación de alumnos

| Método | Ruta | Descripción |
|---|---|---|
| `POST` | `/api/register` | Registrar alumno (auto-matrícula en sus asignaturas autorizadas) |
| `POST` | `/api/login` | Login (cookie JWT con `rol=alumno`) |
| `POST` | `/api/logout` | Logout |
| `GET` | `/api/me` | Datos del alumno autenticado |
| `PUT` | `/api/update-password` | Cambiar contraseña |
| `DELETE` | `/api/delete-account` | Anonimizar cuenta |
| `POST` | `/api/forgot-password` | Solicitar enlace de reset por email |
| `POST` | `/api/reset-password` | Restablecer contraseña con token |

### Autenticación de docentes

| Método | Ruta | Descripción |
|---|---|---|
| `POST` | `/api/docente/register` | Registrar docente |
| `POST` | `/api/docente/login` | Login (cookie JWT con `rol=docente`) |
| `POST` | `/api/docente/logout` | Logout |
| `GET` | `/api/docente/me` | Datos del docente autenticado |

### Chat (alumno)

| Método | Ruta | Descripción |
|---|---|---|
| `POST` | `/api/chat` | Enviar mensaje (respuesta SSE en streaming). El backend resuelve el `tipo` de la asignatura desde BD |
| `GET` | `/api/interacciones` | Historial completo del alumno autenticado |
| `GET` | `/api/asignaturas` | Listar asignaturas disponibles (carpetas en `/data`) |
| `GET` | `/api/me/asignaturas` | Asignaturas en las que el alumno autenticado está matriculado (incluye `tipo`) |

### Panel del docente — asignaturas y alumnos

| Método | Ruta | Descripción |
|---|---|---|
| `POST` | `/api/docente/asignaturas` | Crear asignatura. Body: `{ nombre, codigo, tipo }`. Crea `data/<slug>/teoria/` y `practicas/` |
| `GET` | `/api/docente/asignaturas` | Listar asignaturas del docente (incluye `tipo` en cada item) |
| `GET` | `/api/docente/asignaturas/{id}` | Datos de una asignatura concreta (incluye `tipo`) |
| `POST` | `/api/docente/unirse-asignatura` | Unirse a una asignatura existente con código de invitación |
| `GET` | `/api/docente/asignaturas/{id}/alumnos` | Alumnos matriculados (con cuenta) |
| `POST` | `/api/docente/asignaturas/{id}/matricular` | Matricular un alumno por email |
| `DELETE` | `/api/docente/asignaturas/{id}/alumnos/{alumno_id}` | Eliminar alumno de la asignatura |
| `GET` | `/api/docente/alumnos/{id}` | Datos básicos del alumno (id, nombre, email, nivel) |
| `GET` | `/api/docente/alumnos/{id}/progreso?asignatura_id=N` | Historial de evaluaciones; `asignatura_id` filtra opcionalmente |
| `GET` | `/api/docente/alumnos/{id}/interacciones?asignatura_id=N` | Historial de chat; `asignatura_id` filtra opcionalmente |
| `GET` | `/api/docente/interacciones?asignatura_id=N&alumno_id=M` | Todas las interacciones de los alumnos del docente; filtros opcionales por asignatura y alumno |
| `GET` | `/api/docente/interacciones/export?asignatura_id=N&alumno_id=M` | Exporta las interacciones a Excel (`.xlsx`) respetando los filtros |

### Panel del docente — alumnos autorizados

| Método | Ruta | Descripción |
|---|---|---|
| `POST` | `/api/docente/asignaturas/{id}/import-alumnos` | Importar Excel (UPSERT + auto-matrícula si ya tienen cuenta) |
| `GET` | `/api/docente/asignaturas/{id}/alumnos-autorizados` | Listar autorizados |
| `POST` | `/api/docente/asignaturas/{id}/alumnos-autorizados` | Añadir uno manualmente (UPSERT + auto-matrícula) |
| `PUT` | `/api/docente/alumnos-autorizados/{id}` | Editar |
| `DELETE` | `/api/docente/alumnos-autorizados/{id}` | Eliminar |

### Panel del docente — documentación del RAG

| Método | Ruta | Descripción |
|---|---|---|
| `POST` | `/api/docente/asignaturas/{id}/documentos` | Subir uno o varios archivos. Body: `tipo` (teoria/practicas) + `files`. Solo escribe a disco; el watcher indexa en Qdrant |
| `GET` | `/api/docente/asignaturas/{id}/documentos` | Listar archivos en `data/<slug>/teoria/` y `practicas/` |
| `DELETE` | `/api/docente/asignaturas/{id}/documentos?tipo=X&nombre=Y` | Borrar archivo del disco; el watcher se ocupa de Qdrant |

> Documentación detallada de cada endpoint (parámetros, respuestas, códigos de error) en Swagger UI: http://localhost:8000/docs.

---

## Tests

### Backend (pytest)

Tests del backend en `code/tests/`. Cubren los agentes individualmente, el RAG, la BD y el workflow completo end-to-end.

```bash
# Dentro del contenedor:
docker exec codi-api python -m tests.test_workflow

# O ejecuta un test concreto:
docker exec codi-api python -m tests.test_evaluador
```

Archivos disponibles:
- `test_workflow.py` — flujo completo end-to-end.
- `test_supervisor.py`, `test_educador.py`, `test_demostrador.py`, `test_evaluador.py`, `test_critico.py` — agentes en aislamiento.
- `test_*_chat.py` — agentes con simulación de chat completo.
- `test_rag.py` — recuperación de contexto.
- `test_database.py` — persistencia.

### Frontend (Vitest)

```bash
cd web
npm test           # ejecución única
npm run test:watch # modo watch
npm run test:ui    # UI interactiva
```

---

## Internacionalización

### Backend (Python)

Traducciones en `code/locales/{es,en}/LC_MESSAGES/messages.{po,mo}`.

Para añadir o modificar mensajes:

1. Edita el archivo `.po` correspondiente añadiendo `msgid` / `msgstr`.
2. Compila los `.po` a `.mo`:

```bash
cd code
python compile_translations.py
```

3. Reinicia el servidor para que `gettext` recargue los `.mo` (o, en Docker, `docker compose build api && docker compose up -d`).

En el código se usan con `_("CLAVE")` tras llamar a `setup_i18n("es")` o `setup_i18n("en")`.

### Frontend (Next.js)

Traducciones en `web/public/locales/{es,en}/common.json`. El selector del header (`SelectorIdioma`) cambia el idioma activo en runtime con `react-i18next`.

En los componentes:

```jsx
import { useTranslation } from "react-i18next";

const { t } = useTranslation();
return <button>{t("login_submit")}</button>;
```

**Claves del sistema multi-tipo** (añadidas en sesión 2026-05-22):
- `docente_subject_type_label`: label del select de tipo en el form de creación.
- `docente_subject_type_badge`: texto corto para el badge en cards/detalle.
- `tipo_programacion`, `tipo_formacion_basica`: nombre traducible de cada tipo.
