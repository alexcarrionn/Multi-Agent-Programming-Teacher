# Codi — Multi-Agent Programming Teacher

**Codi** es un asistente educativo con IA diseñado para enseñar introducción a la programación. Implementa un sistema multi-agente (LangGraph) con backend en FastAPI y frontend en Next.js, capaz de explicar conceptos, mostrar ejemplos de código, evaluar ejercicios y dar retroalimentación personalizada adaptada al nivel del alumno.

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
- [Gestión de materiales y alumnos](#gestión-de-materiales-y-alumnos)
- [Endpoints de la API](#endpoints-de-la-api)

---

## Características

- **Sistema multi-agente** con un supervisor que enruta al agente especializado adecuado según el mensaje del alumno:
  - **Educador**: explica conceptos teóricos de programación.
  - **Demostrador**: muestra ejemplos prácticos de código.
  - **Evaluador**: corrige ejercicios del alumno usando rúbricas.
  - **Crítico**: da retroalimentación detallada sobre el código entregado.
- **RAG (Retrieval-Augmented Generation)**: recupera materiales del curso (PDFs, DOCs, etc.) antes de responder, para que los agentes tengan contexto de la asignatura.
- **Detección y adaptación de nivel**: el sistema detecta automáticamente el nivel del alumno (principiante → intermedio → avanzado) y adapta las respuestas.
- **Memoria de conversación**: cada alumno tiene sus propios hilos de conversación persistentes.
- **Streaming en tiempo real**: las respuestas se envían por SSE (Server-Sent Events).
- **Autorización por email**: solo alumnos con email `@um.es` presentes en el Excel de autorizados pueden registrarse.
- **Recarga en caliente**: los documentos del curso y el Excel de alumnos se monitorizan en tiempo real; cualquier cambio se indexa sin reiniciar el servidor.
- **Multiidioma**: detecta automáticamente si el alumno escribe en español o inglés y responde en consecuencia.

---

## Arquitectura

```
Alumno (Next.js)
       │  SSE / REST
       ▼
FastAPI (main.py)
       │
       ├─ Auth (JWT cookies)
       ├─ MySQL  ◄─── Alumnos, progreso
       │
       └─ LangGraph Workflow
              │
              ├─ Supervisor  ──► RAG (Qdrant)
              ├─ Educador
              ├─ Demostrador
              ├─ Evaluador
              └─ Crítico
```

**Flujo de un mensaje**:

1. El supervisor analiza el mensaje y decide qué agente debe responder.
2. El nodo RAG recupera fragmentos relevantes del material del curso desde Qdrant.
3. El agente seleccionado genera la respuesta con ese contexto.
4. Si es una evaluación, el Crítico añade retroalimentación y se guarda el progreso en MySQL.

---

## Tecnologías

| Capa | Tecnología |
|---|---|
| Backend | Python 3.9+, FastAPI |
| Agentes / Workflow | LangChain, LangGraph |
| Base de datos relacional | MySQL + SQLAlchemy |
| Base de datos vectorial | Qdrant |
| Embeddings | BAAI/bge-m3 (o text-embedding-3-small) |
| Autenticación | JWT (python-jose, passlib) |
| Frontend | Next.js 16, React 19 |
| Estilos | Tailwind CSS 4, shadcn/ui, Radix UI |
| Comunicación | Axios, Server-Sent Events |

---

## Requisitos previos

- Python 3.9 o superior
- Node.js 18 o superior
- Servidor MySQL en ejecución
- Instancia de Qdrant (cloud o auto-alojada)
- Clave de API de un LLM compatible (OpenAI-compatible, Gemini, Groq, etc.)

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
LLM_MODEL=           # ID del modelo (e.g. gpt-4o, gemini-2.5-flash)
LLM_API_KEY=tu_api_key_aqui         # Clave de API del proveedor LLM
LLM_URL=https://...                 # URL base del endpoint, en caso de tener(solo para modelos GPT-OSS / compatibles con OpenAI)

# ─── Qdrant (base de datos vectorial) ───────────────────────────────────────
QDRANT_URL= https://tu-instancia.qdrant.io
QDRANT_API_KEY= tu_qdrant_api_key
QDRANT_COLLECTION=     # Nombre de la colección de documentos

# ─── MySQL ───────────────────────────────────────────────────────────────────
MYSQL_HOST= tu_host_mysql
MYSQL_PORT=3306
MYSQL_USER= tu_user_mysql
MYSQL_PASSWORD= tu_password_mysql
MYSQL_DB=agentes_db                 # Nombre de la base de datos (se crea automáticamente)

# ─── Embeddings ──────────────────────────────────────────────────────────────
EMBEDDING_MODEL=BAAI/bge-m3   # Modelo de embeddings

# ─── JWT (autenticación) ─────────────────────────────────────────────────────
JWT_SECRET=cambia_esto_por_un_secreto_de_64_caracteres_hex
JWT_ALGORITHM=HS256
JWT_EXPIRATION=60                   # Expiración en minutos

# ─── LangSmith (opcional, para trazabilidad y depuración) ───────────────────
LANGSMITH_TRACING=false  #Cambiar a true si se va a utilizar
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
LANGSMITH_API_KEY= tu_langsmith_api_key
LANGSMITH_PROJECT= mi-proyecto  #Usa el nombre del proyecto que vayas a utilizar en langSmith
```

> **Nota**: no subas nunca el `.env` al repositorio. Ya está incluido en `.gitignore`.

---

## Ejecutar el proyecto

```bash
# Frontend
cd web
npm run build
npm start


El servidor arranca en `http://localhost:8000` y:
- Crea las tablas de MySQL automáticamente si no existen.
- Inicializa la colección de Qdrant.
- Lanza un watcher de documentos en `/code/data/` para indexación en caliente.
- Lanza un watcher del Excel de alumnos autorizados.

# Backend (con cualquier servidor ASGI, por ejemplo Uvicorn directamente)
cd code
uvicorn main:app


La aplicación estará disponible en `http://localhost:3000`. Las llamadas a la API se redirigen automáticamente al backend en el puerto 8000.
```

---

## Estructura del proyecto

```
Multi-Agent-Programming-Teacher/
├── code/                          # Backend Python (FastAPI)
│   ├── main.py                    # Punto de entrada, rutas, servidor
│   ├── agents/                    # Agentes LLM especializados
│   │   ├── supervisor.py          # Agente enrutador
│   │   ├── educador.py            # Agente teórico
│   │   ├── demostrador.py         # Agente de ejemplos
│   │   ├── evaluador.py           # Agente evaluador
│   │   └── critico.py             # Agente de retroalimentación
│   ├── graph/                     # Orquestación con LangGraph
│   │   ├── workflow.py            # Construcción del grafo y streaming
│   │   └── state.py               # Esquema de estado compartido
│   ├── database/                  # Persistencia de datos
│   │   ├── models.py              # Modelos ORM (SQLAlchemy)
│   │   └── repository.py          # Consultas a la base de datos
│   ├── rag/                       # Retrieval-Augmented Generation
│   │   ├── retriever.py           # Búsqueda vectorial
│   │   ├── indexer.py             # Indexación de documentos
│   │   └── embeddings.py          # Configuración de embeddings
│   ├── prompts/                   # Prompts del sistema de cada agente
│   ├── config/                    # Configuración y settings
│   ├── auth/                      # JWT y autenticación
│   ├── data/                      # Materiales del curso (no incluidos en git)
│   │   ├── Introduccion_programacion/
│   │   │   ├── teoria/
│   │   │   ├── practicas/
│   │   │   ├── ejercicios/
│   │   │   └── rubricas/
│   │   └── alumnos_autorizados.xlsx
│   └── locales/                   # Traducciones (i18n)
│
├── web/                           # Frontend Next.js
│   ├── app/                       # App Router (Next.js 13+)
│   │   ├── page.jsx               # Página principal del chat
│   │   ├── auth/                  # Páginas de login y registro
│   │   └── components/            # Componentes React
│   ├── lib/
│   │   ├── api/                   # Cliente de la API
│   │   └── hooks/                 # useChat y otros hooks
│   └── package.json
│
├── requeriments.txt               # Dependencias Python
├── .env                           # Variables de entorno (no incluido en git)
└── README.md
```

---

## Gestión de materiales y alumnos

### Añadir materiales del curso

Coloca los archivos en `/code/data/Nombre_de_la_asignatura/` en la subcarpeta correspondiente:

| Carpeta | Contenido |
|---|---|
| `teoria/` | Apuntes y diapositivas teóricas |
| `practicas/` | Guiones de prácticas |
| `ejercicios/` | Enunciados de ejercicios |
| `rubricas/` | Rúbricas de evaluación |

**Formatos soportados**: PDF, DOCX, TXT, MD.

El watcher detecta los cambios automáticamente y los indexa en Qdrant sin necesidad de reiniciar el servidor.

### Gestionar alumnos autorizados

Edita el archivo `/code/data/alumnos_autorizados.xlsx`. Columnas esperadas:

| Columna | Descripción |
|---|---|
| `Nombre` | Nombre completo del alumno |
| `Correo` | Email institucional (`@um.es`) |
| `DNI` | DNI del alumno (opcional) |

Los cambios se reflejan de inmediato sin reiniciar el servidor.

---

## Endpoints de la API

| Método | Ruta | Descripción |
|---|---|---|
| `POST` | `/api/register` | Registro de nuevo alumno |
| `POST` | `/api/login` | Inicio de sesión (devuelve cookie JWT) |
| `POST` | `/api/logout` | Cierre de sesión |
| `GET` | `/api/me` | Información del usuario autenticado |
| `PUT` | `/api/update-password` | Cambiar contraseña |
| `DELETE` | `/api/delete-account` | Eliminar cuenta |
| `POST` | `/api/chat` | Enviar mensaje (respuesta SSE en streaming) |
