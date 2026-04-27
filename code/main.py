import sys
from pathlib import Path
from fastapi import Depends, FastAPI, HTTPException, Response, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from watchfiles  import watch, Change
import threading
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from starlette.requests import Request
import smtplib
import secrets
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from config.settings import settings
from email.utils import formataddr
import io
import pandas as pd

# Aseguramos que la raíz del proyecto esté en sys.path para poder importar load_data
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from auth.auth import create_access_token, get_current_user, get_current_docente
from database.repository import (
    crear_asignatura, 
    get_asignaturas_por_docente, 
    get_alumnos_por_asignatura,
    matricular_alumno_en_asignatura,
    get_progreso_alumno,
    register_docente,
    actualizar_base_datos_docentes,
    comprobacion_email_alumno,
    comprobacion_email_docente,
    authenticate_docente,
    create_tables,
    get_alumno_by_email,
    register_alumno,
    authenticate_alumno,
    tablas_existen,
    schema_exists,
    update_password,
    eliminar_cuenta_alumno,
    get_interacciones, 
    import_alumnos_autorizados_excel,
    get_alumnos_autorizados,
    get_alumno_autorizado_by_id,
    crear_alumno_autorizado,
    actualizar_alumno_autorizado,
    eliminar_alumno_autorizado,)
from graph.workflow import stream_graph_updates
from i18n import setup_i18n
from load_data import SUPPORTED_FORMATS ,eliminar_documentacion, indexar_documentos, actualizar_documentacion

CARPETA_DOCUMENTOS = "data"
DATA_ROOT = Path(__file__).resolve().parent / CARPETA_DOCUMENTOS
DATA_AUTORITHED_DOCENT_PATH = Path(__file__).resolve().parent / CARPETA_DOCUMENTOS / "docentes_autorizados.xlsx"


#Configuramos la internacionalización para mostrar los mensajes en el idioma del usuario, en este caso español
_= setup_i18n("es")


"""WatchFiles vigila el Excel de docentes autorizados para sincronizar la tabla DocenteAula
sin reiniciar el servidor. La gestion de alumnos autorizados ahora se hace por asignatura
desde el panel del docente (BD, no fichero)."""

def observar_cambios_docentes():
    for changes in watch(DATA_AUTORITHED_DOCENT_PATH.parent):
        for change_type, path in changes:
            # En Windows, guardar desde Excel suele generar eventos added + modified.
            if change_type in (Change.added, Change.modified) and Path(path).resolve()== DATA_AUTORITHED_DOCENT_PATH:
                actualizar_base_datos_docentes(str(DATA_AUTORITHED_DOCENT_PATH))


#Funcion para observar los cambios en la carpeta de DATA_PATH, para poder recargar los documentos en la base de datos vectorial de QDrant
#cada vez que añadamos o modifiquemos un nuevo documento. 

def observar_cambios_documentacion():
    data_root = DATA_ROOT
    #tenemos que hacerlo de forma recursiva para observar los cambios en las subcarpetas de DATA_PATH
    for changes in watch(data_root):
        for change_type, path in changes:

            file_path = Path(path).resolve()
            #Evitamos que sean ficheros que no sean aceptados por la funcion de carga de documentos.
            if file_path.suffix.lower() not in SUPPORTED_FORMATS:
                continue
            try : 
                collection = file_path.parent.relative_to(data_root).parts[0]
            except ValueError:
                continue
            if change_type == Change.added:
                if not file_path.is_file():
                    continue  # Ignorar cambios en directorios
                indexar_documentos(file_path, data_root, collection)
            elif change_type == Change.modified:
                if not file_path.is_file():
                    continue  # Ignorar cambios en directorios
                actualizar_documentacion(file_path, data_root, collection)
            elif change_type == Change.deleted:
                eliminar_documentacion(file_path, data_root, collection_name=collection)




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

    # Indexar documentos de todas las asignaturas en sus colecciones de Qdrant al arrancar
    #for carpeta in DATA_ROOT.iterdir():
    #  if carpeta.is_dir():
    #     load_documents_from_folder(carpeta, DATA_ROOT, collection_name=carpeta.name)
    
    print (_("INITIALIZE THREADS"))
    #Hilos observadores: docentes autorizados (Excel global) y documentacion del RAG.
    hilo_observador_documentacion = threading.Thread(target=observar_cambios_documentacion, daemon=True)
    hilo_observador_documentacion.start()
    hilo_observador_docentes = threading.Thread(target=observar_cambios_docentes, daemon=True)
    hilo_observador_docentes.start()
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

class DocenteCreate(BaseModel):
    nombre: str
    email: str
    password: str

class AlumnoLogin(BaseModel):
    email: str
    password: str

class DocenteLogin(BaseModel):
    email: str
    password: str

class PasswordUpdateRequest(BaseModel):
    password: str

class ChatRequest(BaseModel):
    message: str
    asignatura: str = "Introduccion_programacion"  # Valor por defecto, se puede cambiar desde el frontend

class ForgotPasswordRequest(BaseModel):
    email: str

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

class AsignaturaCreate(BaseModel):
      nombre: str
      codigo: str

class MatricularRequest(BaseModel):
      alumno_email: str

class AlumnoAutorizadoCreate(BaseModel):
      nombre: str
      correo: str
      dni: str | None = None

class AlumnoAutorizadoUpdate(BaseModel):
      nombre: str
      correo: str
      dni: str | None = None

# --- Modelos de response (Swagger) ---

class MessageResponse(BaseModel):
    message: str

class AlumnoDataResponse(BaseModel):
    email: str
    nombre: str
    nivel: str
    alumno_id: int

class DocenteDataResponse(BaseModel):
    email: str
    nombre: str
    docente_id: int

class InteraccionItem(BaseModel):
    mensaje_usuario: str
    respuesta_agente: str
    tipo_interaccion: str
    fecha: str | None

class InteraccionesResponse(BaseModel):
    interacciones: list[InteraccionItem]

class AsignaturasResponse(BaseModel):
    asignaturas: list[str]

class AsignaturaResponse(BaseModel):
    id: int
    nombre: str
    codigo: str

class AsignaturasListResponse(BaseModel):
    asignaturas: list[AsignaturaResponse]

class AlumnoListItem(BaseModel):
    id: int
    nombre: str
    email: str
    nivel: str | None

class AlumnosListResponse(BaseModel):
    alumnos: list[AlumnoListItem]

class ProgresoItem(BaseModel):
    enunciado: str | None
    codigo_alumno: str | None
    puntuacion: str | None
    feedback: str | None
    ambito: str | None
    fecha: str | None

class ProgresoResponse(BaseModel):
    progreso: list[ProgresoItem]

class AlumnoAutorizadoItem(BaseModel):
      id: int
      asignatura_id: int
      nombre: str
      correo: str
      dni: str | None

class AlumnosAutorizadosListResponse(BaseModel):
    alumnos_autorizados: list[AlumnoAutorizadoItem]

class ImportResultResponse(BaseModel):
    insertados: int
    actualizados: int
    message: str

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
    if not comprobacion_email_alumno(datos.email):
        raise HTTPException(status_code=400, detail=_("ERROR EMAIL NOT AUTHORIZED"))
    try:
        register_alumno(email=datos.email, plain_password=datos.password, nombre=datos.nombre, nivel=datos.nivel)
        return {"message": _("REGISTRATION SUCCESS")}
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=_("REGISTRATION ERROR") + f": {str(e)}")

@app.post(
    "/api/docente/register",
    summary="Registrar docente",
    description="Registra un nuevo docente. El email debe ser @um.es y estar en la lista de docentes autorizados.",
    response_model=MessageResponse,
    tags=["auth"],
    responses={
        400: {"description": "Email no válido, no autorizado o docente ya existente"},
        500: {"description": "Error interno al registrar"},
    }
)
async def registrar_docente(datos: DocenteCreate):
    if not datos.email.endswith("@um.es"):
        raise HTTPException(status_code=400, detail=_("ERROR EMAIL NOT FROM UM"))
    if not comprobacion_email_docente(datos.email):
        raise HTTPException(status_code=400, detail=_("ERROR EMAIL NOT AUTHORIZED"))
    try:
        register_docente(email=datos.email, plain_password=datos.password, nombre=datos.nombre)
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
        "rol": "alumno"
    })
    response.set_cookie(key="access_token",
                        value=token,
                        httponly=True,
                        secure=False,
                        samesite="lax",
                        max_age=3600)
    return {"message": _("LOGIN SUCCESS")}


@app.post(
    "/api/docente/login",
    summary="Iniciar sesión docente",
    description="Autentica al docente y establece una cookie JWT HttpOnly para mantener la sesión.",
    response_model=MessageResponse,
    tags=["auth"],
    responses={
        401: {"description": "Credenciales inválidas"},
    }
)
def login_docente(datos: DocenteLogin, response: Response):
    docente = authenticate_docente(datos.email, datos.password)
    if not docente:
        raise HTTPException(status_code=401, detail=_("ERROR INVALID CREDENTIALS"))
    token = create_access_token({
        "sub": docente.email,
        "nombre": docente.nombre,
        "docente_id": docente.id,
        "rol": "docente"
    })
    response.set_cookie(key="access_token",
                        value=token,
                        httponly=True,
                        secure=False,
                        samesite="lax",
                        max_age=3600)
    return {"message": _("LOGIN SUCCESS")}

#Endpoint para obtener los datos del alumno autenticado a partir de su cookie JWT, 
# esta información se va a mostrar en el frontend para personalizar la experiencia del usuario.
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
@app.get(
    "/api/docente/me",
    summary="Obtener datos del docente",
    description="Devuelve el perfil del docente autenticado a partir de su cookie JWT.",
    response_model=DocenteDataResponse,
    tags=["auth"],
    responses={
        401: {"description": "No autenticado o token inválido"},
    }
)
def obtener_datos_docente_actual(current_user: dict = Depends(get_current_docente)):
    return {"email": current_user["sub"], "nombre": current_user["nombre"], "docente_id": current_user["docente_id"]}
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

#endpoint para cerrar sesion de un docente
@app.post(
    "/api/docente/logout",
    summary="Cerrar sesión docente",
    description="Elimina la cookie JWT y cierra la sesión del docente.",
    response_model=MessageResponse,
    tags=["auth"],
)
def logout_docente(response: Response):
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
            asignatura=datos.asignatura
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
    
# Almacenamiento temporal de tokens: {token: (email, expires_at)}
_reset_tokens: dict[str, tuple[str, datetime]] = {}

def _send_reset_email(recipient: str, reset_url: str):
    
    
    msg = MIMEText(
        f"Hola,\n\n"
        f"Hemos recibido una solicitud para restablecer la contraseña de tu cuenta en Codi.\n\n"
        f"Haz clic en el siguiente enlace para restablecerla (válido durante 1 hora):\n{reset_url}\n\n"
        f"Si no has solicitado este cambio, ignora este correo.\n\n"
        f"Un saludo,\nEl equipo de Codi",
        _charset="utf-8",
    )
    msg["Subject"] = "Restablecer contraseña - Codi"
    msg["From"] = formataddr((settings.BREVO_SENDER_NAME, settings.BREVO_SENDER_EMAIL))
    msg["To"] = recipient

    with smtplib.SMTP(settings.BREVO_SMTP_HOST, settings.BREVO_SMTP_PORT, timeout=10) as smtp:
        smtp.ehlo()
        smtp.starttls()
        smtp.ehlo()
        smtp.login(settings.BREVO_SMTP_LOGIN, settings.BREVO_SMTP_KEY)
        smtp.sendmail(settings.BREVO_SENDER_EMAIL, [recipient], msg.as_string())

@app.post(
    "/api/forgot-password",
    summary="Recuperar contraseña",
    description="Envía un correo al alumno con un enlace para restablecer su contraseña. Siempre devuelve éxito para no revelar si el email existe.",
    response_model=MessageResponse,
    tags=["auth"],
)
def forgot_password(datos: ForgotPasswordRequest):
    import logging
    alumno = get_alumno_by_email(datos.email)
    if alumno and not alumno.anonimizado:
        token = secrets.token_urlsafe(32)
        reset_url = f"{settings.FRONTEND_URL}/auth/reset-password?token={token}"
        try:
            _send_reset_email(datos.email, reset_url)
            # Solo guardamos el token si el correo se envió con éxito
            _reset_tokens[token] = (datos.email, datetime.now() + timedelta(hours=1))
        except Exception as e:
            # Logueamos el error internamente pero devolvemos 200 para no revelar si el email existe
            logging.error(f"Error enviando email de reset a {datos.email}: {e}")
    return {"message": _("FORGOT PASSWORD EMAIL SENT")}

@app.post(
    "/api/reset-password",
    summary="Restablecer contraseña",
    description="Restablece la contraseña del alumno usando el token enviado por correo.",
    response_model=MessageResponse,
    tags=["auth"],
    responses={
        400: {"description": "Token inválido o expirado"},
        500: {"description": "Error interno al actualizar la contraseña"},
    }
)
def reset_password(datos: ResetPasswordRequest):
    token_data = _reset_tokens.get(datos.token)
    if not token_data or datetime.now() > token_data[1]:
        _reset_tokens.pop(datos.token, None)
        raise HTTPException(status_code=400, detail=_("INVALID OR EXPIRED TOKEN"))
    if len(datos.new_password) < 8:
        raise HTTPException(status_code=400, detail=_("PASSWORD TOO SHORT"))
    email = token_data[0]
    alumno = get_alumno_by_email(email)
    if not alumno:
        raise HTTPException(status_code=400, detail=_("ALUMNO NOT FOUND"))
    try:
        update_password(alumno.id, datos.new_password)
        del _reset_tokens[datos.token]
        return {"message": _("PASSWORD RESET SUCCESS")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=_("PASSWORD RESET ERROR") + f": {str(e)}") 
    
#funcion para poder obtener las asignaturas
@app.get(
    "/api/asignaturas",
    summary="Obtener asignaturas",
    description="Devuelve la lista de asignaturas disponibles.",
    response_model=AsignaturasResponse,
    tags=["chat"],
)
def listar_asignaturas():
    data_root = Path(__file__).resolve().parent / CARPETA_DOCUMENTOS
    carpetas = [d.name for d in data_root.iterdir() if d.is_dir()]
    return {"asignaturas": carpetas}

#EndPoint para poder crear una asignatura 
@app.post(
      "/api/docente/asignaturas",
      summary="Crear asignatura",
      description="Crea una asignatura nueva y la asocia al docente autenticado.",
      response_model=AsignaturaResponse,
      tags=["docente"],
      responses={
          400: {"description": "Código duplicado o datos inválidos"},
          401: {"description": "No autenticado"},
          403: {"description": "Rol no autorizado"},
      }
  )
#con el depends get_current_docente nos aseguramos de que solo un docente autenticado pueda crear una asignatura, y además obtenemos su id para asociarla a la asignatura que se va a crear.
def crear_asignatura_endpoint(datos: AsignaturaCreate, current_user: dict = Depends(get_current_docente)):
    try:
        asignatura = crear_asignatura(
            nombre=datos.nombre,
            codigo=datos.codigo,
            docente_id=current_user["docente_id"],
        )
        return {"id": asignatura.id, "nombre": asignatura.nombre, "codigo": asignatura.codigo}
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
      
#Endpoint para poder listar las asignaturas del docente 
@app.get(
      "/api/docente/asignaturas",
      summary="Listar asignaturas del docente",
      description="Devuelve las asignaturas que imparte el docente autenticado.",
      response_model=AsignaturasListResponse,
      tags=["docente"],
      responses={
          401: {"description": "No autenticado"},
          403: {"description": "Rol no autorizado"},
      }
  )
def listar_asignaturas_docente(current_user: dict = Depends(get_current_docente)):
      asignaturas = get_asignaturas_por_docente(current_user["docente_id"])
      return {"asignaturas": [
          {"id": a.id, "nombre": a.nombre, "codigo": a.codigo}
          for a in asignaturas
      ]}

#Enpoint para poder obtener los alumnos por asignatura 
@app.get(
    "/api/docente/asignaturas/{asignatura_id}/alumnos",
    summary="Obtener alumnos por asignatura",
    description="Devuelve la lista de alumnos inscritos en una asignatura específica.",
    response_model=AlumnosListResponse,
    tags=["docente"],
    responses={
        401: {"description": "No autenticado"},
        403: {"description": "Rol no autorizado"},
    }
)
def listar_alumnos_por_asignatura(asignatura_id: int, current_user: dict = Depends(get_current_docente)):
    #comprobamos que la asignatura esta entre las asignturas del docente actual
    asignaturas_docente = get_asignaturas_por_docente(current_user["docente_id"])
    if not any(a.id == asignatura_id for a in asignaturas_docente):
        raise HTTPException(status_code=403, detail=_("ACCESS TO ASSIGNMENT DENIED"))
    alumnos = get_alumnos_por_asignatura(asignatura_id)
    return {"alumnos": [
        {"id": a.id, "nombre": a.nombre, "email": a.email, "nivel": a.nivel}
        for a in alumnos
    ]}

#Endpoint para matricular un alumno en una asignatura
@app.post(
    "/api/docente/asignaturas/{asignatura_id}/matricular",
    summary="Matricular alumno en asignatura",
    description="Matricula a un alumno en la asignatura especificada usando su email.",
    response_model=MessageResponse,
    tags=["docente"],
    responses={
        400: {"description": "Email no válido o alumno no encontrado"},
        401: {"description": "No autenticado"},
        403: {"description": "Rol no autorizado"},
    }
)
def matricular_alumno_endpoint(asignatura_id: int, datos: MatricularRequest, current_user: dict = Depends(get_current_docente)):
    #comprobamos que la asignatura esta entre las asignaturas del docente actual
    asignaturas_docente = get_asignaturas_por_docente(current_user["docente_id"])
    if not any(a.id == asignatura_id for a in asignaturas_docente):
        raise HTTPException(status_code=403, detail=_("ACCESS TO ASSIGNMENT DENIED"))
    alumno = get_alumno_by_email(datos.alumno_email)
    if not alumno or alumno.anonimizado:
        raise HTTPException(status_code=400, detail=_("ALUMNO NOT FOUND"))
    try:
        matricular_alumno_en_asignatura(alumno.id, asignatura_id)
        return {"message": _("STUDENT ENROLLED SUCCESSFULLY")}
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

#Endpoint para obtener el progreso academico de un alumno
@app.get(
    "/api/docente/alumnos/{alumno_id}/progreso",
    summary="Obtener progreso académico",
    description="Devuelve el historial completo de evaluaciones (Progreso) de un alumno.",
    response_model=ProgresoResponse,
    tags=["docente"],
    responses={
        401: {"description": "No autenticado"},
        403: {"description": "El alumno no esta matriculado en ninguna asignatura del docente"},
    }
)
def obtener_progreso_academico(alumno_id: int, current_user: dict = Depends(get_current_docente)):
    #comprobamos que el alumno esta matriculado en alguna asignatura del docente actual
    asignaturas_docente = get_asignaturas_por_docente(current_user["docente_id"])
    alumno_matriculado = any(
        alumno_id in [a.id for a in get_alumnos_por_asignatura(asignatura.id)]
        for asignatura in asignaturas_docente
    )
    if not alumno_matriculado:
        raise HTTPException(status_code=403, detail=_("ACCESS TO STUDENT PROGRESS DENIED"))
    progreso = get_progreso_alumno(alumno_id)
    return {"progreso": [
        {
            "enunciado": p.enunciado_ejercicio,
            "codigo_alumno": p.codigo_alumno,
            "puntuacion": p.puntuacion_ejercicio,
            "feedback": p.retroalimentacion_ejercicio,
            "ambito": p.ambito_dificultad,
            "fecha": p.fecha_evaluacion.isoformat() if p.fecha_evaluacion else None,
        }
        for p in progreso
    ]}

#endpoint para obtener las interacciones
@app.get(
    "/api/docente/alumnos/{alumno_id}/interacciones",
    summary="Obtener interacciones del alumno",
    description="Devuelve el historial de interacciones del alumno autenticado.",
    response_model=InteraccionesResponse,
    tags=["docente"],
    responses={
        401: {"description": "No autenticado"},
        403: {"description": "Rol no autorizado"},
        500: {"description": "Error interno al obtener las interacciones"},
    }
)
def obtener_interacciones_docente(alumno_id: int, current_user: dict = Depends(get_current_docente)):
    #comprobamos que el alumno esta matriculado en alguna asignatura del docente actual
    asignaturas_docente = get_asignaturas_por_docente(current_user["docente_id"])
    alumno_matriculado = any(
        alumno_id in [a.id for a in get_alumnos_por_asignatura(asignatura.id)]
        for asignatura in asignaturas_docente
    )
    if not alumno_matriculado:
        raise HTTPException(status_code=403, detail=_("ACCESS TO STUDENT INTERACTIONS DENIED"))
    try:
        interacciones = get_interacciones(alumno_id)
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
    
#Creamos el endpoint para importar el excel de los alumnos
@app.post(
      "/api/docente/asignaturas/{asignatura_id}/import-alumnos",
      summary="Importar alumnos autorizados desde Excel",
      description="Sube un Excel (.xlsx) con columnas 'Nombre', 'Correo electrónico' y opcional 'DNI'. UPSERT por (asignatura, correo).",
      response_model=ImportResultResponse,
      tags=["docente"],
      responses={
          400: {"description": "Archivo invalido"},
          403: {"description": "No autorizado para esta asignatura"},
      }
  )
async def import_alumnos_endpoint(
      asignatura_id: int,
      #Gracias a esto FastApi recibe un multiPart/form-data con el archivo Excel, y lo valida como un UploadFile, que es un tipo especial de FastApi para manejar archivos subidos por el usuario.
      file: UploadFile = File(...),
      current_user: dict = Depends(get_current_docente),
  ):
      # autorizacion: la asignatura debe ser del docente actual
      asignaturas_docente = get_asignaturas_por_docente(current_user["docente_id"])
      if not any(a.id == asignatura_id for a in asignaturas_docente):
          raise HTTPException(status_code=403, detail=_("ACCESS TO ASSIGNMENT DENIED"))

      if not file.filename or not file.filename.lower().endswith((".xlsx", ".xls")):
          raise HTTPException(status_code=400, detail=_("INVALID FILE FORMAT, EXPECTED EXCEL"))

      try:
          #bytes del archivo, lo pasamos a io.BytesIO para que pandas lo lea sin tener que guardarlo en disco.
          content = await file.read()
          df = pd.read_excel(io.BytesIO(content))
          insertados, actualizados = import_alumnos_autorizados_excel(asignatura_id, df)
          return {
              "insertados": insertados,
              "actualizados": actualizados,
              "message": _("IMPORT SUCCESS"),
          }
      except Exception as e:
          raise HTTPException(status_code=500, detail=str(e))


#Listar alumnos autorizados de una asignatura
@app.get(
    "/api/docente/asignaturas/{asignatura_id}/alumnos-autorizados",
    summary="Listar alumnos autorizados de una asignatura",
    description="Devuelve los alumnos autorizados a registrarse en la asignatura, esten o no ya registrados.",
    response_model=AlumnosAutorizadosListResponse,
    tags=["docente"],
    responses={
        401: {"description": "No autenticado"},
        403: {"description": "No autorizado para esta asignatura"},
    }
)
def listar_alumnos_autorizados(asignatura_id: int, current_user: dict = Depends(get_current_docente)):
    asignaturas_docente = get_asignaturas_por_docente(current_user["docente_id"])
    if not any(a.id == asignatura_id for a in asignaturas_docente):
        raise HTTPException(status_code=403, detail=_("ACCESS TO ASSIGNMENT DENIED"))
    autorizados = get_alumnos_autorizados(asignatura_id)
    return {"alumnos_autorizados": [
        {"id": a.id, "asignatura_id": a.asignatura_id, "nombre": a.nombre, "correo": a.correo, "dni": a.dni}
        for a in autorizados
    ]}


#Añadir manualmente un alumno autorizado a una asignatura
@app.post(
    "/api/docente/asignaturas/{asignatura_id}/alumnos-autorizados",
    summary="Añadir alumno autorizado",
    description="Añade manualmente un alumno autorizado a la asignatura.",
    response_model=AlumnoAutorizadoItem,
    tags=["docente"],
    responses={
        400: {"description": "Correo ya autorizado u otros datos invalidos"},
        401: {"description": "No autenticado"},
        403: {"description": "No autorizado para esta asignatura"},
    }
)
def crear_alumno_autorizado_endpoint(asignatura_id: int, datos: AlumnoAutorizadoCreate, current_user: dict = Depends(get_current_docente)):
    asignaturas_docente = get_asignaturas_por_docente(current_user["docente_id"])
    if not any(a.id == asignatura_id for a in asignaturas_docente):
        raise HTTPException(status_code=403, detail=_("ACCESS TO ASSIGNMENT DENIED"))
    try:
        nuevo = crear_alumno_autorizado(asignatura_id, datos.nombre, datos.correo, datos.dni)
        return {
            "id": nuevo.id,
            "asignatura_id": nuevo.asignatura_id,
            "nombre": nuevo.nombre,
            "correo": nuevo.correo,
            "dni": nuevo.dni,
        }
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


#Editar un alumno autorizado existente
@app.put(
    "/api/docente/alumnos-autorizados/{autorizado_id}",
    summary="Editar alumno autorizado",
    description="Actualiza nombre, correo y/o DNI de una autorizacion existente.",
    response_model=AlumnoAutorizadoItem,
    tags=["docente"],
    responses={
        400: {"description": "Datos invalidos"},
        401: {"description": "No autenticado"},
        403: {"description": "La autorizacion no pertenece a una asignatura del docente"},
        404: {"description": "Autorizacion no encontrada"},
    }
)
def actualizar_alumno_autorizado_endpoint(autorizado_id: int, datos: AlumnoAutorizadoUpdate, current_user: dict = Depends(get_current_docente)):
    autorizado = get_alumno_autorizado_by_id(autorizado_id)
    if autorizado is None:
        raise HTTPException(status_code=404, detail=_("ALUMNO AUTHORIZED NOT FOUND"))
    asignaturas_docente = get_asignaturas_por_docente(current_user["docente_id"])
    if not any(a.id == autorizado.asignatura_id for a in asignaturas_docente):
        raise HTTPException(status_code=403, detail=_("ACCESS TO ASSIGNMENT DENIED"))
    try:
        actualizado = actualizar_alumno_autorizado(autorizado_id, datos.nombre, datos.correo, datos.dni)
        return {
            "id": actualizado.id,
            "asignatura_id": actualizado.asignatura_id,
            "nombre": actualizado.nombre,
            "correo": actualizado.correo,
            "dni": actualizado.dni,
        }
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


#Eliminar un alumno autorizado
@app.delete(
    "/api/docente/alumnos-autorizados/{autorizado_id}",
    summary="Eliminar alumno autorizado",
    description="Elimina una autorizacion existente. NO afecta a la cuenta del alumno si ya se registro.",
    response_model=MessageResponse,
    tags=["docente"],
    responses={
        401: {"description": "No autenticado"},
        403: {"description": "La autorizacion no pertenece a una asignatura del docente"},
        404: {"description": "Autorizacion no encontrada"},
    }
)
def eliminar_alumno_autorizado_endpoint(autorizado_id: int, current_user: dict = Depends(get_current_docente)):
    autorizado = get_alumno_autorizado_by_id(autorizado_id)
    if autorizado is None:
        raise HTTPException(status_code=404, detail=_("ALUMNO AUTHORIZED NOT FOUND"))
    asignaturas_docente = get_asignaturas_por_docente(current_user["docente_id"])
    if not any(a.id == autorizado.asignatura_id for a in asignaturas_docente):
        raise HTTPException(status_code=403, detail=_("ACCESS TO ASSIGNMENT DENIED"))
    try:
        eliminar_alumno_autorizado(autorizado_id)
        return {"message": _("AUTHORIZED STUDENT DELETED")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

