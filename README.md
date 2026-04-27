# Codi — Multi-Agent Programming Teacher

**Codi** es un asistente educativo con IA diseñado para enseñar programación. Implementa un sistema multi-agente (LangGraph) con backend en FastAPI y frontend en Next.js, capaz de explicar conceptos, mostrar ejemplos de código, evaluar ejercicios y dar retroalimentación personalizada adaptada al nivel del alumno. Incluye un panel del docente para gestionar asignaturas, materiales y alumnos autorizados.

---

## Tabla de contenidos

- [Características](#características)
- [Arquitectura](#arquitectura)
- [Tecnologías](#tecnologías)
- [Requisitos previos](#requisitos-previos)
- [Instalación](#instalación)
- [Variables de entorno](#variables-de-entorno)
- [Ejecutar el proyecto](#ejecutar-el-proyecto)
- [Estructura del proyecto](#estructura-del-proyecto)
- [Modelo de datos](#modelo-de-datos)
- [Roles: alumno y docente](#roles-alumno-y-docente)
- [Gestión de materiales y alumnos](#gestión-de-materiales-y-alumnos)
- [Endpoints de la API](#endpoints-de-la-api)
- [Internacionalización](#internacionalización)

---

## Características

- **Sistema multi-agente** con un supervisor que enruta al agente especializado adecuado según el mensaje del alumno:
  - **Educador**: explica conceptos teóricos de programación.
  - **Demostrador**: muestra ejemplos prácticos de código.
  - **Evaluador**: corrige ejercicios del alumno usando rúbricas.
  - **Crítico**: da retroalimentación detallada sobre el código entregado.
- **RAG (Retrieval-Augmented Generation)**: recupera materiales del curso (PDFs, DOCs, etc.) antes de responder, para que los agentes tengan contexto de la asignatura.
- **Selección de asignatura por el alumno**: el alumno elige la asignatura activa desde el header; el RAG filtra por la colección correspondiente de Qdrant.
- **Detección y adaptación de nivel**: el sistema detecta automáticamente el nivel del alumno (principiante → intermedio → avanzado) y adapta las respuestas.
- **Memoria de conversación**: cada alumno tiene sus propios hilos de conversación persistentes (LangGraph `MemorySaver`).
- **Streaming en tiempo real**: las respuestas se envían por SSE (Server-Sent Events).
- **Roles diferenciados**: alumno y docente con autenticación, JWT y endpoints separados.
- **Panel del docente**: alta de asignaturas, gestión de alumnos autorizados (CRUD + import Excel), consulta de progreso e interacciones de cada alumno.
- **Auto-matrícula**: al registrarse un alumno, queda matriculado automáticamente en todas las asignaturas donde su correo aparezca como autorizado.
- **Recuperación de contraseña por email** vía Brevo SMTP, con tokens temporales.
- **Recarga en caliente** de los documentos del curso: cualquier cambio en `/code/data/` se indexa sin reiniciar.
- **Multiidioma**:
  - Backend: detección automática del idioma del alumno (es/en) y traducción de mensajes con gettext.
  - Frontend: selector manual de idioma en el header (react-i18next) con traducciones en `web/public/locales/{es,en}/common.json`.
- **Anonimización de cuentas**: la baja de un alumno conserva su progreso académico anonimizando los datos personales (cumple con políticas de datos).
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
       ├─ MySQL  ◄─── Alumnos, Docentes, Asignaturas, Matrículas, Progreso, Interacciones
       │
       └─ LangGraph Workflow
              │
              ├─ Supervisor  ──► RAG (Qdrant, colección por asignatura)
              ├─ Educador
              ├─ Demostrador
              ├─ Evaluador
              └─ Crítico
```

**Flujo de un mensaje**:

1. El alumno envía un mensaje al endpoint `/api/chat` indicando la asignatura activa.
2. El supervisor analiza el mensaje y decide qué agente debe responder. Antes de delegar, valida que la pregunta esté en el ámbito de la asignatura mediante una consulta RAG.
3. El nodo RAG recupera fragmentos relevantes del material desde la colección Qdrant correspondiente a esa asignatura.
4. El agente seleccionado genera la respuesta con ese contexto.
5. Si es una evaluación, el Crítico añade retroalimentación y se guarda el progreso en MySQL.
6. La interacción completa se almacena en `interacciones` para el historial del alumno y la consulta del docente.

---

## Tecnologías

| Capa | Tecnología |
|---|---|
| Backend | Python 3.9+, FastAPI, Uvicorn |
| Agentes / Workflow | LangChain, LangGraph |
| Base de datos relacional | MySQL + SQLAlchemy |
| Base de datos vectorial | Qdrant |
| Embeddings | BAAI/bge-m3 (o text-embedding-3-small) |
| Autenticación | JWT (python-jose, passlib) |
| Email | Brevo SMTP (recuperación de contraseña) |
| Frontend | Next.js 16, React 19 |
| Estilos | Tailwind CSS 4, shadcn/ui, Radix UI |
| i18n | gettext (backend), react-i18next (frontend) |
| Comunicación | Axios, Server-Sent Events |

---

## Requisitos previos

- Python 3.9 o superior
- Node.js 18 o superior
- Servidor MySQL en ejecución
- Instancia de Qdrant (cloud o auto-alojada)
- Clave de API de un LLM compatible (OpenAI-compatible, Gemini, Groq, etc.)
- Cuenta SMTP en Brevo (opcional, solo si se quiere usar la recuperación de contraseña)

---

## Instalación

### 1. Clonar el repositorio

```bash
git clone <url-del-repositorio>
cd Multi-Agent-Programming-Teacher
```

### 2. Backend (Python / FastAPI)

```bash
# Crear y activar entorno virtual
python -m venv .venv
source .venv/bin/activate        # Linux / macOS
.venv\Scripts\activate           # Windows

# Instalar dependencias
pip install -r requeriments.txt
```

### 3. Frontend (Next.js)

```bash
cd web
npm install
```

---

## Variables de entorno

Crea un archivo `.env` en la raíz del proyecto con las siguientes variables:

```env
# ─── LLM ────────────────────────────────────────────────────────────────────
LLM_MODEL=                          # ID del modelo (e.g. gpt-4o, gemini-2.5-flash)
LLM_API_KEY=tu_api_key_aqui         # Clave de API del proveedor LLM
LLM_URL=https://...                 # URL base (solo para modelos GPT-OSS / compatibles con OpenAI)

# ─── Qdrant (base de datos vectorial) ───────────────────────────────────────
QDRANT_URL=https://tu-instancia.qdrant.io
QDRANT_API_KEY=tu_qdrant_api_key
QDRANT_COLLECTION=                  # Colección por defecto

# ─── MySQL ───────────────────────────────────────────────────────────────────
MYSQL_HOST=tu_host_mysql
MYSQL_PORT=3306
MYSQL_USER=tu_user_mysql
MYSQL_PASSWORD=tu_password_mysql
MYSQL_DB=agentes_db                 # Se crea automáticamente si no existe

# ─── Embeddings ──────────────────────────────────────────────────────────────
EMBEDDING_MODEL=BAAI/bge-m3

# ─── JWT (autenticación) ─────────────────────────────────────────────────────
JWT_SECRET=cambia_esto_por_un_secreto_de_64_caracteres_hex
JWT_ALGORITHM=HS256
JWT_EXPIRATION=60                   # Expiración en minutos

# ─── Brevo SMTP (recuperación de contraseña) ────────────────────────────────
BREVO_SMTP_HOST=smtp-relay.brevo.com
BREVO_SMTP_PORT=587
BREVO_SMTP_LOGIN=tu_login_brevo
BREVO_SMTP_KEY=tu_clave_brevo
BREVO_SENDER_EMAIL=noreply@tu-dominio.com    # email verificado en Brevo
BREVO_SENDER_NAME=Codi
FRONTEND_URL=http://localhost:3000           # base URL del frontend (para los enlaces de reset)

# ─── LangSmith (opcional, trazabilidad y depuración) ────────────────────────
LANGSMITH_TRACING=false
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
LANGSMITH_API_KEY=tu_langsmith_api_key
LANGSMITH_PROJECT=mi-proyecto
```

> **Nota**: no subas nunca el `.env` al repositorio. Ya está incluido en `.gitignore`.

---

## Ejecutar el proyecto

### Backend

```bash
cd code
uvicorn main:app --reload
```

El servidor arranca en `http://localhost:8000` y al inicio:

- Crea las tablas de MySQL automáticamente si no existen.
- Lanza un watcher de documentos en `/code/data/` para indexación en caliente en Qdrant.
- Lanza un watcher del Excel `data/docentes_autorizados.xlsx` para sincronizar la lista de docentes autorizados.

Documentación interactiva de la API disponible en:

- `http://localhost:8000/docs` (Swagger UI)
- `http://localhost:8000/redoc` (ReDoc)

### Frontend

```bash
cd web
npm run dev               # modo desarrollo
# o, en producción:
npm run build && npm start
```

La aplicación estará disponible en `http://localhost:3000`. Las llamadas a `/backend/api/...` se redirigen automáticamente al backend en el puerto 8000.

---

## Estructura del proyecto

```
Multi-Agent-Programming-Teacher/
├── code/                              # Backend Python (FastAPI)
│   ├── main.py                        # Punto de entrada, rutas, servidor, watchers
│   ├── i18n.py                        # Utilidad gettext
│   ├── compile_translations.py        # Script para compilar .po → .mo
│   ├── load_data.py                   # Carga e indexación de documentos del RAG
│   ├── agents/                        # Agentes LLM especializados
│   │   ├── supervisor.py              # Enrutador con Pydantic Router
│   │   ├── educador.py
│   │   ├── demostrador.py
│   │   ├── evaluador.py
│   │   └── critico.py
│   ├── graph/                         # Orquestación con LangGraph
│   │   ├── workflow.py                # Construcción del grafo y streaming SSE
│   │   └── state.py                   # Esquema de estado compartido
│   ├── database/                      # Persistencia
│   │   ├── models.py                  # Modelos SQLAlchemy
│   │   ├── repository.py              # Consultas y lógica de BD
│   │   └── hash_password.py           # Hashing bcrypt
│   ├── rag/                           # RAG con Qdrant
│   │   ├── retriever.py
│   │   ├── indexer.py
│   │   ├── embeddings.py
│   │   └── qDrantClient.py
│   ├── prompts/                       # Prompts del sistema de cada agente
│   ├── config/                        # Settings desde .env
│   ├── auth/                          # JWT y autenticación
│   ├── data/                          # Materiales del curso (no incluidos en git)
│   │   ├── <asignatura>/
│   │   │   ├── teoria/
│   │   │   ├── practicas/
│   │   │   └── ejercicios/
│   │   └── docentes_autorizados.xlsx  # Lista de docentes autorizados a registrarse
│   └── locales/                       # Traducciones gettext (es, en)
│
├── web/                               # Frontend Next.js
│   ├── app/
│   │   ├── page.jsx                   # Página principal del chat
│   │   ├── layout.jsx                 # Providers (Auth + i18n)
│   │   ├── auth/                      # Login, registro, recuperación de contraseña
│   │   ├── chat/                      # Vista de chat
│   │   ├── components/
│   │   │   ├── chat/                  # ChatArea, ChatInput, MessageBubble, WelcomeScreen
│   │   │   ├── ui/                    # Header, botones, selector de idioma
│   │   │   └── providers/             # I18Provider
│   │   └── context/
│   │       └── AuthContext.jsx
│   ├── lib/
│   │   ├── i18n.js                    # Configuración react-i18next
│   │   ├── api/                       # Cliente de la API
│   │   └── hooks/                     # useChat
│   ├── public/locales/{es,en}/common.json
│   └── package.json
│
├── requeriments.txt
├── .env                               # Variables de entorno (no incluido en git)
└── README.md
```

---

## Modelo de datos

```
alumnos                       docentes
   │                             │
   │                             │
   ▼ (N:M)                       ▼ (N:M)
alumnos_asignaturas      docentes_asignaturas
   │                             │
   └────────► asignaturas ◄──────┘
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
| `asignaturas` | Catálogo de asignaturas creadas por docentes |
| `docentes_asignaturas` | Relación N:M docente ↔ asignatura |
| `alumnos_asignaturas` | Matrícula real (alumno ↔ asignatura) |
| `alumnos_aula_asignatura` | Lista de correos autorizados a registrarse en cada asignatura (la gestiona el docente) |
| `progresos` | Historial de evaluaciones del alumno |
| `interacciones` | Historial completo de mensajes del chat |

**Flujo de matrícula**:

1. El docente se registra (su correo debe estar en `docentes_autorizados.xlsx`).
2. Crea una asignatura desde el panel.
3. Importa un Excel de alumnos autorizados o los añade manualmente → filas en `alumnos_aula_asignatura`.
4. Los alumnos cuyos correos estén en esa lista pueden registrarse.
5. Al registrarse, el alumno queda **automáticamente matriculado** en todas las asignaturas donde su correo aparezca autorizado (una fila en `alumnos_asignaturas` por cada).

---

## Roles: alumno y docente

El sistema diferencia dos roles mediante un campo `rol` en el JWT.

### Alumno
- Se registra en `/auth/register` con un correo `@um.es` autorizado por algún docente.
- Hace login en `/auth/login`.
- Accede al chat con los agentes y puede consultar su propio historial.
- Sus rutas de API son `/api/...` (sin el prefijo `/docente/`).

### Docente
- Se registra en `/auth/docente/register` con un correo `@um.es` que figure en `docentes_autorizados.xlsx`.
- Hace login en `/auth/docente/login`.
- Accede al panel del docente con las siguientes capacidades:
  - **Asignaturas**: crear y listar las que imparte.
  - **Alumnos autorizados**: importar Excel, añadir, editar, borrar.
  - **Alumnos matriculados**: listar quienes ya tienen cuenta y están matriculados.
  - **Matricular manualmente** un alumno existente.
  - **Consultar progreso e interacciones** de cualquier alumno matriculado en sus asignaturas.
- La autorización se valida en cada endpoint: un docente solo puede ver/modificar lo que pertenece a sus asignaturas.

---

## Gestión de materiales y alumnos

### Añadir materiales del curso

Coloca los archivos en `/code/data/<codigo_asignatura>/` en la subcarpeta correspondiente. El `<codigo_asignatura>` debe coincidir con el `codigo` de la asignatura en BD y con el nombre de la colección de Qdrant.

| Carpeta | Contenido |
|---|---|
| `teoria/` | Apuntes y diapositivas teóricas |
| `practicas/` | Guiones de prácticas |
| `ejercicios/` | Enunciados de ejercicios |
| `rubricas/` | Rúbricas de evaluación |

**Formatos soportados**: PDF, DOCX, TXT, MD.

El watcher detecta los cambios automáticamente y los indexa en Qdrant sin necesidad de reiniciar el servidor.

### Gestionar docentes autorizados

Edita el archivo `/code/data/docentes_autorizados.xlsx`. Columnas esperadas:

| Columna | Descripción |
|---|---|
| `Nombre` | Nombre completo del docente |
| `Correo electrónico` | Email institucional (`@um.es`) |
| `DNI` | DNI del docente (opcional) |

Los cambios se sincronizan en caliente con la tabla `docentes_aula`.

### Gestionar alumnos autorizados (por asignatura)

Los alumnos se gestionan **desde el panel del docente** (no desde el filesystem). Cada docente puede:

- Importar un Excel con la misma estructura que el de docentes (`Nombre`, `Correo electrónico`, `DNI`). El sistema hace UPSERT: actualiza los existentes y añade los nuevos sin tocar los manuales.
- Añadir, editar o borrar autorizaciones individualmente desde el panel.
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
| `POST` | `/api/chat` | Enviar mensaje (respuesta SSE en streaming) |
| `GET` | `/api/interacciones` | Historial completo del alumno autenticado |
| `GET` | `/api/asignaturas` | Listar asignaturas disponibles (carpetas en `/data`) |

### Panel del docente — asignaturas y alumnos

| Método | Ruta | Descripción |
|---|---|---|
| `POST` | `/api/docente/asignaturas` | Crear asignatura |
| `GET` | `/api/docente/asignaturas` | Listar asignaturas que imparte el docente |
| `GET` | `/api/docente/asignaturas/{id}/alumnos` | Alumnos matriculados (con cuenta) |
| `POST` | `/api/docente/asignaturas/{id}/matricular` | Matricular un alumno por email |
| `GET` | `/api/docente/alumnos/{id}/progreso` | Historial de evaluaciones del alumno |
| `GET` | `/api/docente/alumnos/{id}/interacciones` | Historial de chat del alumno |

### Panel del docente — alumnos autorizados

| Método | Ruta | Descripción |
|---|---|---|
| `POST` | `/api/docente/asignaturas/{id}/import-alumnos` | Importar Excel (UPSERT) |
| `GET` | `/api/docente/asignaturas/{id}/alumnos-autorizados` | Listar autorizados |
| `POST` | `/api/docente/asignaturas/{id}/alumnos-autorizados` | Añadir uno manualmente |
| `PUT` | `/api/docente/alumnos-autorizados/{id}` | Editar |
| `DELETE` | `/api/docente/alumnos-autorizados/{id}` | Eliminar |

> Toda la documentación detallada de cada endpoint (parámetros, respuestas, códigos de error) está disponible en Swagger UI: `http://localhost:8000/docs`.

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

3. Reinicia el servidor para que `gettext` recargue los `.mo`.

En el código se usan con `_("CLAVE")` tras llamar a `setup_i18n("es")` o `setup_i18n("en")`.

### Frontend (Next.js)

Traducciones en `web/public/locales/{es,en}/common.json`. El selector del header (`SelectorIdioma`) cambia el idioma activo en runtime con `react-i18next`.

En los componentes:

```jsx
import { useTranslation } from "react-i18next";

const { t } = useTranslation();
return <button>{t("login_submit")}</button>;
```
