import sys
from pathlib import Path
from fastapi import Depends, FastAPI, HTTPException, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from watchfiles  import watch, Change
import threading
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from starlette.requests import Request

# Aseguramos que la raíz del proyecto esté en sys.path para poder importar load_data
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from auth.auth import create_access_token, get_current_user
from database.repository import actualizar_base_datos, comprobacion_email, create_tables, register_alumno, authenticate_alumno, tablas_existen, schema_exists, update_password, eliminar_cuenta_alumno, get_interacciones
from graph.workflow import stream_graph_updates
from i18n import setup_i18n
from load_data import SUPPORTED_FORMATS ,eliminar_documentacion, indexar_documentos, actualizar_documentacion, load_documents_from_folder
ASIGNATURA = "Introduccion_programacion"
CARPETA_DOCUMENTOS = "data"
DATA_PATH = Path(__file__).resolve().parent / CARPETA_DOCUMENTOS / ASIGNATURA
DATA_AUTORITHED_USER_PATH = Path(__file__).resolve().parent / CARPETA_DOCUMENTOS / "alumnos_autorizados.xlsx"


#Configuramos la internacionalización para mostrar los mensajes en el idioma del usuario, en este caso español
_= setup_i18n("es")

"""Definimos WatchFiles para que se recargue la base de datos MySQL cada vez que se modifique el excel 
 con los alumnos autorizados, de esta forma el docente puede añadir o eliminar alumnos autorizados 
 sin necesidad de reiniciar el agente docente, simplemente modificando el excel y guardándolo, con la 
 condición de que el excel tenga la misma estructura que el original (con las columnas "Nombre", "Correo" y "DNI")."""

def observar_cambios_archivos():
    for changes in watch(DATA_AUTORITHED_USER_PATH.parent):
        for change_type, path in changes:
            # En Windows, guardar desde Excel suele generar eventos added + modified.
            if change_type in (Change.added, Change.modified) and Path(path).resolve()== DATA_AUTORITHED_USER_PATH:
                actualizar_base_datos(str(DATA_AUTORITHED_USER_PATH))


#Funcion para observar los cambios en la carpeta de DATA_PATH, para poder recargar los documentos en la base de datos vectorial de QDrant
#cada vez que añadamos o modifiquemos un nuevo documento. 

def observar_cambios_documentacion():
    #tenemos que hacerlo de forma recursiva para observar los cambios en las subcarpetas de DATA_PATH
    for changes in watch(DATA_PATH):
        for change_type, path in changes:

            file_path = Path(path).resolve()
            
            #Evitamos que sean ficheros que no sean aceptados por la funcion de carga de documentos.
            if file_path.suffix.lower() not in SUPPORTED_FORMATS:
                continue

            if change_type == Change.added:
                if not file_path.is_file():
                    continue  # Ignorar cambios en directorios
                indexar_documentos(file_path, DATA_PATH.parent)
            elif change_type == Change.modified:
                if not file_path.is_file():
                    continue  # Ignorar cambios en directorios
                actualizar_documentacion(file_path, DATA_PATH.parent)
            elif change_type == Change.deleted:
                eliminar_documentacion(file_path, DATA_PATH.parent)




#Funcion principal que se encargará de manejar el ciclo de vida de la app para los hilos del observador de cambios en los archivos y el stream de actualizaciones del grafo de conocimiento.
@asynccontextmanager
async def lifespan(app: FastAPI):
    #indicamos que se ha iniciado el servidor
    print(_("SERVER STARTED"))

    #Comprobamos que las tablas de la base de datos MySQL existen, si no existen las creamos
    schema_exists()
    #Después tenemos que construir la base de datos mySql con la tabla de alumnos y progreso, para ello verficiamos primero si se existen ya el schema y las tablas
    #Si no existen las creamos si existen no hacemos nada 
    if not tablas_existen():
        create_tables()

    #data_root = Path(__file__).resolve().parent / CARPETA_DOCUMENTOS
    #para poder cambiar de asignatura solo hay que cambiar el nombre de la carpeta, siempre y cuando se mantenga la estructura de carpetas dentro de data
    #load_documents_from_folder(data_root / ASIGNATURA, data_root)
    
    print (_("INITIALIZE THREADS"))
    #Ahora inicializamos los hilos observadores 
    hilo_observador_alumnos = threading.Thread(target=observar_cambios_archivos, daemon=True)
    hilo_observador_documentacion = threading.Thread(target=observar_cambios_documentacion, daemon=True)
    hilo_observador_alumnos.start()
    hilo_observador_documentacion.start()

    #Ahora el servidor le cede el control y se pone a escuchar peticiones 
    yield

#Creamos la Api con FastApi
app = FastAPI(
    title="Codi - Agente Docente de Programación",
    description="BackEnd para el agente educador",
    lifespan=lifespan
)

#configuramos CORS para permitir peticiones desde el frontend, en este caso desde localhost:3000, pero esto se puede cambiar cuando se despliegue el frontend en producción
# main.py — sustituye el CORSMiddleware por esto:
"""
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://showers-performance-chargers-eye.trycloudflare.com",  # ← añadimos el dominio
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)"""

@app.middleware("http")
async def cors_middleware(request: Request, call_next):
    origin = request.headers.get("origin", "")
    response = await call_next(request)
    if origin.endswith(".trycloudflare.com") or origin == "http://localhost:3000":
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "*"
    return response
# --- Modelos de request ---

class AlumnoCreate(BaseModel):
    nombre: str
    email: str
    password: str
    nivel: str

class AlumnoLogin(BaseModel):
    email: str
    password: str

class PasswordUpdateRequest(BaseModel):
    password: str

class ChatRequest(BaseModel):
    message: str

# --- Modelos de response (Swagger) ---

class MessageResponse(BaseModel):
    message: str

class AlumnoDataResponse(BaseModel):
    email: str
    nombre: str
    nivel: str
    alumno_id: int

class InteraccionItem(BaseModel):
    mensaje_usuario: str
    respuesta_agente: str
    tipo_interaccion: str
    fecha: str | None

class InteraccionesResponse(BaseModel):
    interacciones: list[InteraccionItem]

# --- Endpoints de autenticación ---

@app.post(
    "/api/register",
    summary="Registrar alumno",
    description="Registra un nuevo alumno. El email debe ser @um.es y estar en la lista de alumnos autorizados.",
    response_model=MessageResponse,
    tags=["auth"],
    responses={
        400: {"description": "Email no válido, no autorizado o alumno ya existente"},
        500: {"description": "Error interno al registrar"},
    }
)
async def registrar_alumno(datos: AlumnoCreate):
    if not datos.email.endswith("@um.es"):
       raise HTTPException(status_code=400, detail=_("ERROR EMAIL NOT FROM UM"))
    if not comprobacion_email(datos.email):
        raise HTTPException(status_code=400, detail=_("ERROR EMAIL NOT AUTHORIZED"))
    try:
        register_alumno(email=datos.email, plain_password=datos.password, nombre=datos.nombre, nivel=datos.nivel)
        return {"message": _("REGISTRATION SUCCESS")}
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=_("REGISTRATION ERROR") + f": {str(e)}")

@app.post(
    "/api/login",
    summary="Iniciar sesión",
    description="Autentica al alumno y establece una cookie JWT HttpOnly para mantener la sesión.",
    response_model=MessageResponse,
    tags=["auth"],
    responses={
        401: {"description": "Credenciales inválidas"},
    }
)
def login_alumno(datos: AlumnoLogin, response: Response):
    alumno = authenticate_alumno(datos.email, datos.password)
    if not alumno:
        raise HTTPException(status_code=401, detail=_("ERROR INVALID CREDENTIALS"))
    token = create_access_token({
        "sub": alumno.email,
        "nombre": alumno.nombre,
        "nivel": alumno.nivel,
        "alumno_id": alumno.id,
    })
    response.set_cookie(key="access_token",
                        value=token,
                        httponly=True,
                        secure=False,
                        samesite="lax",
                        max_age=3600)
    return {"message": _("LOGIN SUCCESS")}

@app.get(
    "/api/me",
    summary="Obtener datos del alumno",
    description="Devuelve el perfil del alumno autenticado a partir de su cookie JWT.",
    response_model=AlumnoDataResponse,
    tags=["auth"],
    responses={
        401: {"description": "No autenticado o token inválido"},
    }
)
def obtener_datos_alumno_actual(current_user: dict = Depends(get_current_user)):
    return {"email": current_user["sub"], "nombre": current_user["nombre"], "nivel": current_user["nivel"], "alumno_id": current_user["alumno_id"]}

@app.post(
    "/api/logout",
    summary="Cerrar sesión",
    description="Elimina la cookie JWT y cierra la sesión del alumno.",
    response_model=MessageResponse,
    tags=["auth"],
)
def logout_alumno(response: Response):
    response.delete_cookie(key="access_token")
    return {"message": _("GOODBYE MESSAGE")}

@app.put(
    "/api/update-password",
    summary="Cambiar contraseña",
    description="Actualiza la contraseña del alumno autenticado. Mínimo 8 caracteres.",
    response_model=MessageResponse,
    tags=["auth"],
    responses={
        400: {"description": "Contraseña demasiado corta"},
        500: {"description": "Error interno al actualizar"},
    }
)
def actualizar_contraseña(datos: PasswordUpdateRequest, current_user: dict = Depends(get_current_user)):
    if len(datos.password) < 8:
        raise HTTPException(status_code=400, detail=_("PASSWORD TOO SHORT"))
    try:
        update_password(current_user["alumno_id"], datos.password)
        return {"message": _("PASSWORD UPDATE SUCCESS")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=_("PASSWORD UPDATE ERROR") + f": {str(e)}")

@app.delete(
    "/api/delete-account",
    summary="Eliminar cuenta",
    description="Anonimiza la cuenta del alumno conservando su progreso académico. Cierra la sesión al finalizar.",
    response_model=MessageResponse,
    tags=["auth"],
    responses={
        500: {"description": "Error interno al eliminar la cuenta"},
    }
)
def eliminar_cuenta(response: Response, current_user: dict = Depends(get_current_user)):
    try:
        eliminar_cuenta_alumno(current_user["alumno_id"])
        response.delete_cookie(key="access_token")
        return {"message": _("ACCOUNT DELETION SUCCESS")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=_("ACCOUNT DELETION ERROR") + f": {str(e)}")

# --- Endpoints de chat ---

@app.post(
    "/api/chat",
    summary="Enviar mensaje al agente",
    description=(
        "Envía un mensaje al agente docente y recibe la respuesta como stream de Server-Sent Events (SSE). "
        "Cada evento tiene el formato: `data: {\"content\": \"...\", \"agent\": \"educador|demostrador|evaluador|critico|codi\"}`. "
        "El stream finaliza con `data: [DONE]`."
    ),
    tags=["chat"],
    responses={
        401: {"description": "No autenticado"},
    }
)
def chat_endpoint(datos: ChatRequest, current_user: dict = Depends(get_current_user)):
    thread_id = str(current_user["alumno_id"])
    return StreamingResponse(
        stream_graph_updates(
            user_input=datos.message,
            thread_id=thread_id,
            user_level=current_user["nivel"],
            alumno_id=current_user["alumno_id"],
        ),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
    )

@app.get(
    "/api/interacciones",
    summary="Historial de interacciones",
    description="Devuelve el historial completo de conversaciones del alumno autenticado.",
    response_model=InteraccionesResponse,
    tags=["chat"],
    responses={
        401: {"description": "No autenticado"},
        500: {"description": "Error interno al obtener el historial"},
    }
)
def obtener_interacciones(current_user: dict = Depends(get_current_user)):
    try:
        interacciones = get_interacciones(current_user["alumno_id"])
        return {"interacciones": [
            {
                "mensaje_usuario": i.mensaje_usuario,
                "respuesta_agente": i.respuesta_agente,
                "tipo_interaccion": i.tipo_interaccion,
                "fecha": i.fecha_interaccion.isoformat() if i.fecha_interaccion else None,
            }
            for i in interacciones
        ]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener interacciones: {str(e)}")